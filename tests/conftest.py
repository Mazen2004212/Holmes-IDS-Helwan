"""Shared pytest fixtures for HAWKEYE IDS tests."""
import sys
import os
import sqlite3
import json
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scapy.all import Ether, IP, TCP, UDP, ICMP, Raw, ARP
from packet import Packet
from DB import Database


# ========== Scapy Packet Fixtures ========== #

@pytest.fixture
def tcp_syn_packet():
    """A TCP SYN packet."""
    pkt = Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / TCP(sport=12345, dport=80, flags="S")
    return pkt


@pytest.fixture
def tcp_psh_ack_packet():
    """A TCP PSH+ACK packet with HTTP GET payload."""
    payload = b"GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n"
    pkt = Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / TCP(sport=12345, dport=80, flags="PA") / Raw(load=payload)
    return pkt


@pytest.fixture
def udp_packet():
    """A basic UDP packet."""
    pkt = Ether() / IP(src="192.168.1.1", dst="8.8.8.8") / UDP(sport=5000, dport=53) / Raw(load=b"query")
    return pkt


@pytest.fixture
def icmp_packet():
    """An ICMP echo request (ping)."""
    pkt = Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / ICMP(type=8)
    return pkt


@pytest.fixture
def arp_packet():
    """An ARP request packet."""
    pkt = Ether() / ARP(psrc="192.168.1.1", pdst="192.168.1.2")
    return pkt


# ========== Database Fixtures ========== #

@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database with all tables."""
    db = Database(":memory:")
    conn = db.connect()
    
    # Create tables
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT, protocol TEXT, src_ip TEXT, src_port TEXT,
            direction TEXT, dst_ip TEXT, dst_port TEXT, options TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY, timestamp DATETIME, event_type TEXT,
            src_ip TEXT, dst_ip TEXT, message TEXT, attack TEXT, method TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME,
            src_ip TEXT, dst_ip TEXT, message TEXT, attack TEXT, method TEXT
        )
    """)
    conn.commit()
    
    yield conn
    conn.close()


@pytest.fixture
def sample_rule_dict():
    """A sample rule dictionary for testing."""
    return {
        "action": "alert",
        "protocol": "tcp",
        "src_ip": "any",
        "dst_ip": "any",
        "src_port": "any",
        "dst_port": "80",
        "options": {
            "msg": "HTTP GET detected",
            "content": "GET",
            "flags": "PA",
            "attack": "Application Layer Attack"
        }
    }


@pytest.fixture
def sample_rule_negated_content():
    """A rule with negated content (!)."""
    return {
        "action": "alert",
        "protocol": "tcp",
        "src_ip": "any",
        "dst_ip": "any",
        "src_port": "any",
        "dst_port": "80",
        "options": {
            "msg": "Non-GET HTTP detected",
            "content": "!GET",
            "attack": "Application Layer Attack"
        }
    }


@pytest.fixture
def sample_rule_dsize():
    """A rule with dsize option."""
    return {
        "action": "alert",
        "protocol": "tcp",
        "src_ip": "any",
        "dst_ip": "any",
        "src_port": "any",
        "dst_port": "any",
        "options": {
            "msg": "Large packet",
            "dsize": 50,
            "attack": "Transport Layer Attack"
        }
    }


@pytest.fixture
def sample_rule_pcre():
    """A rule with PCRE regex option."""
    return {
        "action": "alert",
        "protocol": "tcp",
        "src_ip": "any",
        "dst_ip": "any",
        "src_port": "any",
        "dst_port": "80",
        "options": {
            "msg": "HTTP GET index",
            "pcre": "/GET\\s+\\/index/",
            "attack": "Application Layer Attack"
        }
    }


@pytest.fixture(autouse=True)
def reset_packet_counters():
    """Reset Packet class counters before each test."""
    Packet.reset_counts()
    yield
    Packet.reset_counts()
