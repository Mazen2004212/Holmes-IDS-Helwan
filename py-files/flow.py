from collections import defaultdict
import numpy as np

class Flow:
    def __init__(self, packet_list):
        self.packet_list = packet_list
        self.flows = self.group_into_flows(packet_list)

    @staticmethod
    def safe_int(value):
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def group_into_flows(packet_list):
        flows = defaultdict(list)
        for pkt in packet_list:
            key = (pkt.src_ip, pkt.dst_ip, pkt.src_port, pkt.dst_port, pkt.protocol)
            reverse_key = (pkt.dst_ip, pkt.src_ip, pkt.dst_port, pkt.src_port, pkt.protocol)

            if reverse_key in flows:
                flows[reverse_key].append(pkt)
            else:
                flows[key].append(pkt)
        return flows

    @staticmethod
    def compute_features(flow_packets):
        fwd_sizes, bwd_sizes = [], []
        fwd_seg_size, bwd_seg_size = [], []
        fwd_times, bwd_times = [], []

        fwd_header_len = bwd_header_len = 0
        subflow_fwd_bytes = subflow_bwd_bytes = 0
        init_win_bytes_bwd = 0

        flow_start = flow_packets[0].time
        flow_end = flow_start

        src_ip = flow_packets[0].src_ip
        dst_ip = flow_packets[0].dst_ip

        prev_fwd_time = prev_bwd_time = None

        for pkt in flow_packets:
            direction = 'fwd' if pkt.src_ip == src_ip else 'bwd'
            pkt_time = pkt.time
            pkt_size = pkt.data_size
            flow_end = max(flow_end, pkt_time)

            header_len = pkt.get_header_length()
            seg_size = pkt.get_payload_length()

            if direction == 'fwd':
                fwd_sizes.append(pkt_size)
                subflow_fwd_bytes += pkt_size
                fwd_seg_size.append(seg_size)
                fwd_header_len += header_len
                
                if prev_fwd_time is not None:
                    fwd_times.append(pkt_time - prev_fwd_time)
                prev_fwd_time = pkt_time
            else:
                bwd_sizes.append(pkt_size)
                subflow_bwd_bytes += pkt_size
                bwd_seg_size.append(seg_size)
                bwd_header_len += header_len
                
                if init_win_bytes_bwd == 0:
                    init_win_bytes_bwd = pkt.get_window_size()
                
                if prev_bwd_time is not None:
                    bwd_times.append(pkt_time - prev_bwd_time)
                prev_bwd_time = pkt_time

        flow_duration = flow_end - flow_start if flow_end > flow_start else 1e-6
        total_pkt_count = len(fwd_sizes) + len(bwd_sizes)
        total_bytes = subflow_fwd_bytes + subflow_bwd_bytes

        dst_port = Flow.safe_int(flow_packets[0].dst_port) if flow_packets else 0

        features = [
            np.mean(fwd_sizes) if fwd_sizes else 0,                      # FwdPacketLengthMean
            np.max(fwd_sizes) if fwd_sizes else 0,                       # FwdPacketLengthMax
            max(fwd_times + bwd_times) if (fwd_times + bwd_times) else 0,# FlowIATMax
            subflow_bwd_bytes,                                           # SubflowBwdBytes
            init_win_bytes_bwd,                                          # Init_Win_bytes_backward
            sum(bwd_sizes),                                              # TotalLengthofBwdPackets
            total_pkt_count / flow_duration if flow_duration else 0,     # FlowPackets/s
            sum(fwd_sizes),                                              # TotalLengthofFwdPackets
            len(bwd_sizes) / flow_duration if flow_duration else 0,      # BwdPackets/s
            np.mean(fwd_sizes + bwd_sizes) if total_pkt_count else 0,    # AveragePacketSize
            flow_duration,                                               # FlowDuration
            np.mean(bwd_sizes) if bwd_sizes else 0,                      # BwdPacketLengthMean
            subflow_fwd_bytes,                                           # SubflowFwdBytes
            np.mean(bwd_seg_size) if bwd_seg_size else 0,                # AvgBwdSegmentSize
            np.std(fwd_sizes) if fwd_sizes else 0,                       # FwdPacketLengthStd
            np.mean(fwd_seg_size) if fwd_seg_size else 0,                # AvgFwdSegmentSize
            dst_port,                                                    # DestinationPort
            bwd_header_len,                                              # BwdHeaderLength
            np.mean(fwd_sizes + bwd_sizes) if total_pkt_count else 0,    # PacketLengthMean
            np.std(bwd_sizes) if bwd_sizes else 0                        # BwdPacketLengthStd
        ]

        return features
