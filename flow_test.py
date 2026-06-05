from scapy.all import rdpcap
from packet import Packet
from flow import Flow

def main():
    # === 1. Load PCAP File ===
    pcap_file = "test/BENIGN.pcapng"
    scapy_packets = rdpcap(pcap_file)

    # === 2. Convert to Packet objects ===
    parsed_packets = []
    for pkt in scapy_packets:
        try:
            parsed_packet = Packet(pkt)
            parsed_packets.append(parsed_packet)
        except Exception as e:
            print(f"[!] Failed to parse packet: {e}")

    # === 3. Group into flows and compute features ===
    flow_handler = Flow(parsed_packets)

    print(f"\n[+] Total Flows Detected: {len(flow_handler.flows)}")

    for i, (flow_key, packets) in enumerate(flow_handler.flows.items(), 1):
        features = Flow.compute_features(packets)
        print(f"\n--- Flow #{i} ---")
        print(f"Key: {flow_key}")
        print("Features:")
        for j, feat in enumerate(features, 1):
            print(f"  Feature {j}: {feat:.4f}")

if __name__ == "__main__":
    main()
