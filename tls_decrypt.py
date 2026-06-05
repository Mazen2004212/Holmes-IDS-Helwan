"""
TLS/HTTPS Traffic Decryption for HOLMES IDS.
=============================================
Decrypts TLS traffic from PCAP files using SSLKEYLOGFILE
via tshark, and extracts TLS metadata (SNI, JA3) as fallback.
"""

import json
import os
import shutil
import subprocess
import tempfile


# ========== tshark Detection ========== #

def check_tshark():
    """
    Detect tshark installation.
    Returns (path, None) if found, or (None, instructions) if not.
    """
    # Check PATH first
    tshark_path = shutil.which("tshark")
    if tshark_path:
        return tshark_path, None

    # Common Windows locations
    common_paths = [
        r"C:\Program Files\Wireshark\tshark.exe",
        r"C:\Program Files (x86)\Wireshark\tshark.exe",
    ]
    for path in common_paths:
        if os.path.isfile(path):
            return path, None

    instructions = (
        "tshark (Wireshark CLI) is required for TLS decryption.\n\n"
        "Installation instructions:\n"
        "  Windows: Install Wireshark from https://www.wireshark.org/download.html\n"
        "           Make sure to check 'Install TShark' during setup.\n"
        "           Add Wireshark directory to PATH.\n\n"
        "  Linux:   sudo apt install tshark\n\n"
        "After installation, restart the HOLMES IDS server."
    )
    return None, instructions


# ========== TLS Decryption via SSLKEYLOGFILE ========== #

