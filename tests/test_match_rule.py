"""Tests for the standalone match_rule() function."""
import pytest
from scapy.all import Ether, IP, TCP, UDP, ICMP, Raw
from packet import Packet
from rule import Rule
from match_rule import match_rule


class TestMatchRuleContent:
    def test_content_present_matches(self, tcp_psh_ack_packet):
        """Content found in payload → should return True (match)."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "GET"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) is True

    def test_content_absent_no_match(self, tcp_psh_ack_packet):
        """Content NOT in payload → should return False."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "DELETE"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) is False

    def test_negated_content_not_present(self, tcp_psh_ack_packet):
        """Negated content: !POST, POST not in payload → match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "!POST"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) is True

    def test_negated_content_present(self, tcp_psh_ack_packet):
        """Negated content: !GET, GET IS in payload → no match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "!GET"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) is False


class TestMatchRuleDsize:
    def test_dsize_packet_large_enough(self, tcp_psh_ack_packet):
        """Packet size >= dsize → should match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {"dsize": 10}
        })
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) is True

    def test_dsize_packet_too_small(self, tcp_psh_ack_packet):
        """Packet size < dsize → should NOT match."""
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {"dsize": 99999}
        })
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) is False


class TestMatchRuleFlags:
    def test_flags_match(self, tcp_psh_ack_packet):
        p = Packet(tcp_psh_ack_packet)
        # Scapy extracts flags in bit order: ACK(0x10) before PSH(0x08) → "AP"
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "any",
            "options": {"flags": p.flags}
        })
        assert match_rule(p, rule) is True


class TestMatchRulePCRE:
    def test_pcre_match(self, tcp_psh_ack_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"pcre": "/GET\\s+\\/index/"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) is True

    def test_pcre_no_match(self, tcp_psh_ack_packet):
        rule = Rule({
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"pcre": "/POST\\s+\\/admin/"}
        })
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) is False


class TestMatchRuleConsistency:
    """Verify match_rule() gives same results as Rule.match_rule()."""

    def test_content_consistency(self, tcp_psh_ack_packet):
        rule_dict = {
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "GET", "flags": "PA"}
        }
        rule = Rule(rule_dict)
        p = Packet(tcp_psh_ack_packet)
        assert match_rule(p, rule) == rule.match_rule(p)

    def test_no_match_consistency(self, tcp_syn_packet):
        rule_dict = {
            "action": "alert", "protocol": "tcp",
            "src_ip": "any", "dst_ip": "any",
            "src_port": "any", "dst_port": "80",
            "options": {"content": "GET", "flags": "PA"}
        }
        rule = Rule(rule_dict)
        p = Packet(tcp_syn_packet)
        assert match_rule(p, rule) == rule.match_rule(p)
