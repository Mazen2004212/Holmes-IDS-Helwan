"""Tests for the Packet class."""
import pytest
import threading
from scapy.all import Ether, IP, TCP, UDP, ICMP, Raw, ARP
from packet import Packet


class TestPacketProtocol:
    def test_tcp_protocol(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.protocol == "tcp"

    def test_udp_protocol(self, udp_packet):
        p = Packet(udp_packet)
        assert p.protocol == "udp"

    def test_icmp_protocol(self, icmp_packet):
        p = Packet(icmp_packet)
        assert p.protocol == "icmp"

    def test_arp_protocol(self, arp_packet):
        p = Packet(arp_packet)
        assert p.protocol == "arp"


class TestPacketIPExtraction:
    def test_tcp_src_ip(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.src_ip == "10.0.0.1"

    def test_tcp_dst_ip(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.dst_ip == "10.0.0.2"

    def test_arp_src_ip(self, arp_packet):
        p = Packet(arp_packet)
        assert p.src_ip == "192.168.1.1"

    def test_arp_dst_ip(self, arp_packet):
        p = Packet(arp_packet)
        assert p.dst_ip == "192.168.1.2"


class TestPacketPortExtraction:
    def test_tcp_src_port(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.src_port == "12345"

    def test_tcp_dst_port(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.dst_port == "80"

    def test_udp_src_port(self, udp_packet):
        p = Packet(udp_packet)
        assert p.src_port == "5000"

    def test_icmp_no_port(self, icmp_packet):
        p = Packet(icmp_packet)
        assert p.src_port == "N/A"
        assert p.dst_port == "N/A"


class TestPacketFlags:
    def test_syn_flag(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert "S" in p.flags

    def test_psh_ack_flags(self, tcp_psh_ack_packet):
        p = Packet(tcp_psh_ack_packet)
        assert "P" in p.flags
        assert "A" in p.flags

    def test_no_flags_icmp(self, icmp_packet):
        p = Packet(icmp_packet)
        # ICMP has IP-level flags
        assert p.flags is not None


class TestPacketPayload:
    def test_has_payload(self, tcp_psh_ack_packet):
        p = Packet(tcp_psh_ack_packet)
        assert "GET" in p.payload
        assert "/index.html" in p.payload

    def test_no_payload(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.payload == ""


class TestPacketSize:
    def test_size_positive(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.data_size > 0


class TestPacketCounters:
    def test_src_ip_count_increments(self, tcp_syn_packet):
        Packet.reset_counts()
        p1 = Packet(tcp_syn_packet)
        assert Packet.src_ip_count.get("10.0.0.1") == 1

        p2 = Packet(tcp_syn_packet)
        assert Packet.src_ip_count.get("10.0.0.1") == 2

    def test_reset_counts(self, tcp_syn_packet):
        Packet(tcp_syn_packet)
        Packet.reset_counts()
        assert len(Packet.src_ip_count) == 0
        assert len(Packet.dst_ip_count) == 0

    def test_thread_safety(self, tcp_syn_packet):
        """Verify counters work correctly under concurrent access."""
        Packet.reset_counts()
        errors = []
        
        def create_packets():
            try:
                for _ in range(100):
                    Packet(tcp_syn_packet)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_packets) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert Packet.src_ip_count.get("10.0.0.1") == 500


class TestPacketICMP:
    def test_itype(self, icmp_packet):
        p = Packet(icmp_packet)
        assert p.get_itype() == 8  # Echo request

    def test_itype_no_icmp(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.get_itype() is None


class TestPacketStr:
    def test_str_representation(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        s = str(p)
        assert "10.0.0.1" in s
        assert "tcp" in s


class TestPacketGetKey:
    def test_get_key_protocol(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.get_key("protocol") == "tcp"

    def test_get_key_invalid(self, tcp_syn_packet):
        p = Packet(tcp_syn_packet)
        assert p.get_key("nonexistent") == "Key not found"
