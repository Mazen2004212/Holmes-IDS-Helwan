from scapy.all import rdpcap
from packet import Packet
from tqdm import tqdm

def main():
    pcap_path = "test/BENIGN.pcapng"  

    print("[INFO] Reading packets...")
    scapy_packets = rdpcap(pcap_path)

    print(f"[INFO] Total packets loaded: {len(scapy_packets)}\n")

    for i, pkt in enumerate(tqdm(scapy_packets), 1):
        try:
            p = Packet(pkt)

            print(f"\nPacket #{i}")
            print(f"Time: {p.time_formatted}")
            print(f"Protocol: {p.protocol}")
            print(f"Source IP: {p.src_ip}")
            print(f"Destination IP: {p.dst_ip}")
            print(f"Source Port: {p.src_port}")
            print(f"Destination Port: {p.dst_port}")
            print(f"Flags: {p.flags}")
            print(f"Data Size: {p.data_size}")
            print(f"Payload: {p.payload[:100]}")  

        except Exception as e:
            print(f"[ERROR] Failed to process packet #{i}: {e}")

    print("\n[INFO] Done processing packets.")

if __name__ == "__main__":
    main()
