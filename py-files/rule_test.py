from scapy.all import rdpcap
from packet import Packet
from rule import Rule

def main():
    pcap_file = "test/BENIGN.pcapng"  
    packets = rdpcap(pcap_file)

    rule_dict = {
        "action": "alert",
        "protocol": "tcp",
        "src_ip": "any",
        "dst_ip": "any",
        "src_port": "any",
        "dst_port": "80",
        "options": {
            "content": "GET",
            "flags": "PA",
            "dsize": 50,
            "pcre": "/GET\s+\/index/",
            "threshold": 1,
            "detection_filter": "track_by_src"
        }
    }

    rule = Rule(rule_dict)

    for i, pkt in enumerate(packets, 1):
        try:
            p = Packet(pkt)
            if rule.match_rule(p):
                print(f"\nMatched Packet #{i}")
                print(f"  Time: {p.time_formatted}")
                print(f"  Protocol: {p.protocol}")
                print(f"  Src IP: {p.src_ip}:{p.src_port}")
                print(f"  Dst IP: {p.dst_ip}:{p.dst_port}")
                print(f"  Flags: {p.flags}")
                print(f"  Payload: {p.payload[:80]}")
        except Exception as e:
            print(f"[ERROR] Packet #{i} failed: {e}")

    print("\n✅ Done testing rules.")

if __name__ == "__main__":
    main()
