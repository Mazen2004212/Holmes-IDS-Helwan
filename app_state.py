"""
Shared application state for HOLMES IDS.
Pure declarations only — no imports with side effects, no I/O at import time.
UI.py populates all None placeholders during startup.
"""
import os

# ========== Config (constants, no I/O) ========== #
DB_PATH = "DB/IDS.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_PCAP_EXTENSIONS = {".pcap", ".pcapng"}
ALLOWED_CSV_EXTENSIONS = {".csv"}

# ========== ML Models (populated by UI.py at startup) ========== #
model = None
iso_forest = None
scaler = None
label_encoder = None
feature_order = None

# ========== Mutable Global State (populated by UI.py) ========== #
rules = []
live_capture_instance = None


# ========== Helper Functions ========== #

def _validate_file(file, allowed_extensions):
    """Validate uploaded file has an allowed extension."""
    from werkzeug.utils import secure_filename  # lazy import
    if not file or file.filename == "":
        return None, "Please upload a valid file"
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        return None, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    return filename, None


def get_interfaces():
    """Get list of available network interfaces with friendly names."""
    try:
        from scapy.all import conf  # lazy import — no scapy at module level
    except Exception:
        return []
    ifaces_list = []
    try:
        for iface_id, iface_obj in conf.ifaces.items():
            name = getattr(iface_obj, "name", str(iface_id))
            desc = getattr(iface_obj, "description", "")
            ifaces_list.append({"id": str(iface_id), "name": name, "description": desc})
    except Exception as e:
        print(f"[WARN] Could not enumerate interfaces: {e}")
    return ifaces_list
