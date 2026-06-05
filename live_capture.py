import threading
import queue
import time as time_mod
from datetime import datetime
from collections import defaultdict
from scapy.all import sniff
import pandas as pd
from packet import Packet
from flow import Flow
from rule import Rule
from signature_IDS import SignatureIDS
from anomaly_IDS import AnomalyIDS
from DB import Database
from log import Log
from alert import Alert
from ntp_time import get_ntp_time
from continual_learning import store_batch_features
from explainability import store_alert_features


class LiveCapture:
    """Captures live network traffic using Scapy sniff() and runs
    both signature and anomaly IDS detection on the captured packets.

    Anomaly detection works on flow batches: packets are accumulated
    into flows every FLOW_WINDOW seconds, then analysed together.
    """

    # How often to process accumulated packets as flows (seconds)
    FLOW_WINDOW = 10
    # Batch size for training-data DB writes
    BATCH_SIZE = 50

    def __init__(self, rules, model=None, iso_forest=None, scaler=None,
                 label_encoder=None, feature_order=None, db_path="DB/IDS.db",
                 interface=None, threshold=-0.000001):
        self.rules = rules
        self.model = model
        self.iso_forest = iso_forest
        self.scaler = scaler
        self.label_encoder = label_encoder
        self.feature_order = feature_order
        self.db_path = db_path
        self.interface = interface
        self.threshold = threshold

        self._running = False
        self._thread = None
        self._lock = threading.Lock()

        # Interface display info (set by UI.py)
        self._interface_name = interface or "default"
        self._interface_desc = ""

        # Stats (use lock for thread safety)
        self._stats_lock = threading.Lock()
        self.packets_captured = 0
        self.alerts_generated = 0

        # Packet buffer for flow-based anomaly detection
        self._packet_buffer = []
        self._buffer_lock = threading.Lock()
        self._flow_thread = None

        # Batch queue for training data storage
        self._feature_queue = queue.Queue()
        self._writer_thread = None

    @property
    def is_running(self):
        return self._running

    def start(self):
        """Start live capture in a background thread."""
        with self._lock:
            if self._running:
                print("[LiveCapture] Already running.")
                return False
            self._running = True
            self.packets_captured = 0
            self.alerts_generated = 0

        # Start the sniffing thread
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        # Start flow-processing thread (anomaly detection)
        self._flow_thread = threading.Thread(target=self._flow_processing_loop, daemon=True)
        self._flow_thread.start()

        # Start batch writer thread (training data)
        self._writer_thread = threading.Thread(target=self._batch_writer_loop, daemon=True)
        self._writer_thread.start()

        print(f"[LiveCapture] Started on interface: {self._interface_name}")
        return True

    def stop(self):
        """Stop the live capture."""
        with self._lock:
            if not self._running:
                print("[LiveCapture] Not running.")
                return False
            self._running = False

        if self._thread:
            self._thread.join(timeout=5)

        # Process any remaining buffered packets
        self._process_flow_buffer()

        # Flush remaining training data
        self._flush_feature_queue()

        print(f"[LiveCapture] Stopped. Captured {self.packets_captured} packets, "
              f"generated {self.alerts_generated} alerts.")
        return True

    def _capture_loop(self):
        """Main capture loop using Scapy sniff with a callback."""
        try:
            while self._running:
                sniff(
                    iface=self.interface,
                    prn=self._process_packet,
                    store=False,
                    stop_filter=lambda _: not self._running,
                    timeout=2
                )
        except Exception as e:
            print(f"[LiveCapture ERROR] Capture failed: {e}")
            self._running = False

    def _process_packet(self, raw_pkt):
        """Process a single captured packet: signature detection + buffer for anomaly."""
        conn = None
        try:
            packet = Packet(raw_pkt)

            with self._stats_lock:
                self.packets_captured += 1

            # --- Signature Detection (per-packet) ---
            sig_rules = [Rule(r) for r in self.rules]
            for rule in sig_rules:
                if rule.match_rule(packet):
                    conn = self._get_connection()
                    if not conn:
                        return

                    time_str = get_ntp_time()
                    src_ip = packet.get_src_ip()
                    dst_ip = packet.get_dst_ip()
                    action = rule.action
                    message = rule.options.get("msg", "No message specified")
                    layer = rule.options.get("attack", "No attack type")
                    method = "signature"

                    log = Log(time_str, action, src_ip, dst_ip, message, layer, method)
                    alert = Alert(time_str, src_ip, dst_ip, message, layer, method)

                    log.add_to_log_table(conn)
                    alert.add_to_alert_table(conn)

                    with self._stats_lock:
                        self.alerts_generated += 1

                    print(f"[LiveCapture ALERT] {message} | {src_ip} -> {dst_ip}")

            # --- Buffer raw scapy packet for flow-based anomaly detection ---
            with self._buffer_lock:
                self._packet_buffer.append(raw_pkt)

        except Exception:
            pass
        finally:
            if conn:
                conn.close()

    # ========== Flow-Based Anomaly Detection ========== #

    def _flow_processing_loop(self):
        """Periodically drain the packet buffer, group into flows,
        and run anomaly detection on each flow."""
        while self._running:
            time_mod.sleep(self.FLOW_WINDOW)
            if self._running:
                self._process_flow_buffer()

    def _process_flow_buffer(self):
        """Take all buffered packets, group into flows, and run anomaly detection."""
        # Drain buffer
        with self._buffer_lock:
            if not self._packet_buffer:
                return
            raw_packets = list(self._packet_buffer)
            self._packet_buffer.clear()

        if not self.model or not self.feature_order:
            print("[LiveCapture] Anomaly skipped: model or feature_order not loaded.")
            return

        try:
            # Convert raw scapy packets to Packet objects — skip bad ones individually
            packets = []
            for pkt in raw_packets:
                try:
                    p = Packet(pkt)
                    # Only include IP-based packets that can form meaningful flows
                    if p.protocol in ("tcp", "udp", "icmp") and p.src_ip != "N/A":
                        packets.append(p)
                except Exception:
                    pass  # Skip malformed / non-IP packets

            if not packets:
                return

            flows = Flow(packets).flows

            if not flows:
                return

            print(f"[LiveCapture Anomaly] Processing {len(flows)} flows from {len(packets)} packets...")

            conn = self._get_connection()
            if not conn:
                return

            anomaly_count = 0
            try:
                for flow_key, flow_packets in flows.items():
                    if self._analyze_flow(flow_key, flow_packets, conn):
                        anomaly_count += 1
            finally:
                conn.close()

            if anomaly_count:
                print(f"[LiveCapture Anomaly] Detected {anomaly_count} anomalous flows.")

        except Exception as e:
            print(f"[LiveCapture Anomaly Error] {e}")
            import traceback
            traceback.print_exc()

    def _analyze_flow(self, flow_key, flow_packets, conn):
        """Analyze a single flow with the anomaly model and store features.
        Returns True if an anomaly alert was created."""
        try:
            # compute_features is a static method — call directly on the packet list
            stats = Flow.compute_features(flow_packets)

            if len(stats) != len(self.feature_order):
                return False

            df = pd.DataFrame([stats], columns=self.feature_order)
            df_scaled = pd.DataFrame(
                self.scaler.transform(df), columns=self.feature_order
            )

            # Isolation Forest detects abnormal flows; the classifier still labels them.
            score = self.iso_forest.decision_function(df_scaled)[0]
            is_unknown = score < self.threshold

            proba = None
            try:
                pred = self.model.predict(df_scaled)[0]
                predicted_class = self.label_encoder.inverse_transform([pred])[0]
                try:
                    proba = self.model.predict_proba(df_scaled)[0]
                    confidence = float(proba.max())
                except Exception:
                    confidence = None
            except Exception:
                predicted_class = "Unknown Attack"
                confidence = float(abs(score))

            # If the anomaly detector fires but the classifier only says BENIGN,
            # label it with the strongest non-benign class if probabilities exist.
            if is_unknown and predicted_class == "BENIGN":
                relabeled = False
                if proba is not None:
                    try:
                        class_ids = list(getattr(self.model, "classes_", range(len(proba))))
                        non_benign = []
                        for class_id, probability in zip(class_ids, proba):
                            label = self.label_encoder.inverse_transform([class_id])[0]
                            if label != "BENIGN":
                                non_benign.append((float(probability), label))

                        if non_benign:
                            confidence, predicted_class = max(non_benign, key=lambda item: item[0])
                            relabeled = True
                    except Exception:
                        relabeled = False

                if not relabeled:
                    predicted_class = "Unknown Attack"
                    confidence = float(abs(score))

            # Build feature dict for storage
            features_dict = {
                self.feature_order[i]: float(stats[i])
                for i in range(len(self.feature_order))
            }

            # Always queue features for training data (continual learning)
            self._feature_queue.put({
                "features": features_dict,
                "predicted_label": predicted_class,
                "confidence": confidence,
            })

            # If attack detected, create alert
            if predicted_class != "BENIGN":
                time_str = get_ntp_time()
                src_ip, dst_ip, sport, dport, proto = flow_key
                message = f"Expected {predicted_class}"
                method = "anomaly"

                log = Log(time_str, "alert", src_ip, dst_ip, message, predicted_class, method)
                alert = Alert(time_str, src_ip, dst_ip, message, predicted_class, method)

                log.add_to_log_table(conn)
                alert_id = alert.add_to_alert_table(conn)

                # Store features for SHAP/LIME explanation
                store_alert_features(conn, alert_id, features_dict,
                                     predicted_class, confidence)

                with self._stats_lock:
                    self.alerts_generated += 1

                print(f"[LiveCapture ANOMALY] {predicted_class} | {src_ip} -> {dst_ip}")
                return True

            return False

        except Exception as e:
            print(f"[Flow Analysis Error] {e}")
            import traceback
            traceback.print_exc()
            return False

    # ========== Training Data Batch Writer ========== #

    def _batch_writer_loop(self):
        """Background thread that writes training data in batches."""
        batch = []
        while self._running or not self._feature_queue.empty():
            try:
                item = self._feature_queue.get(timeout=2)
                batch.append(item)

                if len(batch) >= self.BATCH_SIZE:
                    self._write_batch(batch)
                    batch = []
            except queue.Empty:
                if batch:
                    self._write_batch(batch)
                    batch = []

        # Final flush
        if batch:
            self._write_batch(batch)

    def _write_batch(self, batch):
        """Write a batch of training data to DB."""
        try:
            db = Database(self.db_path)
            conn = db.connect()
            if conn:
                store_batch_features(conn, batch, self.feature_order)
                conn.close()
                print(f"[LiveCapture] Stored {len(batch)} flow features for retraining.")
        except Exception as e:
            print(f"[Batch Write Error] {e}")

    def _flush_feature_queue(self):
        """Flush remaining items in the feature queue."""
        batch = []
        while not self._feature_queue.empty():
            try:
                batch.append(self._feature_queue.get_nowait())
            except queue.Empty:
                break
        if batch:
            self._write_batch(batch)

    def _get_connection(self):
        """Get a fresh database connection."""
        db = Database(self.db_path)
        return db.connect()

    def get_status(self):
        """Return current capture status as a dict."""
        with self._stats_lock:
            return {
                "running": self._running,
                "packets_captured": self.packets_captured,
                "alerts_generated": self.alerts_generated,
                "interface": self.interface or "",
                "interface_name": self._interface_name,
                "interface_desc": self._interface_desc,
                "pending_features": self._feature_queue.qsize(),
            }
