import numpy as np
import threading
from collections import defaultdict
from scapy.all import TCP,UDP,ICMP,Ether,IP,ARP,Raw
from datetime import datetime


class Packet:
    src_ip_count = {}
    dst_ip_count = {}
    _lock = threading.Lock()
    
    
    def __init__(self, scapy_packet):
        
        self.scapy_packet = scapy_packet
        self.protocol = self.extract_protocol()
        self.src_ip = self.get_src_ip()
        self.dst_ip = self.get_dst_ip()
        self.src_port = self.get_src_port()
        self.dst_port = self.get_dst_port()
        self.flags = self.extract_flags()
        self.data_size = self.get_pkt_size()
        self.payload = self.extract_payload()
        self.time = self.get_packet_time()
        self.time_formatted = self.get_packet_time_formatted()
        self.src_ip_count = self.update_src_ip_count()
        self.dst_ip_count = self.update_dst_ip_count()
    
    def get_itype(self):
         return self.scapy_packet[ICMP].type if ICMP in self.scapy_packet else None
    
    def get_packet_time_formatted(self):
        pkt = self.scapy_packet
        packet_time = float(pkt.time)
        
        formatted_time = datetime.fromtimestamp(packet_time).strftime("%Y-%m-%d %H:%M:%S")
        
        return formatted_time
    
    def get_packet_time(self):
        return float(self.scapy_packet.time)  
    
    def update_src_ip_count(self):
        with Packet._lock:
            if self.src_ip in Packet.src_ip_count:
                Packet.src_ip_count[self.src_ip] += 1
            else:
                Packet.src_ip_count[self.src_ip] = 1
            
    def update_dst_ip_count(self):
        with Packet._lock:
            if self.dst_ip in Packet.dst_ip_count:
                Packet.dst_ip_count[self.dst_ip] += 1
            else:
                Packet.dst_ip_count[self.dst_ip] = 1
    
    def extract_protocol(self):
        
        pkt = self.scapy_packet
        
        if pkt.haslayer(TCP):
            return "tcp"
        
        elif pkt.haslayer(UDP):
            return "udp"
        
        elif pkt.haslayer(ARP):
            return "arp"
        
        elif pkt.haslayer(ICMP):
            return "icmp"
        
        elif pkt.haslayer(IP):
            return "ip"
        
        else:
            return f"N/A"

    def get_src_ip(self):
        
        pkt = self.scapy_packet
        
        if pkt.haslayer(IP):#network
            return pkt[IP].src#srcip
        
        elif pkt.haslayer(ARP):#data
            return pkt[ARP].psrc#srcip
        
        else:
            return "N/A"

    def get_dst_ip(self):
        
        pkt = self.scapy_packet
        
        if pkt.haslayer(IP):
            return pkt[IP].dst
        
        elif pkt.haslayer(ARP):
            return pkt[ARP].pdst
        
        else:
            return "N/A"

    def get_src_port(self):
        
        pkt = self.scapy_packet
        
        if pkt.haslayer(TCP):
            return str(pkt[TCP].sport)
        
        elif pkt.haslayer(UDP):
            return str(pkt[UDP].sport)
        
        else:
            return "N/A"

    def get_dst_port(self):
        
        pkt = self.scapy_packet
        
        if pkt.haslayer(TCP):
            return str(pkt[TCP].dport)
        
        elif pkt.haslayer(UDP):
            return str(pkt[UDP].dport)
        
        else:
            return "N/A"

    def extract_flags(self):
        pkt = self.scapy_packet

        if pkt.haslayer(TCP):
            tcp_flags = pkt[TCP].flags
            
            flags = []

            if tcp_flags & 0x02:  # SYN
                flags.append("S")
                
            if tcp_flags & 0x10:  # ACK
                flags.append("A")
                
            if tcp_flags & 0x01:  # FIN
                flags.append("F")
                
            if tcp_flags & 0x08:  # PSH
                flags.append("P")
                
            if tcp_flags & 0x04:  # RST
                flags.append("R")
                
            if tcp_flags & 0x20:  # URG
                flags.append("U")
                
            if tcp_flags & 0x40:  # ECE
                flags.append("E")
                
            if tcp_flags & 0x80:  # CWR
                flags.append("C")

            return ''.join(flags)

        elif pkt.haslayer(IP):
            ip_flags = pkt[IP].flags
            flags = []

            if ip_flags & 0x02:  # DF (Don't Fragment)
                flags.append("DF")
                
            if ip_flags & 0x01:  # MF (More Fragments)
                flags.append("MF")

            return ', '.join(flags) if flags else "No Flags"

        else:
            return "N/A"

    def get_header_length(self):
        if self.scapy_packet.haslayer('TCP'):
            tcp_layer = self.scapy_packet.getlayer('TCP')
            dataofs = tcp_layer.dataofs
            return (dataofs if dataofs is not None else 5) * 4
        
        elif self.scapy_packet.haslayer('UDP'):
            return 8
        
        elif self.scapy_packet.haslayer('IP'):
            ip_layer = self.scapy_packet.getlayer('IP')
            ihl = ip_layer.ihl
            return (ihl if ihl is not None else 5) * 4
        
        return 0
    
    def get_window_size(self):
        if self.scapy_packet.haslayer('TCP'):
            tcp_layer = self.scapy_packet.getlayer('TCP')
            return tcp_layer.window
        return 0
    
    def get_pkt_size(self):
        pkt = self.scapy_packet
        return len(pkt)
        
    def get_payload_length(self):
        # Assuming you want the length of the TCP/UDP payload, not including headers
        if self.scapy_packet.haslayer('TCP'):
            tcp_layer = self.scapy_packet['TCP']
            return len(tcp_layer.payload)
        elif self.scapy_packet.haslayer('UDP'):
            udp_layer = self.scapy_packet['UDP']
            return len(udp_layer.payload)
        else:
            # fallback: maybe no TCP/UDP layer, return 0 or total length minus headers
            return 0
    
    def extract_payload(self):
        pkt = self.scapy_packet
        
        if pkt.haslayer(Raw):
            
            try:
                payload = pkt[Raw].load.decode(errors="ignore")
                
                return payload
            
            except Exception as e:
                return pkt[Raw].load.hex()
        
        else:
            return ""
        
    @staticmethod
    def get_src_counts():
        return Packet.src_ip_count
    
    @staticmethod
    def get_dst_counts():
        return Packet.dst_ip_count

    @staticmethod
    def reset_counts():
        with Packet._lock:
            Packet.src_ip_count.clear()
            Packet.dst_ip_count.clear()
    

    def __str__(self):
        
        packet_info = {
            "protocol": self.protocol,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "flags": self.flags,
            "dataSize":self.data_size,
            "payload": self.payload
        }
        
        return str(packet_info)

    def get_key(self, key):
        
        packet_info = {
            "protocol": self.protocol,
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "flags": self.flags,
            "dataSize": self.data_size,
            "payload": self.payload,
        }
        
        return packet_info.get(key, "Key not found")  
    