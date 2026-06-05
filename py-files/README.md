# 🛡️ HOLMES IDS - Intelligent Intrusion Detection System  
**Graduation Project - Faculty of Computers and Artificial Intelligence, Capital University (2025)**

---

## 📌 Overview

**HOLMES IDS** is an Intrusion Detection System that combines both anomaly-based and signature-based detection techniques to effectively identify and prevent known and unknown cyber threats in real-time network traffic.

It features a modern dark-themed web dashboard, real-time live capture with flow-based anomaly detection, TLS/HTTPS traffic analysis, SHAP/LIME model explainability, and a continual learning pipeline for model improvement over time.

---

## 🚀 Features

### Core Detection
- ✅ **Signature-Based Detection** — Custom rule engine matching packet payloads against known attack patterns (SQLi, XSS, XXE, Command Injection, WannaCry, etc.)
- 🤖 **Anomaly-Based Detection** — Machine learning using Stacking Classifier (RF, DT, KNN, SVM) + Isolation Forest for unknown attack detection
- 📡 **Real-Time Live Capture** — Scapy `sniff()` with selectable network interface, per-packet signature matching, and flow-based anomaly detection every 10 seconds
- ⏱️ **NTP-Synchronized Timestamps** — Accurate alert timing via NTP time synchronization

### Advanced Features
- 🔐 **TLS/HTTPS Traffic Decryption** — Upload PCAP + SSLKEYLOGFILE for full HTTP decryption; TLS metadata extraction (SNI, JA3 fingerprints) without keylog
- 🧠 **SHAP/LIME Explainability** — Per-alert explanations showing which features drove the anomaly detection, with interactive charts and a feature glossary
- 🔄 **Continual Learning** — Store live capture flow features, admin relabeling, full model retraining with SMOTE balancing, evaluation gate (F1 ≥ 0.95, FPR ≤ 5%), model promotion/rollback

### UI & Management
- 🌙 **Dark Mode UI** — Modern dark-themed interface using Bootstrap 5.3
- 🔒 **Authentication & RBAC** — Flask-Login with 4 roles (Admin, Signature Analyst, Anomaly Analyst, Live Operator)
- 👥 **Admin Panel** — User creation, deletion, and role management
- 🔍 **Alert Management** — Search, filter by method/IP/attack/layer, sortable columns, selective delete, and reset
- 📊 **Dashboard** — Real-time alert visualization, logs, top source/target IPs
- 📁 **PCAP Upload** — Analyze captured traffic files with signature detection
- 📂 **CSV Upload** — Batch anomaly prediction on flow feature datasets
- 🏷️ **Retrain Dashboard** — Filter samples by label/source/date, pagination, human relabeling, retraining history

---

## 🛠️ Technologies Used

| Component           | Technology |
|--------------------|------------|
| Frontend           | HTML, Bootstrap 5.3 (Dark Mode), JavaScript |
| Backend            | Python (Flask) |
| Authentication     | Flask-Login + Werkzeug |
| ML Models          | Scikit-learn (Stacking Classifier + Isolation Forest) |
| Explainability     | SHAP, LIME |
| Class Balancing    | imbalanced-learn (SMOTE) |
| Real-time Traffic  | Scapy |
| TLS Decryption     | tshark (Wireshark CLI) |
| Time Sync          | NTPlib |
| Dataset            | CIC-IDS-2017 |
| Database           | SQLite (WAL mode) |
| Testing            | pytest (78 tests) |

---

## 📂 Project Structure

```
HOLMES_IDS/
├── DB/                      # SQLite database
├── Models/                  # Pre-trained ML models, scaler, encoder
│   ├── Models/              # Stacking classifier + Isolation Forest
│   ├── Scaler/              # MinMax scaler
│   ├── Label Encoder/       # Label encoder
│   ├── Features_Order/      # Feature order manifest
│   ├── candidate/           # Candidate models (after retraining)
│   └── rollback/            # Rollback models (before promotion)
├── static/
│   ├── CSS/                 # Dark mode stylesheets
│   ├── JS/                  # Client-side scripts
│   └── IMG/                 # Logo and assets
├── templates/               # Jinja2 HTML templates
│   ├── base.html            # Base layout (dark theme)
│   ├── nav.html             # Navigation bar
│   ├── login.html           # Login page
│   ├── signature.html       # Signature IDS dashboard
│   ├── anomaly.html         # Anomaly IDS dashboard
│   ├── live.html            # Live capture with alert management
│   ├── pcap.html            # PCAP upload + TLS decryption
│   ├── rules.html           # Signature rules viewer
│   ├── admin.html           # User management panel
│   ├── retrain.html         # Continual learning dashboard
│   └── explain.html         # SHAP/LIME explanation view
├── tests/                   # pytest test suite (78 tests)
├── UI.py                    # Main Flask app (entry point)
├── auth.py                  # Authentication & RBAC (4 roles)
├── ntp_time.py              # NTP time synchronization
├── packet.py                # Scapy packet parsing
├── flow.py                  # Flow grouping & feature extraction
├── rule.py                  # Rule class & matching engine
├── match_rule.py            # Standalone rule matcher
├── signature_IDS.py         # Signature-based detection engine
├── anomaly_IDS.py           # Anomaly-based detection (ML)
├── live_capture.py          # Real-time capture + flow anomaly detection
├── tls_decrypt.py           # TLS decryption & metadata extraction
├── explainability.py        # SHAP/LIME alert explanations
├── continual_learning.py    # Model retraining pipeline
├── alert.py                 # Alert model
├── log.py                   # Log model
├── alert_analyzer.py        # Alert statistics
├── RuleProcessor.py         # Rule file parser & DB loader
└── DB.py                    # Database connection & management
```

