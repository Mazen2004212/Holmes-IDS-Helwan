from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import pandas as pd
from DB import Database
from log import Log
from alert import Alert
from flow import Flow
from packet import Packet
from explainability import store_alert_features

class AnomalyIDS:
    def __init__(self, clf_model, iso_model, scaler, label_encoder, feature_order,
                 db_path="DB/IDS.db", threshold=-0.000001):
        self.clf_model = clf_model
        self.iso_model = iso_model
        self.scaler = scaler
        self.label_encoder = label_encoder
        self.feature_order = feature_order
        self.threshold = threshold
        self.db_path = db_path

    def process_flow(self, flow_item, conn=None):
        flow_key, flow_packets = flow_item
        own_conn = False

        try:
            if conn is None:
                DB = Database(self.db_path)
                conn = DB.connect()
                own_conn = True

            flow_handler = Flow(flow_packets)
            stats = flow_handler.compute_features(flow_packets)

            pkt_obj = flow_packets[0]
            raw_features = stats

            if len(raw_features) != len(self.feature_order):
                raise ValueError("Mismatch between extracted features and model's feature order")

            df = pd.DataFrame([raw_features], columns=self.feature_order)
            df_scaled = pd.DataFrame(self.scaler.transform(df), columns=self.feature_order)

            # Get isolation forest score for confidence
            score = self.iso_model.decision_function(df_scaled)[0]
            if score < self.threshold:
                predicted_class = "Unknown Attack"
                confidence = float(abs(score))
            else:
                pred = self.clf_model.predict(df_scaled)[0]
                predicted_class = self.label_encoder.inverse_transform([pred])[0]
                # Use predict_proba for confidence
                try:
                    proba = self.clf_model.predict_proba(df_scaled)[0]
                    confidence = float(proba.max())
                except Exception:
                    confidence = None

            if predicted_class != "BENIGN":
                timestamp = datetime.fromtimestamp(pkt_obj.time).strftime("%Y-%m-%d %H:%M:%S")
                src_ip, dst_ip, sport, dport, proto = flow_key
                message = f"Expected {predicted_class}"
                method = "anomaly"
                action = "alert"

                log = Log(timestamp, action, src_ip, dst_ip, message, proto, method)
                alert = Alert(timestamp, src_ip, dst_ip, message, proto, method)

                log.add_to_log_table(conn)
                alert_id = alert.add_to_alert_table(conn)

                # Store raw features linked to this alert for SHAP/LIME explanation
                features_dict = {
                    self.feature_order[i]: float(raw_features[i])
                    for i in range(len(self.feature_order))
                }
                store_alert_features(conn, alert_id, features_dict,
                                     predicted_class, confidence)

        except Exception as e:
            print(f"[ERROR] Failed to process flow {flow_key}: {e}")

        finally:
            if own_conn and conn:
                conn.close()

    def detect(self, scapy_packets, threads=10):
        try:
            packets = [Packet(pkt) for pkt in scapy_packets]
            flows = Flow(packets).flows

            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = [executor.submit(self.process_flow, flow) for flow in flows.items()]
                for future in futures:
                    future.result()

            print(f"[INFO] Anomaly detection complete. Total flows processed: {len(flows)}")

        except Exception as e:
            print(f"[CRITICAL] Anomaly detection failed: {e}")

    def predict_from_csv(self, csv_path):
        try:
            df = pd.read_csv(csv_path)

            # ---- Column name normalization ----
            # CIC-IDS-2017 CSVs have leading spaces and inconsistent naming.
            # Build a mapping: normalized_name -> original_csv_column
            # Normalization: strip whitespace, remove spaces, lowercase
            def _normalize(name):
                return name.strip().replace(' ', '').replace('_', '').lower()

            csv_col_map = {_normalize(c): c for c in df.columns}

            # Try to map each feature_order name to a CSV column
            rename_map = {}
            missing = []
            for feat in self.feature_order:
                norm_feat = _normalize(feat)
                if feat in df.columns:
                    # Exact match — no rename needed
                    pass
                elif norm_feat in csv_col_map:
                    rename_map[csv_col_map[norm_feat]] = feat
                else:
                    missing.append(feat)

            if missing:
                raise KeyError(
                    f"CSV is missing {len(missing)} required feature columns: "
                    f"{missing[:5]}{'...' if len(missing) > 5 else ''}. "
                    f"CSV columns: {list(df.columns[:10])}..."
                )

            if rename_map:
                df = df.rename(columns=rename_map)

            df = df[self.feature_order]

            # ---- Replace inf / NaN with 0 ----
            df = df.replace([float('inf'), float('-inf')], 0).fillna(0)

            # ---- Scale ----
            df_scaled = pd.DataFrame(
                self.scaler.transform(df), columns=self.feature_order
            )

            # ---- Vectorized prediction ----
            # Isolation forest scores (batch)
            scores = self.iso_model.decision_function(df_scaled)
            unknown_mask = scores < self.threshold

            # Classifier predictions (batch) for non-unknown rows
            classifier_preds = self.clf_model.predict(df_scaled)
            classifier_labels = self.label_encoder.inverse_transform(classifier_preds)

            # Merge: use "Unknown Attack" where isolation forest flags, else classifier
            predictions = []
            for i in range(len(df_scaled)):
                if unknown_mask[i]:
                    predictions.append("Unknown Attack")
                else:
                    predictions.append(classifier_labels[i])

            # Stats
            stats = {"BENIGN": 0, "ATTACK": 0, "UNKNOWN": 0}
            for p in predictions:
                if p == "Unknown Attack":
                    stats["UNKNOWN"] += 1
                elif p == "BENIGN":
                    stats["BENIGN"] += 1
                else:
                    stats["ATTACK"] += 1

            # Features list for explainability
            features_list = [
                {self.feature_order[j]: float(df.iloc[i, j])
                 for j in range(len(self.feature_order))}
                for i in range(len(df))
            ]

            return predictions, stats, features_list

        except KeyError as e:
            print(f"[ERROR] CSV column mismatch: {e}")
            raise  # Let the API route return the actual error message
        except Exception as e:
            print(f"[ERROR] Failed to predict from CSV: {e}")
            import traceback
            traceback.print_exc()
            raise  # Let the API route return the actual error message