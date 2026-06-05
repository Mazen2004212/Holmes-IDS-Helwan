from packet import Packet
import json
import re

class Rule:
    def __init__(self, rule_dict):
        self.action = rule_dict["action"]
        self.protocol = rule_dict["protocol"]
        self.src_ip = rule_dict["src_ip"]
        self.dst_ip = rule_dict["dst_ip"]
        self.src_port = rule_dict["src_port"]
        self.dst_port = rule_dict["dst_port"]
        self.options = rule_dict.get("options", {})
    
    def matches(self, packet):##header
        if self.protocol != "any" and packet.get_key("protocol") != self.protocol:  
            return False
        if self.src_ip != "any" and packet.get_key("src_ip") != self.src_ip:
            return False
        if self.dst_ip != "any" and packet.get_key("dst_ip") != self.dst_ip:
            return False
        if self.src_port != "any" and packet.get_key("src_port") != self.src_port:
            return False
        if self.dst_port != "any" and packet.get_key("dst_port") != self.dst_port:
            return False
        return True
    
    def match_rule(self,packet):#Option
        if not self.matches(packet):
            return False
        if "content" in self.options:
            content = self.options["content"]
            payload = packet.payload            
            if content.startswith("!"):
                if content[1:] in payload:
                    return False
            else:
                if content not in payload:
                    return False 
        if "pcre" in self.options:
            pcre = self.options["pcre"]
            pcre = pcre.strip("/")  
            if pcre.startswith("(?i)"):
                pcre = pcre[4:]  
                pattern = re.compile(pcre, re.IGNORECASE) 
                
            else:
                pattern = re.compile(pcre) 

            payload = packet.payload
            
            if not pattern.search(payload):  
                return False

            
        if "flags" in self.options:
            
            flags = self.options["flags"]
            
            packet_flags = packet.flags
            
            if (flags != packet_flags):
                return False

    
        if "dsize" in self.options:
            
            dsize = self.options["dsize"]
            
            data_size = packet.data_size
            
            if data_size < dsize:
                return False

    
        if "threshold" in self.options:
            
            threshold = self.options["threshold"]
            
            if self.options["detection_filter"] == "track_by_src":
                
                src_ip_counts = Packet.get_src_counts()
                ips_to_delete = []
                
                for src_ip, count in src_ip_counts.items():
                    
                    if src_ip == packet.src_ip:
                        
                        if count < threshold:
                            return False
                        
                        else :
                            ips_to_delete.append(src_ip)
                            
                for ip in ips_to_delete:
                    
                    del src_ip_counts[ip]
        
                    
            elif self.options["detection_filter"] == "track_by_dst":
                
                dst_ip_counts = Packet.get_dst_counts()
                ips_to_delete = []
                
                for dst_ip, count in dst_ip_counts.items():
                    
                    if dst_ip == packet.dst_ip:
                        
                        if count < threshold:
                            return False
                        
                        else :
                            ips_to_delete.append(dst_ip)
                
                for ip in ips_to_delete:
                    
                    del dst_ip_counts[ip]

    
        if "itype" in self.options:

            itype = Packet.get_itype(packet)
            
            itype_rule = self.options["itype"]
            
            if itype != itype_rule:
                return False
    
    
        return True

    @staticmethod
    def get_rules_from_db(conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules")
        rows = cursor.fetchall()
    
        rules = []
        for row in rows:
            rules.append({
                "id": row[0],
                "action": row[1],
                "protocol": row[2],
                "src_ip": row[3],
                "src_port": row[4],
                "direction": row[5],
                "dst_ip": row[6],
                "dst_port": row[7],
                "options": json.loads(row[8]) 
            })
        
        return rules


    def __str__(self):   
         
        rule_info = {
            "protocol": self.protocol,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "options":self.options
        }
        
        return str(rule_info)