---

## 🔧 Installation & Running

### Prerequisites
- Python 3.9+
- [Npcap](https://npcap.com/) (Windows) or libpcap (Linux) for live capture
- [Wireshark / tshark](https://www.wireshark.org/) (optional, for TLS decryption)

### Setup

```bash
git clone https://github.com/mohameddahmedd/IDS-Grad-Helwan.git
cd IDS-Grad-Helwan
pip install -r requirements.txt
python UI.py
```

Then open your browser at **http://127.0.0.1:8000/**

**Default login:** `admin` / `admin`

> **Note:** On Linux, live capture may require `sudo`. On Windows, run as Administrator if Npcap requires it.

---

## 🔒 Authentication & Roles

| Role | Access |
|---|---|
| **Admin** | All pages + User management + Retrain dashboard |
| **Signature Analyst** | Signature IDS, PCAP upload, Rules |
| **Anomaly Analyst** | Anomaly IDS, CSV upload, Explainability |
| **Live Operator** | Live Capture + Alert management |

Admins can create, delete, and change roles for users from the **Admin Panel**.

---

## 🌐 Available Routes

| Route | Description | Roles |
|-------|-------------|-------|
| `/login` | Login page | Public |
| `/` | Signature IDS Dashboard | Admin, Signature Analyst |
| `/anomaly` | Anomaly IDS Dashboard | Admin, Anomaly Analyst |
| `/live` | Live Traffic Capture + Alert Management | Admin, Anomaly Analyst, Live Operator |
| `/live/start` | Start live capture | Admin, Live Operator |
| `/live/stop` | Stop live capture | Admin, Live Operator |
| `/live/clear` | Reset all alerts | Admin, Live Operator |
| `/live/delete` | Delete selected alerts | Admin, Live Operator |
| `/csv` | Upload CSV for anomaly prediction | Admin, Anomaly Analyst |
| `/upload_pcap` | Upload PCAP + optional TLS keylog | Admin, Signature Analyst |
| `/rules` | View signature rules | Admin, Signature Analyst |
| `/explain/<id>` | SHAP/LIME explanation for alert | Admin, Anomaly Analyst |
| `/retrain` | Continual learning dashboard | Admin only |
| `/retrain/start` | Trigger model retraining | Admin only |
| `/retrain/label` | Update sample labels | Admin only |
| `/admin` | User management panel | Admin only |

---

## 🔐 TLS/HTTPS Decryption

HOLMES IDS can analyze encrypted TLS/HTTPS traffic in two ways:

1. **Full Decryption** — Upload a PCAP with the corresponding `SSLKEYLOGFILE` to decrypt and inspect HTTP requests within TLS sessions.
2. **Metadata Extraction** — Without a keylog, the system extracts SNI (Server Name Indication) and JA3 fingerprints from TLS handshakes.

To capture TLS keys, set the `SSLKEYLOGFILE` environment variable before browsing:
```bash
# Windows
set SSLKEYLOGFILE=C:\sslkeys.log

# Linux/Mac
export SSLKEYLOGFILE=~/sslkeys.log
```

---

## 🧠 Explainability (SHAP/LIME)

Each anomaly alert has an **Explain** button that generates:
- **SHAP** waterfall chart showing feature contributions
- **LIME** local explanation with feature weights
- **Feature Glossary** explaining what each network feature means

---

## 🔄 Continual Learning

The system supports ongoing model improvement:
1. **Data Collection** — Live capture stores flow features automatically in batches
2. **Admin Relabeling** — Human-verified labels stored separately from model predictions
3. **Filter & Select** — Filter samples by label, source, date range, labeled status
4. **Retraining** — Full model retrain using original CIC-IDS-2017 + human-labeled data, with SMOTE balancing
5. **Evaluation Gate** — Candidate models must pass F1 ≥ 0.95 and FPR ≤ 5% for promotion
6. **Rollback** — Previous model preserved for rollback if needed

---

## 🧪 Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

78 tests covering packet parsing, rule matching, flow extraction, alerting, and database operations.

---

## 📄 License

This project is for academic use. Feel free to fork and build on it, giving credit where it's due.

---

## Contact

- GitHub: [mohameddahmedd](https://github.com/mohameddahmedd)