def decrypt_pcap(pcap_path, keylog_path):
    """
    Decrypt TLS traffic in a PCAP file using an SSLKEYLOGFILE.
    Extracts application-layer HTTP fields via tshark JSON output.

    Returns:
        list of dicts with keys: frame_number, src_ip, dst_ip, src_port,
        dst_port, http_host, http_uri, http_method, http_content_type,
        http_response_code, decrypted_payload_preview
    """
    tshark_path, error = check_tshark()
    if not tshark_path:
        return {"error": error, "results": []}

    if not os.path.isfile(pcap_path):
        return {"error": f"PCAP file not found: {pcap_path}", "results": []}
    if not os.path.isfile(keylog_path):
        return {"error": f"Keylog file not found: {keylog_path}", "results": []}

    try:
        # Use tshark to decrypt and export HTTP fields as JSON
        cmd = [
            tshark_path,
            "-r", pcap_path,
            "-o", f"tls.keylog_file:{keylog_path}",
            "-Y", "http || http2",  # Filter for decrypted HTTP/HTTP2 traffic
            "-T", "json",
            "-e", "frame.number",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "tcp.srcport",
            "-e", "tcp.dstport",
            "-e", "http.host",
            "-e", "http.request.uri",
            "-e", "http.request.method",
            "-e", "http.content_type",
            "-e", "http.response.code",
            "-e", "http.file_data",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0 and not result.stdout:
            return {
                "error": f"tshark error: {result.stderr[:500]}",
                "results": []
            }

        # Parse JSON output
        if not result.stdout.strip():
            return {
                "error": None,
                "results": [],
                "message": "No HTTP traffic found after decryption. "
                           "The PCAP may not contain TLS traffic, or "
                           "the keylog file may not match."
            }

        packets = json.loads(result.stdout)
        decrypted_results = []

        for pkt in packets:
            layers = pkt.get("_source", {}).get("layers", {})

            def get_field(field_name):
                val = layers.get(field_name, [""])
                return val[0] if isinstance(val, list) else val

            # Truncate payload preview for safety (no full payload storage)
            payload = get_field("http.file_data")
            payload_preview = payload[:200] + "..." if len(payload) > 200 else payload

            entry = {
                "frame_number": get_field("frame.number"),
                "src_ip": get_field("ip.src"),
                "dst_ip": get_field("ip.dst"),
                "src_port": get_field("tcp.srcport"),
                "dst_port": get_field("tcp.dstport"),
                "http_host": get_field("http.host"),
                "http_uri": get_field("http.request.uri"),
                "http_method": get_field("http.request.method"),
                "http_content_type": get_field("http.content_type"),
                "http_response_code": get_field("http.response.code"),
                "payload_preview": payload_preview,
            }
            decrypted_results.append(entry)

        return {"error": None, "results": decrypted_results}

    except subprocess.TimeoutExpired:
        return {"error": "tshark timed out (120s limit)", "results": []}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse tshark output: {e}", "results": []}
    except Exception as e:
        return {"error": f"Decryption failed: {e}", "results": []}


# ========== TLS Metadata Extraction (Fallback) ========== #

def extract_tls_metadata(pcap_path):
    """
    Extract TLS metadata from a PCAP without decryption keys.
    Extracts: SNI (Server Name Indication), JA3 fingerprints, cert info.

    This provides useful IDS signals even without decryption:
    - SNI reveals the target hostname
    - JA3/JA3S fingerprints identify client/server TLS implementations
    - Unusual JA3 hashes can indicate malware or C2 channels

    Returns:
        list of dicts with tls_sni, ja3, ja3s, cert_issuer, cert_subject
    """
    tshark_path, error = check_tshark()
    if not tshark_path:
        return {"error": error, "results": []}

    if not os.path.isfile(pcap_path):
        return {"error": f"PCAP file not found: {pcap_path}", "results": []}

    try:
        # Extract TLS handshake metadata
        cmd = [
            tshark_path,
            "-r", pcap_path,
            "-Y", "tls.handshake.type == 1 || tls.handshake.type == 2",  # ClientHello + ServerHello
            "-T", "json",
            "-e", "frame.number",
            "-e", "ip.src",
            "-e", "ip.dst",
            "-e", "tcp.dstport",
            "-e", "tls.handshake.extensions_server_name",  # SNI
            "-e", "tls.handshake.ja3",        # JA3 (if Wireshark plugin)
            "-e", "tls.handshake.ja3s",       # JA3S
            "-e", "tls.handshake.version",    # TLS version
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if not result.stdout.strip():
            # Try alternative: just extract SNI without JA3 fields
            cmd_fallback = [
                tshark_path,
                "-r", pcap_path,
                "-Y", "tls.handshake.extensions_server_name",
                "-T", "fields",
                "-e", "ip.src",
                "-e", "ip.dst",
                "-e", "tcp.dstport",
                "-e", "tls.handshake.extensions_server_name",
            ]
            result_fb = subprocess.run(
                cmd_fallback,
                capture_output=True,
                text=True,
                timeout=60
            )

            metadata = []
            if result_fb.stdout.strip():
                for line in result_fb.stdout.strip().split("\n"):
                    parts = line.split("\t")
                    if len(parts) >= 4:
                        metadata.append({
                            "src_ip": parts[0],
                            "dst_ip": parts[1],
                            "dst_port": parts[2],
                            "tls_sni": parts[3],
                            "ja3": "",
                            "ja3s": "",
                            "tls_version": "",
                        })
            return {"error": None, "results": metadata}

        packets = json.loads(result.stdout)
        metadata = []

        for pkt in packets:
            layers = pkt.get("_source", {}).get("layers", {})

            def get_field(field_name):
                val = layers.get(field_name, [""])
                return val[0] if isinstance(val, list) else val

            entry = {
                "frame_number": get_field("frame.number"),
                "src_ip": get_field("ip.src"),
                "dst_ip": get_field("ip.dst"),
                "dst_port": get_field("tcp.dstport"),
                "tls_sni": get_field("tls.handshake.extensions_server_name"),
                "ja3": get_field("tls.handshake.ja3"),
                "ja3s": get_field("tls.handshake.ja3s"),
                "tls_version": get_field("tls.handshake.version"),
            }
            metadata.append(entry)

        return {"error": None, "results": metadata}

    except subprocess.TimeoutExpired:
        return {"error": "tshark timed out (60s limit)", "results": []}
    except Exception as e:
        return {"error": f"TLS metadata extraction failed: {e}", "results": []}
