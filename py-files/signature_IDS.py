from concurrent.futures import ThreadPoolExecutor
from log import Log
from alert import Alert
from packet import Packet
from rule import Rule
from DB import Database
from ntp_time import get_ntp_time

class SignatureIDS:
    def __init__(self, rules, db_path='DB/IDS.db', max_workers=5):
        self.rules = [
            Rule(rule) for rule in rules
        ]
        
        self.db_path = db_path
        self.max_workers = max_workers

    def process_packet(self, pkt):
        conn = None
        try:
            DB_obj = Database(self.db_path)
            conn = DB_obj.connect()
            if not conn:
                print("[ERROR] Failed to establish database connection in thread.")
                return

            packet = Packet(pkt)
            
            for rule in self.rules:
                
                if rule.match_rule(packet):
                    # Use the actual packet timestamp (from PCAP), not current time
                    time = packet.get_packet_time_formatted()
                    src_ip = packet.get_src_ip()
                    dst_ip = packet.get_dst_ip()
                    
                    action = rule.action
                    message = rule.options.get("msg", "No message specified")
                    layer = rule.options.get("attack", "No attack type")
                    
                    method = "signature"

                    log = Log(
                        time,
                        action,
                        src_ip,
                        dst_ip,
                        message,
                        layer,
                        method
                    )
                    
                    alert = Alert(
                        time, 
                        src_ip, 
                        dst_ip, 
                        message,
                        layer, 
                        method
                    )

                    log.add_to_log_table(conn)
                    alert.add_to_alert_table(conn)

        except Exception as e:
            print(f"[ERROR] Failed to process packet: {type(e).__name__} - {e}")
        finally:
            if conn:
                conn.close()

    def detect(self, packets):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            
            futures = [executor.submit(self.process_packet, pkt) for pkt in packets]
            
            for future in futures:
                future.result()

        print(f"[INFO] Signature detection complete. Total packets processed: {len(packets)}")
    
    
    def predict_from_pcap(self, packets):
        alerts = []

        def process_single_packet(pkt):
            local_alerts = []
            try:
                packet = Packet(pkt)
                
                for rule in self.rules:
                
                    if rule.match_rule(packet):
                
                        alert = {
                            "time": packet.get_packet_time_formatted(),
                            "src_ip": packet.get_src_ip(),
                            "dst_ip": packet.get_dst_ip(),
                            "message": rule.options.get("msg", "No message specified"),
                            "layer": rule.options.get("attack", "No attack type"),
                            "method": "signature"
                        }
                
                        local_alerts.append(alert)
           
            except Exception as e:
                print(f"[ERROR] Predict packet failed: {type(e).__name__} - {e}")
           
            return local_alerts

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            
            results = executor.map(process_single_packet, packets)
            
            for res in results:
            
                alerts.extend(res)

        return alerts