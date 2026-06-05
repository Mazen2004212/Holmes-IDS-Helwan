import re
from packet import Packet
   
def match_rule(packet, rule):
    
    if not rule.matches(packet):
        return False
    
#####################################################################################################################
    
    if "content" in rule.options:
        
        content = rule.options["content"]
        
        payload = packet.payload
        
        if content.startswith("!"):
            if content[1:] in payload:
                return False
        else:
            if content not in payload:
                return False 
    
#####################################################################################################################

    if "pcre" in rule.options:
        pcre = rule.options["pcre"]

        pcre = pcre.strip("/")  

        
        if pcre.startswith("(?i)"):
            pcre = pcre[4:]  
            pattern = re.compile(pcre, re.IGNORECASE) 
            
        else:
            pattern = re.compile(pcre) 

        payload = packet.payload
        
        if not pattern.search(payload):  
            return False

#####################################################################################################################
        
    if "flags" in rule.options:
        
        flags = rule.options["flags"]
        
        packet_flags = packet.flags
        
        if flags != packet_flags:
            return False

#####################################################################################################################

    if "dsize" in rule.options:
        
        dsize = rule.options["dsize"]
        
        data_size = packet.data_size
        
        if data_size < dsize:
            return False

#####################################################################################################################

    if "threshold" in rule.options:
        
        threshold = rule.options["threshold"]
        
        if rule.options["detection_filter"] == "track_by_src":
            
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
    
        elif rule.options["detection_filter"] == "track_by_dst":
            
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

#####################################################################################################################

    if "itype" in rule.options:

        itype = Packet.get_itype(packet)
        
        itype_rule = rule.options["itype"]

        if itype != itype_rule:
            return False
 
#####################################################################################################################

    return True
