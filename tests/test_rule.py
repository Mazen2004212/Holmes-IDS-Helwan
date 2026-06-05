"""Tests for the Rule class and its matching logic."""
import pytest
from scapy.all import Ether, IP, TCP, UDP, ICMP, Raw
from packet import Packet
from rule import Rule


class TestRuleHeaderMatching:
    def test_matches_any_protocol(self, tcp_syn_packet):
        rule = Rule({
            "action": "alert", "protocol": "any",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {}
        })
        p = Packet(tcp_syn_packet)
        assert rule.matches(p) is True

    def test_matches_specific_protocol(self, tcp_syn_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {}
        })
        p = Packet(tcp_syn_packet)
        assert rule.matches(p) is True

    def test_no_match_wrong_protocol(self, udp_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {}
        })
        p = Packet(udp_packet)
        assert rule.matches(p) is False

    def test_matches_specific_src_ip(self, tcp_syn_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "10.0.0.1", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {}
        })
        p = Packet(tcp_syn_packet)
        assert rule.matches(p) is True

    def test_no_match_wrong_src_ip(self, tcp_syn_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "99.99.99.99", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {}
        })
        p = Packet(tcp_syn_packet)
        assert rule.matches(p) is False

    def test_matches_dst_port(self, tcp_syn_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {}
        })
        p = Packet(tcp_syn_packet)
        assert rule.matches(p) is True


class TestRuleContentMatching:
    def test_content_match(self, tcp_psh_ack_packet):
        """Content present in payload → rule should match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "GET"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is True

    def test_content_no_match(self, tcp_psh_ack_packet):
        """Content NOT in payload → rule should not match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "POST"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is False

    def test_negated_content_match(self, tcp_psh_ack_packet):
        """Negated content: !POST means 'match if POST is NOT present'."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "!POST"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is True  # POST is not in GET payload

    def test_negated_content_no_match(self, tcp_psh_ack_packet):
        """Negated content: !GET means 'match if GET is NOT present' → should NOT match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "!GET"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is False  # GET IS present, so negation fails


class TestRuleFlagsMatching:
    def test_flags_match(self, tcp_psh_ack_packet):
        p = Packet(tcp_psh_ack_packet)
        # Scapy extracts flags in bit order: ACK(0x10) before PSH(0x08) → "AP"
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"flags": p.flags}
        })
        assert rule.match_rule(p) is True

    def test_flags_no_match(self, tcp_syn_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"flags": "PA"}
        })
        p = Packet(tcp_syn_packet)
        assert rule.match_rule(p) is False


class TestRuleDsizeMatching:
    def test_dsize_above_threshold(self, tcp_psh_ack_packet):
        """Packet size >= dsize → should match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {"dsize": 10}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is True

    def test_dsize_below_threshold(self, tcp_psh_ack_packet):
        """Packet size < dsize → should NOT match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {"dsize": 99999}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is False


class TestRulePCRE:
    def test_pcre_match(self, tcp_psh_ack_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"pcre": "/GET\\s+\\/index/"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is True

    def test_pcre_case_insensitive(self, tcp_psh_ack_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"pcre": "/(?i)get\\s+\\/INDEX/"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is True

    def test_pcre_no_match(self, tcp_psh_ack_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"pcre": "/POST\\s+\\/admin/"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert rule.match_rule(p) is False


class TestRuleICMP:
    def test_itype_match(self, icmp_packet):
        rule = Rule({
            "action": "alert", "protocol": "icmp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {"itype": 8}
        })
        p = Packet(icmp_packet)
        assert rule.match_rule(p) is True

    def test_itype_no_match(self, icmp_packet):
        rule = Rule({
            "action": "alert", "protocol": "icmp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {"itype": 3}
        })
        p = Packet(icmp_packet)
        assert rule.match_rule(p) is False


class TestRuleGetFromDB:
    def test_get_rules_from_db(self, in_memory_db):
        """Test loading rules from the database."""
        import json
        cursor = in_memory_db.cursor()
        options = json.dumps({"msg": "Test rule", "content": "GET"})
        cursor.execute(
            "INSERT INTO rules (action, protocol, src_ip, src_port, direction, dst_ip, dst_port, options) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("alert", "tcp", "any", "any", "->", "any", "80", options)
        )
        in_memory_db.commit()

        rules = Rule.get_rules_from_db(in_memory_db)
        assert len(rules) == 1
        assert rules[0]["action"] == "alert"
        assert rules[0]["options"]["msg"] == "Test rule"
