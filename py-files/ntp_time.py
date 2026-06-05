"""NTP time synchronization utility.
Queries an NTP server to get accurate timestamps.
Falls back to local system time if NTP is unavailable.
"""
import ntplib
from datetime import datetime

# Default NTP servers to try (in order)
NTP_SERVERS = [
    "pool.ntp.org",
    "time.google.com",
    "time.windows.com",
]

_ntp_offset = None  # Cached offset between local clock and NTP


def sync_ntp():
    """Query NTP server and cache the time offset."""
    global _ntp_offset
    client = ntplib.NTPClient()

    for server in NTP_SERVERS:
        try:
            response = client.request(server, timeout=3)
            _ntp_offset = response.offset
            print(f"[NTP] Synced with {server} (offset: {_ntp_offset:.4f}s)")
            return True
        except Exception:
            continue

    print("[NTP] Failed to sync with any NTP server. Using local time.")
    _ntp_offset = 0.0
    return False


def get_ntp_time():
    """Get current NTP-synced time as a formatted string."""
    global _ntp_offset
    if _ntp_offset is None:
        sync_ntp()

    import time
    ntp_timestamp = time.time() + (_ntp_offset or 0.0)
    return datetime.fromtimestamp(ntp_timestamp).strftime("%Y-%m-%d %H:%M:%S")


def get_ntp_timestamp():
    """Get current NTP-synced time as a float timestamp."""
    global _ntp_offset
    if _ntp_offset is None:
        sync_ntp()

    import time
    return time.time() + (_ntp_offset or 0.0)
