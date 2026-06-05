"""Tests for Flow grouping and feature computation."""
import pytest
from scapy.all import Ether, IP, TCP, UDP, Raw
from packet import Packet
from flow import Flow


class TestFlowGrouping:
    def test_single_flow(self, tcp_syn_packet, tcp_psh_ack_packet):
        """Packets with same src/dst should be grouped into one flow."""
        p1 = Packet(tcp_syn_packet)
        p2 = Packet(tcp_psh_ack_packet)
        flow = Flow([p1, p2])
        assert len(flow.flows) == 1

    def test_multiple_flows(self, tcp_syn_packet, udp_packet):
        """Packets with different protocols should be in different flows."""
        p1 = Packet(tcp_syn_packet)
        p2 = Packet(udp_packet)
        flow = Flow([p1, p2])
        assert len(flow.flows) == 2

    def test_reverse_flow_grouped(self):
        """Forward and reverse packets should be in the same flow."""
        fwd = Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / TCP(sport=1234, dport=80, flags="S")
        rev = Ether() / IP(src="10.0.0.2", dst="10.0.0.1") / TCP(sport=80, dport=1234, flags="SA")
        p1 = Packet(fwd)
        p2 = Packet(rev)
        flow = Flow([p1, p2])
        assert len(flow.flows) == 1

    def test_empty_flow(self):
        """Empty packet list should produce no flows."""
        flow = Flow([])
        assert len(flow.flows) == 0


class TestFlowFeatures:
    def test_feature_count(self, tcp_psh_ack_packet):
        """Should produce exactly 20 features."""
        p = Packet(tcp_psh_ack_packet)
        features = Flow.compute_features([p])
        assert len(features) == 20

    def test_features_are_numeric(self, tcp_psh_ack_packet):
        """All features should be numeric."""
        import numbers
        p = Packet(tcp_psh_ack_packet)
        features = Flow.compute_features([p])
        for f in features:
            assert isinstance(f, numbers.Number)

    def test_features_with_bidirectional_flow(self):
        """Features computed from bidirectional flow."""
        fwd = Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / TCP(sport=1234, dport=80, flags="PA") / Raw(load=b"GET /test")
        rev = Ether() / IP(src="10.0.0.2", dst="10.0.0.1") / TCP(sport=80, dport=1234, flags="PA") / Raw(load=b"HTTP/1.1 200 OK")
        p1 = Packet(fwd)
        p2 = Packet(rev)
        features = Flow.compute_features([p1, p2])
        assert len(features) == 20
        # Total bytes should be positive
        assert features[7] > 0  # TotalLengthofFwdPackets


class TestFlowSafeInt:
    def test_valid_int(self):
        assert Flow.safe_int("80") == 80

    def test_invalid_int(self):
        assert Flow.safe_int("N/A") == 0

    def test_none_int(self):
        assert Flow.safe_int(None) == 0
