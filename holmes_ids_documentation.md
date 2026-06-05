# HOLMES IDS — Complete Technical Documentation

> **Hybrid Online Learning Model for Enhanced Security**
> Capital University — Faculty of Computers and Artificial Intelligence
> Intrusion Detection System — Graduation Project

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [File-by-File Breakdown](#4-file-by-file-breakdown)
5. [Data Processing Pipeline](#5-data-processing-pipeline)
6. [Machine Learning System](#6-machine-learning-system)
7. [Signature-Based Detection](#7-signature-based-detection)
8. [Database Design (SQLite)](#8-database-design-sqlite)
9. [Web Interface](#9-web-interface)
10. [Live Capture System](#10-live-capture-system)
11. [Explainability (SHAP / LIME)](#11-explainability-shap--lime)
12. [TLS Decryption](#12-tls-decryption)
13. [Continual Learning](#13-continual-learning)
14. [Error Handling & Logging](#14-error-handling--logging)
15. [Performance & Scalability](#15-performance--scalability)
16. [Security Considerations](#16-security-considerations)
17. [Known Issues & Bugs](#17-known-issues--bugs)
18. [How to Run the Project](#18-how-to-run-the-project)
19. [Evaluation & Testing](#19-evaluation--testing)
20. [Future Improvements](#20-future-improvements)

---

## 1. Project Overview

### 1.1 Purpose

HOLMES IDS is a **hybrid network intrusion detection system** that combines two complementary detection methodologies:

1. **Signature-Based Detection** — Pattern matching against a rule database (Snort-like syntax)
2. **Anomaly-Based Detection** — Machine learning classification using a stacking ensemble + isolation forest

The system is designed for **real-time network monitoring** via live packet capture, **offline analysis** via PCAP/CSV uploads, and **continuous improvement** via a human-in-the-loop continual learning pipeline.

### 1.2 Problem Statement

Traditional IDS systems rely solely on signature databases and cannot detect novel (zero-day) attacks. Pure ML-based systems suffer from high false-positive rates and lack interpretability. HOLMES addresses both gaps by:

- Using **signature detection** for known attack patterns (fast, deterministic)
- Using **anomaly detection** for unknown/novel attacks (ML-based classification + outlier scoring)
- Providing **SHAP/LIME explanations** so SOC analysts can understand *why* an alert was raised
- Supporting **continual learning** so the ML models improve over time with human feedback

### 1.3 Key Features

| Feature | Description |
|---|---|
| Hybrid Detection | Signature + Anomaly running simultaneously on live traffic |
| Live Capture | Real-time packet sniffing with Scapy on selectable network interfaces |
| PCAP Upload | Offline signature analysis of PCAP files |
| CSV Upload | Offline anomaly analysis of pre-extracted flow features |
| TLS Decryption | Decrypt HTTPS traffic via SSLKEYLOGFILE + tshark |
| TLS Metadata | Extract SNI, JA3 fingerprints without decryption keys |
| SHAP/LIME Explainability | Per-alert feature importance explanations with charts |
| Continual Learning | Store live features → human labeling → model retraining with evaluation gate |
| Analytics Query Builder | GUI-based query builder with detection patterns (brute-force, port scan, DoS) |
| RBAC | Four roles: Admin, Signature Analyst, Anomaly Analyst, Live Operator |
| React SPA Frontend | Modern React 19 + Vite frontend with sortable tables |
| NTP Synchronization | Accurate timestamps via NTP server sync |

### 1.4 High-Level Workflow

```
Network Traffic / PCAP File / CSV File
        │
        ▼
┌──────────────────────────────┐
│   Packet Parsing (Scapy)     │
│   packet.py → Packet class   │
└───────────┬──────────────────┘
            │
    ┌───────┴────────┐
    ▼                ▼
┌──────────┐  ┌─────────────────┐
│Signature │  │ Flow Extraction │
│ Matching │  │ flow.py → Flow  │
│ rule.py  │  │ (5-tuple group) │
└────┬─────┘  └───────┬─────────┘
     │                │
     │                ▼
     │        ┌───────────────────┐
     │        │ Feature Engineering│
     │        │ 20 flow features   │
     │        └───────┬───────────┘
     │                │
     │                ▼
     │        ┌───────────────────┐
     │        │  ML Inference      │
     │        │  IsolationForest → │
     │        │  StackingClassifier│
     │        └───────┬───────────┘
     │                │
     ▼                ▼
┌──────────────────────────┐
│  Alerts + Logs → SQLite  │
│  alert_features → DB     │
│  training_data → DB      │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  React SPA Dashboard     │
│  (Flask JSON API backend)│
└──────────────────────────┘
```

---

## 2. System Architecture

### 2.1 Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                        HOLMES IDS                                │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐  │
│  │  React SPA   │──▶│  Flask API   │──▶│  SQLite Database     │  │
│  │  (Vite :5174)│   │  (UI.py:8000)│   │  (DB/IDS.db)         │  │
│  │              │   │              │   │                      │  │
│  │  - Login     │   │  api_auth.py │   │  Tables:             │  │
│  │  - Dashboard │   │  api_routes  │   │  - alerts            │  │
│  │  - Upload    │   │              │   │  - logs              │  │
│  │  - Live      │   │  Blueprints: │   │  - rules             │  │
│  │  - Admin     │   │  /api/auth/* │   │  - users             │  │
│  │  - Explain   │   │  /api/*      │   │  - alert_features    │  │
│  │  - Retrain   │   │              │   │  - training_data     │  │
│  │  - Analytics │   │              │   │  - retrain_jobs      │  │
│  └─────────────┘   └──────┬───────┘   └──────────────────────┘  │
│                           │                                      │
│              ┌────────────┴────────────┐                         │
│              │   Core Detection Engine │                         │
│              │                         │                         │
│    ┌─────────┴──┐    ┌────────────┐    │                         │
│    │ Signature  │    │  Anomaly   │    │                         │
│    │ IDS Engine │    │  IDS Engine│    │                         │
│    │            │    │            │    │                         │
│    │ Rule.py    │    │ AnomalyIDS │    │                         │
│    │ match_rule │    │ Flow.py    │    │                         │
│    │ SignatureID│    │ Packet.py  │    │                         │
│    └────────────┘    └────────────┘    │                         │
│              │                         │                         │
│    ┌─────────┴──────────────────┐      │                         │
│    │    LiveCapture             │      │                         │
│    │    (3 daemon threads)      │      │                         │
│    │    - _capture_loop         │      │                         │
│    │    - _flow_processing_loop │      │                         │
│    │    - _batch_writer_loop    │      │                         │
│    └────────────────────────────┘      │                         │
│                                        │                         │
│    ┌───────────────────────────────┐   │                         │
│    │  Supporting Subsystems        │   │                         │
│    │  - explainability.py (SHAP)   │   │                         │
│    │  - continual_learning.py      │   │                         │
│    │  - tls_decrypt.py             │   │                         │
│    │  - analytics.py               │   │                         │
│    │  - ntp_time.py                │   │                         │
│    └───────────────────────────────┘   │                         │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Threading / Concurrency Model

The system uses **multiple threads** for concurrent operations:

| Thread | Owner | Purpose |
|---|---|---|
| Main Thread | Flask (Werkzeug) | HTTP request handling (threaded=True) |
| `_capture_loop` | LiveCapture | Scapy `sniff()` with 2s timeout loop |
| `_flow_processing_loop` | LiveCapture | Drains packet buffer every 10s, runs anomaly detection |
| `_batch_writer_loop` | LiveCapture | Writes training data in batches of 50 to SQLite |
| Retrain Thread | UI.py | Background model retraining (daemon) |
| ThreadPoolExecutor | SignatureIDS | Parallel packet processing (5 workers) |
| ThreadPoolExecutor | AnomalyIDS | Parallel flow processing (10 workers) |

**Thread safety mechanisms:**
- `Packet._lock` — protects global src/dst IP counters
- `LiveCapture._lock` — protects `_running` state
- `LiveCapture._stats_lock` — protects packet/alert counters
- `LiveCapture._buffer_lock` — protects the raw packet buffer
- `_retrain_lock` (module-level) — prevents concurrent retraining
- SQLite WAL mode + `check_same_thread=False` + 10s timeout

### 2.3 Data Flow

**Live Capture path:**
```
Scapy sniff() → raw_pkt
  → _process_packet():
      → Packet(raw_pkt) → signature check → if match → Log + Alert → DB
      → buffer raw_pkt
  → _flow_processing_loop() (every 10s):
      → drain buffer → Packet objects → Flow.group_into_flows()
      → for each flow: compute_features() → scale → IsoForest + Classifier
      → if attack: Log + Alert + alert_features → DB
      → always: enqueue features for training_data
  → _batch_writer_loop():
      → dequeue batches of 50 → training_data → DB
```

**PCAP Upload path:**
```
POST /api/uploads/pcap → save file → rdpcap() → SignatureIDS.predict_from_pcap()
  → ThreadPoolExecutor: for each packet → Packet() → rule matching → dict alerts
  → Optional TLS: tshark decryption or metadata extraction
  → Return JSON: {alerts, tls_results, tls_metadata, messages}
```

**CSV Upload path:**
```
POST /api/uploads/csv → pd.read_csv() → AnomalyIDS.predict_from_csv()
  → for each row: scale → IsoForest score → if anomaly: "Unknown Attack"
  → else: Classifier predict → label_encoder.inverse_transform()
  → Return JSON: {predictions, stats}
```

---

## 3. Technology Stack

### 3.1 Core Languages
| Language | Usage |
|---|---|
| Python 3.x | Backend, ML, packet processing |
| JavaScript (ES2022+) | React SPA frontend |
| SQL | SQLite queries |
| CSS | Styling (Bootstrap 5.3) |

### 3.2 Backend Frameworks & Libraries

| Library | Version | Purpose | Why Chosen |
|---|---|---|---|
| Flask | 3.1.0 | Web framework | Lightweight, Python-native, easy REST API |
| Flask-Login | — | Session management | Built-in cookie-session auth |
| Werkzeug | 3.1.3 | WSGI utilities, password hashing | Flask dependency, `generate_password_hash` |
| Scapy | 2.6.1 | Packet parsing + live capture | Pure Python, no external deps, full packet access |
| scikit-learn | 1.6.1 | ML models (StackingClassifier, IsolationForest) | Industry standard, serializable |
| pandas | 2.2.3 | DataFrame operations | Feature engineering, CSV handling |
| numpy | 2.1.3 | Numerical operations | Array math in features |
| joblib | 1.4.2 | Model serialization | Efficient `.joblib` saving for sklearn |
| SHAP | — | TreeExplainer / KernelExplainer | Gold standard for ML interpretability |
| LIME | — | Local interpretable explanations | Complementary to SHAP, model-agnostic |
| matplotlib | 3.9.2 | Chart generation (base64 PNG) | Explanation bar charts |
| ntplib | — | NTP time synchronization | Accurate alert timestamps |
| imbalanced-learn | — | SMOTE oversampling | Class balancing during retraining |
| SQLite3 | (stdlib) | Database | Zero-config, file-based, sufficient for single-node |

### 3.3 Frontend Stack

| Library | Version | Purpose |
|---|---|---|
| React | 19.1.0 | SPA framework |
| React Router DOM | 7.13.1 | Client-side routing |
| Vite | 7.3.1 | Build tool + dev server |
| Bootstrap | 5.3.3 | CSS framework (dark theme) |
| Font Awesome | 6.5.0 | Icons |
| Chart.js | 4.4.7 | Charts (analytics page) |

### 3.4 External Tools

| Tool | Purpose | Required? |
|---|---|---|
| tshark (Wireshark CLI) | TLS decryption + metadata extraction | Optional |
| Npcap / WinPcap | Packet capture driver (Windows) | Required for live capture |

---

## 4. File-by-File Breakdown

### 4.1 Core Application Files

#### `UI.py` (766 lines) — **Main Application Entry Point**
- Creates Flask app with secret key
- Initializes Flask-Login with `load_user` callback
- Loads all ML model components into `app_state` at startup
- Registers API blueprints (`api_auth`, `api_routes`)
- Defines all legacy Jinja2 routes (still present alongside JSON API)
- Startup: syncs NTP → creates DB tables → creates default admin → loads rules
- Runs on `port=8000`, `threaded=True`, `debug=False`

#### `app_state.py` (55 lines) — **Shared Global State**
- Pure declarations — no I/O at import time (prevents circular imports)
- Holds: `model`, `iso_forest`, `scaler`, `label_encoder`, `feature_order`
- Holds: `rules[]`, `live_capture_instance`
- Config: `DB_PATH`, `UPLOAD_FOLDER`, allowed extensions
- Helper: `_validate_file()`, `get_interfaces()`

#### `api_auth.py` (112 lines) — **Authentication API Blueprint**
- Prefix: `/api/auth`
- Endpoints: `/csrf` (GET), `/me` (GET), `/login` (POST), `/logout` (POST)
- CSRF protection: session-stored token checked via `X-CSRFToken` header
- Login sets session cookie + generates new CSRF token
- Maps backend route names to SPA paths for redirect after login

#### `api_routes.py` (~590 lines) — **All Feature API Endpoints**
- Prefix: `/api`
- Serializer helpers: `_alert_to_dict()`, `_log_to_dict()`, `_rule_to_dict()`, `_user_to_dict()`
- All serializers handle both dict and object inputs safely
- Endpoints grouped: signature, anomaly, CSV, PCAP, rules, live, admin, explain, retrain, analytics

#### `auth.py` (163 lines) — **Authentication & RBAC Core**
- `ROLES` dict: admin (full access), signature_analyst, anomaly_analyst, live_operator
- `User` class: extends `UserMixin`, methods: `get_by_id`, `get_by_username`, `get_all`, `create`, `delete`, `update_role`, `ensure_default_admin`
- `role_required(*roles)` decorator: checks `current_user.role`, redirects unauthorized users to their default page
- Password hashing: `werkzeug.security.generate_password_hash` / `check_password_hash`

### 4.2 Detection Engine Files

#### `packet.py` (279 lines) — **Scapy Packet Wrapper**
- Wraps a raw Scapy packet into a normalized `Packet` object
- Extracts: `protocol` (tcp/udp/icmp/arp/ip), `src_ip`, `dst_ip`, `src_port`, `dst_port`
- Extracts: `flags` (TCP: S/A/F/P/R/U/E/C; IP: DF/MF), `data_size`, `payload` (Raw layer decoded)
- Extracts: `time` (float epoch), `time_formatted` (YYYY-MM-DD HH:MM:SS)
- Methods: `get_header_length()`, `get_window_size()`, `get_payload_length()`, `get_itype()`
- **Class-level counters**: `src_ip_count` / `dst_ip_count` (thread-safe) — used by threshold rules

#### `flow.py` (108 lines) — **Flow Extraction & Feature Engineering**
- Groups `Packet` objects into flows using **5-tuple key**: `(src_ip, dst_ip, src_port, dst_port, protocol)`
- Bidirectional: if `reverse_key` exists, packets are appended to the existing flow
- `compute_features()` — static method that computes **20 features** per flow (see Section 5)

#### `rule.py` (166 lines) — **Signature Rule Engine**
- `Rule` class: constructed from dict with `action`, `protocol`, `src_ip/dst_ip`, `src_port/dst_port`, `options`
- `matches()` — header matching (5-tuple, supports "any" wildcards)
- `match_rule()` — full rule matching including options: `content`, `pcre`, `flags`, `dsize`, `threshold`, `itype`
- `get_rules_from_db()` — loads rules as dicts from SQLite (options stored as JSON)

#### `signature_IDS.py` (118 lines) — **Signature Detection Engine**
- Two modes: `detect()` (live — writes to DB) and `predict_from_pcap()` (upload — returns dicts)
- Uses `ThreadPoolExecutor` with configurable `max_workers` (default 5)
- `detect()`: each packet processed in its own thread, creates own DB connection
- `predict_from_pcap()`: returns list of dicts `{time, src_ip, dst_ip, message, layer, method}`

#### `anomaly_IDS.py` (148 lines) — **Anomaly Detection Engine**
- Two modes: `detect()` (flow-based with DB writes) and `predict_from_csv()` (batch)
- `process_flow()`: extracts features → scales → IsoForest score check → if anomaly score < threshold → "Unknown Attack"; else → classifier predict
- Stores alert features in `alert_features` table for SHAP/LIME
- Confidence: `predict_proba().max()` for classifier, `abs(score)` for isolation forest

#### `live_capture.py` (351 lines) — **Real-Time Capture Engine**
- Three daemon threads: capture loop, flow processing, batch writer
- `FLOW_WINDOW = 10` seconds — how often buffered packets are grouped into flows
- `BATCH_SIZE = 50` — training data DB write batch size
- Signature detection: per-packet (in `_process_packet`)
- Anomaly detection: per-flow-batch (in `_process_flow_buffer`)
- `get_status()` — returns running state, counters, interface info, pending features queue size

#### `match_rule.py` (124 lines) — **Standalone Rule Matching Function**
- Duplicate of `Rule.match_rule()` as a standalone function (legacy)

#### `RuleProcessor.py` (174 lines) — **Rule File Parser & DB Loader**
- `extract_rules()` — reads Snort-format rule files (handles multi-line rules)
- `parse_rule()` — splits header (action, protocol, IPs, ports, direction) and options (content, pcre, flags, etc.)
- `load_rules_to_db()` — inserts parsed rules into SQLite with options as JSON string

### 4.3 Supporting Subsystem Files

#### `explainability.py` (484 lines) — **SHAP/LIME Explanations**
- `FEATURE_GLOSSARY` — human-readable names, descriptions, units for all 20 features
- `explain_shap()` — uses TreeExplainer on final_estimator, maps stacked meta-features back to original features; falls back to KernelExplainer
- `explain_lime()` — uses LimeTabularExplainer with discretize_continuous
- `_generate_shap_chart()` — horizontal bar chart, base64-encoded PNG (top 15 features)
- `store_alert_features()` / `get_alert_features()` — DB CRUD for alert_features table

#### `continual_learning.py` (498 lines) — **Model Retraining Pipeline**
- `store_flow_features()` / `store_batch_features()` — stores flow features with feature versioning (MD5 hash)
- `get_training_stats()` — counts total/labeled/unlabeled, class distributions
- `get_training_samples()` — paginated + filtered sample listing for admin review
- `retrain_models()` — full pipeline: load original CSV + human-labeled DB samples → combine → split → SMOTE → retrain StackingClassifier + IsolationForest → evaluate → promote if F1 ≥ 0.95 AND FPR ≤ 0.05
- `rollback_models()` — restore previous model from rollback directory
- Promotion thresholds: `MIN_F1_THRESHOLD = 0.95`, `MAX_FPR_THRESHOLD = 0.05`, `MIN_SAMPLES_PER_CLASS = 10`

#### `tls_decrypt.py` (261 lines) — **TLS Traffic Analysis**
- `check_tshark()` — detects tshark installation (PATH + common Windows locations)
- `decrypt_pcap()` — runs tshark with `-o tls.keylog_file` to extract HTTP/HTTP2 fields as JSON
- `extract_tls_metadata()` — extracts TLS handshake metadata (SNI, JA3, JA3S, TLS version) without keys

#### `analytics.py` (504 lines) — **Query Builder Engine**
- Parses structured JSON queries from the frontend
- `FIELD_MAP` — maps user-facing names to DB columns (whitelisted)
- Supports: filters (eq, neq, contains, in, between), time ranges (relative/absolute), grouping, time bucketing
- Detection patterns: brute_force, port_scan, dos_spike, credential_stuffing, beaconing
- **Security**: never exposes raw SQL; all queries parameterized

#### `alert_analyzer.py` (28 lines) — **Alert Statistics**
- `get_top_src_ip()` / `get_top_dst_ip()` — finds most frequent IPs across alerts

#### `ntp_time.py` (56 lines) — **NTP Time Synchronization**
- Queries NTP servers: pool.ntp.org, time.google.com, time.windows.com
- Caches time offset; `get_ntp_time()` returns corrected formatted timestamp

#### `alert.py` (57 lines) — **Alert Data Model**
- Constructor: `time`, `src_ip`, `dst_ip`, `message`, `attack`, `method`
- `add_to_alert_table()` — INSERT into alerts, returns `lastrowid`
- `get_alerts_from_db()` — loads all alerts, sets `.id` from row[0]

#### `log.py` (50 lines) — **Log Data Model**
- Constructor: `time`, `action`, `src_ip`, `dst_ip`, `message`, `attack`, `method`
- `add_to_log_table()` — INSERT into logs
- `get_logs_from_db()` — loads all logs (no `.id` attribute)

#### `evaluate_anomaly.py` (225 lines) — **Model Evaluation Script**
- Part 1: Classifier accuracy on CIC-IDS-2017 (accuracy, F1, precision, recall, confusion matrix)
- Part 2: Isolation Forest on simulated unknown attacks
- Part 3: Full pipeline (IsoForest + Classifier) combined evaluation

---

## 5. Data Processing Pipeline

### 5.1 Packet Parsing

Raw Scapy packets are wrapped into `Packet` objects that normalize:
- Protocol detection: TCP → "tcp", UDP → "udp", ARP → "arp", ICMP → "icmp", IP → "ip"
- IP extraction: from IP layer (or ARP layer for ARP frames)
- Port extraction: from TCP/UDP layers
- Flag extraction: TCP flags as character string (e.g., "SA" for SYN-ACK)
- Payload extraction: Raw layer decoded as UTF-8 (or hex fallback)

### 5.2 Flow Construction

Flows are grouped by **5-tuple**: `(src_ip, dst_ip, src_port, dst_port, protocol)`.

**Bidirectional handling**: if the reverse 5-tuple already exists in the flow dictionary, the packet is appended to the existing flow rather than creating a new one.

**No timeout-based splitting** — flows are defined by the packet buffer window (10 seconds in live capture, or all packets in PCAP upload).

### 5.3 Feature Engineering — The 20 Features

Extracted by `Flow.compute_features()` in the exact order required by the ML model:

| # | Feature Name | Computation | Unit |
|---|---|---|---|
| 1 | FwdPacketLengthMean | Mean of forward packet sizes | bytes |
| 2 | FwdPacketLengthMax | Max forward packet size | bytes |
| 3 | FlowIATMax | Max inter-arrival time (fwd + bwd combined) | seconds |
| 4 | SubflowBwdBytes | Total backward bytes | bytes |
| 5 | Init_Win_bytes_backward | First backward packet's TCP window size | bytes |
| 6 | TotalLengthofBwdPackets | Sum of all backward packet sizes | bytes |
| 7 | FlowPackets/s | total_packets / flow_duration | pkt/s |
| 8 | TotalLengthofFwdPackets | Sum of all forward packet sizes | bytes |
| 9 | BwdPackets/s | bwd_packet_count / flow_duration | pkt/s |
| 10 | AveragePacketSize | Mean of all packet sizes | bytes |
| 11 | FlowDuration | flow_end - flow_start (min 1e-6) | seconds |
| 12 | BwdPacketLengthMean | Mean of backward packet sizes | bytes |
| 13 | SubflowFwdBytes | Total forward bytes | bytes |
| 14 | AvgBwdSegmentSize | Mean backward payload length | bytes |
| 15 | FwdPacketLengthStd | Std dev of forward packet sizes | bytes |
| 16 | AvgFwdSegmentSize | Mean forward payload length | bytes |
| 17 | DestinationPort | Destination port (int) | port |
| 18 | BwdHeaderLength | Sum of backward header lengths | bytes |
| 19 | PacketLengthMean | Mean of all packet sizes (duplicate of #10) | bytes |
| 20 | BwdPacketLengthStd | Std dev of backward packet sizes | bytes |

**Direction determination**: Forward = same src_ip as first packet; Backward = opposite.

### 5.4 Feature Preprocessing

1. **Scaling**: MinMaxScaler (`Models/Scaler/scaler_minmax.save`) — fitted on training data
2. **Feature order**: Strict column ordering from `Models/Features_Order/features_order.pkl`
3. **Label encoding**: `Models/Label Encoder/lb_encoder.pkl` — maps attack labels to integers

---

## 6. Machine Learning System

### 6.1 Models Used

#### Primary Classifier: StackingClassifier
- File: `Models/Models/tst1_stk_classifier.joblib` (47 MB)
- Architecture:
  - **Base estimators**: Decision Tree, Random Forest, Logistic Regression, KNN
  - **Final estimator**: Random Forest (meta-learner)
  - Each base estimator predicts class probabilities; these are stacked as features for the final estimator

#### Outlier Detector: Isolation Forest
- File: `Models/Models/isolation_forest.joblib` (937 KB)
- Purpose: Detect **unknown/novel attacks** that the classifier wasn't trained on
- Decision threshold: `-0.000001` (very close to zero — conservative)
- If `decision_function(X) < threshold` → classified as "Unknown Attack"

#### Also Present (unused in production):
- `Models/Models/dnn_ids_model.h5` (184 KB) — Keras DNN model (not loaded by UI.py)

### 6.2 Training Details

- **Dataset**: CIC-IDS-2017 (cleaned version)
  - File: `Models/Dt/tst2_Cleaned_CIC_IDS2017_full_week.csv` (33.8 MB)
  - Contains labeled network flow features from a full week of simulated traffic
  - Labels include: BENIGN, DDoS, PortScan, Bot, Infiltration, Web Attack, SSH-Patator, FTP-Patator, etc.

- **Training notebook**: `Models/model.ipynb` (2.1 MB) — Jupyter notebook with full training pipeline

- **Feature selection**: 20 features selected (likely via importance ranking or correlation analysis)

### 6.3 Inference Pipeline

```python
# 1. Extract raw features (20 values)
raw_features = Flow.compute_features(flow_packets)

# 2. Create DataFrame with correct column order
df = pd.DataFrame([raw_features], columns=feature_order)

# 3. Scale features
df_scaled = scaler.transform(df)  # MinMaxScaler

# 4. Isolation Forest gate
score = iso_forest.decision_function(df_scaled)[0]
if score < -0.000001:
    predicted = "Unknown Attack"
    confidence = abs(score)
else:
    # 5. Stacking Classifier prediction
    pred = model.predict(df_scaled)[0]
    predicted = label_encoder.inverse_transform([pred])[0]
    confidence = model.predict_proba(df_scaled)[0].max()

# 6. If not BENIGN → create alert
if predicted != "BENIGN":
    # → Alert + Log + alert_features → DB
```

### 6.4 Model Files Summary

| File | Content | Size |
|---|---|---|
| `tst1_stk_classifier.joblib` | StackingClassifier (DT+RF+LR+KNN → RF) | 47 MB |
| `isolation_forest.joblib` | IsolationForest outlier detector | 937 KB |
| `scaler_minmax.save` | MinMaxScaler fitted on training data | 2.2 KB |
| `lb_encoder.pkl` | LabelEncoder (attack label ↔ integer) | 650 B |
| `features_order.pkl` | List of 20 feature names in order | 411 B |

### 6.5 Limitations

1. **Dataset bias**: CIC-IDS-2017 is synthetic — real-world traffic distributions may differ significantly
2. **Feature drift**: Network patterns change over time; static models degrade
3. **Unknown attacks**: Only detectable via IsolationForest outlier score; classifier may misclassify novel attacks
4. **Model size**: 47 MB classifier — large memory footprint in production
5. **Inference speed**: StackingClassifier requires predictions from 4 base models → slow for high-throughput

---

## 7. Signature-Based Detection

### 7.1 Rule Structure (Snort-like)

```
action protocol src_ip src_port direction dst_ip dst_port (options)
```

Example stored in DB (options as JSON):
```json
{
  "action": "alert", "protocol": "tcp", "src_ip": "any", "src_port": "any",
  "direction": "->", "dst_ip": "any", "dst_port": "80",
  "options": {"msg": "HTTP GET request", "content": "GET", "attack": "Web Attack"}
}
```

### 7.2 Matching Logic (in `Rule.match_rule()`)

1. **Header match** (`matches()`): protocol, src_ip, dst_ip, src_port, dst_port — all support `"any"` wildcard
2. **Content match**: exact string search in payload; `!` prefix = negation
3. **PCRE match**: regex pattern in payload; supports `(?i)` case-insensitive flag
4. **Flags match**: exact TCP flag string comparison (e.g., "S" for SYN)
5. **Dsize match**: packet size ≥ threshold
6. **Threshold match**: IP counter-based (track_by_src / track_by_dst) — prevents alert flooding
7. **ICMP type match**: exact ICMP type comparison

### 7.3 Rule Storage

Rules are stored in the `rules` SQLite table with options serialized as JSON. Loaded at startup via `Rule.get_rules_from_db()` which returns list of dicts. Rules loaded from text files via `RuleProcessor.load_rules_to_db()`.

---

## 8. Database Design (SQLite)

### 8.1 Full Schema

```sql
-- Core detection tables
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT,
    protocol TEXT,
    src_ip TEXT,
    src_port TEXT,
    direction TEXT,
    dst_ip TEXT,
    dst_port TEXT,
    options TEXT  -- JSON-encoded rule options
);

CREATE TABLE logs (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    event_type TEXT,    -- "alert"
    src_ip TEXT,
    dst_ip TEXT,
    message TEXT,
    attack TEXT,
    method TEXT          -- "signature" | "anomaly"
);

CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME,
    src_ip TEXT,
    dst_ip TEXT,
    message TEXT,
    attack TEXT,
    method TEXT          -- "signature" | "anomaly"
);

-- Authentication
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'live_operator',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Explainability
CREATE TABLE alert_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER NOT NULL,
    features_json TEXT NOT NULL,    -- JSON dict of 20 features
    predicted_label TEXT,
    confidence REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (alert_id) REFERENCES alerts(id)
);

-- Continual Learning
CREATE TABLE training_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    features_json TEXT NOT NULL,    -- JSON dict of 20 features
    predicted_label TEXT,
    confidence REAL,
    human_label TEXT,               -- NULL until admin labels
    feature_version TEXT,           -- MD5 hash of feature order
    source TEXT DEFAULT 'live_capture',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE retrain_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending/running/completed/failed
    started_by TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    old_accuracy REAL,
    new_accuracy REAL,
    old_f1 REAL,
    new_f1 REAL,
    promoted INTEGER DEFAULT 0,
    samples_used INTEGER DEFAULT 0,
    error_message TEXT
);
```

### 8.2 SQLite Configuration

- **Connection**: `sqlite3.connect(db_name, check_same_thread=False, timeout=10)`
- **Row factory**: `sqlite3.Row` (dict-like access)
- **Journal mode**: `WAL` (Write-Ahead Logging) — allows concurrent reads during writes
- **No explicit indexing** beyond primary keys

### 8.3 Threading Concerns

SQLite with WAL mode supports concurrent reads, but writes are serialized. The system creates **new connections per operation** (no connection pooling). The `check_same_thread=False` flag is required because background threads (LiveCapture, retraining) need DB access. Potential risk: "database is locked" under heavy concurrent write load.

---

## 9. Web Interface

### 9.1 Architecture

The system runs a **dual architecture**:
1. **Legacy Flask/Jinja2 routes** (still in UI.py) — server-rendered HTML
2. **React SPA** (frontend/) with **Flask JSON API** (api_auth.py, api_routes.py) — modern SPA

The React SPA communicates with Flask via `/api/*` endpoints. In development, Vite proxies `/api/*` to Flask on port 8000.

### 9.2 API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/auth/csrf` | No | Get CSRF token |
| GET | `/api/auth/me` | No | Check current session |
| POST | `/api/auth/login` | No | Login (JSON body) |
| POST | `/api/auth/logout` | Yes+CSRF | Logout |
| GET | `/api/signature/dashboard` | admin, sig_analyst | Signature alerts + rules + stats |
| GET | `/api/anomaly/dashboard` | admin, anomaly_analyst | Anomaly alerts + stats |
| POST | `/api/uploads/csv` | admin, anomaly_analyst | Upload CSV for anomaly detection |
| POST | `/api/uploads/pcap` | admin, sig_analyst | Upload PCAP for signature detection |
| GET | `/api/rules` | admin, sig_analyst | List all rules |
| GET | `/api/live/status` | all roles | Live capture status + alerts |
| POST | `/api/live/start` | admin, live_operator | Start capture |
| POST | `/api/live/stop` | admin, live_operator | Stop capture |
| POST | `/api/live/clear` | admin, live_operator | Clear all alerts |
| POST | `/api/live/delete` | admin, live_operator | Delete selected alerts |
| GET | `/api/admin/users` | admin | List users + roles |
| POST | `/api/admin/users` | admin | Create user |
| DELETE | `/api/admin/users/:id` | admin | Delete user |
| PUT | `/api/admin/users/:id/role` | admin | Update user role |
| GET | `/api/explain/:alert_id` | admin, anomaly_analyst | SHAP+LIME explanation |
| GET | `/api/retrain/dashboard` | admin | Training stats + samples + history |
| POST | `/api/retrain/start` | admin | Start retraining |
| POST | `/api/retrain/label` | admin | Label training sample |
| POST | `/api/analytics/query` | admin, sig/anomaly analyst | Execute analytics query |

### 9.3 React SPA Pages

| Route | Component | Role Access |
|---|---|---|
| `/login` | LoginPage | Public |
| `/` | SignaturePage | admin, signature_analyst |
| `/anomaly` | AnomalyPage | admin, anomaly_analyst |
| `/csv` | CsvUploadPage | admin, anomaly_analyst |
| `/upload_pcap` | PcapUploadPage | admin, signature_analyst |
| `/rules` | RulesPage | admin, signature_analyst |
| `/live` | LiveCapturePage | all authenticated |
| `/admin` | AdminPage | admin |
| `/explain/:alertId` | ExplainPage | admin, anomaly_analyst |
| `/retrain` | RetrainPage | admin |
| `/analytics` | AnalyticsPage | admin, sig/anomaly analyst |

---

## 10. Live Capture System

### 10.1 Architecture

LiveCapture runs **3 daemon threads**:

1. **Capture loop** (`_capture_loop`): calls `scapy.sniff()` with 2-second timeout in a while loop. Each captured packet calls `_process_packet()` synchronously.

2. **Flow processing loop** (`_flow_processing_loop`): sleeps for `FLOW_WINDOW` (10s), then drains the packet buffer, groups into flows, and runs anomaly detection on each flow.

3. **Batch writer loop** (`_batch_writer_loop`): dequeues items from `_feature_queue` and writes them to the `training_data` table in batches of 50.

### 10.2 Per-Packet Processing

In `_process_packet()`:
- Packet is wrapped in `Packet()` object
- **Signature detection**: instantiates `Rule` objects, runs `match_rule()` — if match, creates `Log` + `Alert` in DB
- Raw scapy packet is buffered for anomaly detection

### 10.3 Per-Flow-Batch Processing

In `_process_flow_buffer()` (called every 10s):
- Drain packet buffer (thread-safe)
- Convert raw packets to `Packet` objects
- Group into flows via `Flow()`
- For each flow: compute features → scale → IsoForest check → Classifier predict
- If attack: `Log` + `Alert` + `alert_features` → DB
- Always: enqueue features for training data

### 10.4 Performance Limitations

- **Single-threaded capture**: `sniff()` runs in one thread — high-throughput networks may lose packets
- **10-second flow window**: short window may split legitimate long flows
- **Rule re-instantiation**: `Rule(r)` is created per-packet for every rule — O(n) per packet
- **No BPF filter**: captures ALL traffic on the interface

---

## 11. Explainability (SHAP / LIME)

### 11.1 SHAP Implementation

- **Primary method**: `TreeExplainer` on the StackingClassifier's `final_estimator_` (RandomForest)
- **Challenge**: SHAP explains the meta-features (stacked predictions), not original features
- **Solution**: `_map_stacked_to_original()` distributes SHAP importance proportionally using base estimators' `feature_importances_` or `coef_`
- **Fallback**: `KernelExplainer` with `nsamples=100` (slower but model-agnostic)

### 11.2 LIME Implementation

- `LimeTabularExplainer` with `discretize_continuous=True`
- Background data: 500 samples from training CSV (scaled)
- Explains `model.predict_proba()` for the predicted class
- Feature contributions mapped back to clean feature names

### 11.3 Output

Both methods produce:
- Sorted feature contributions (name, weight)
- Base64-encoded horizontal bar chart PNG (top 15 features)
- Red = pushes toward attack, Blue = pushes toward benign

---

## 12. TLS Decryption

### 12.1 Method: SSLKEYLOGFILE

- User uploads PCAP + TLS keylog file
- tshark decrypts TLS using `-o tls.keylog_file:path`
- Filters for `http || http2` post-decryption
- Extracts: host, URI, method, content_type, response_code, truncated payload (200 chars)

### 12.2 Fallback: TLS Metadata Extraction

Without keylog file:
- Extracts from `tls.handshake.type == 1 || 2` (ClientHello / ServerHello)
- Fields: SNI (`tls.handshake.extensions_server_name`), JA3, JA3S, TLS version
- **Security value**: JA3 fingerprints can identify malware C2 channels

### 12.3 Limitations

- Requires tshark/Wireshark installed
- 120s timeout for decryption, 60s for metadata
- Cannot decrypt without session keys (no MITM capability)
- JA3 requires Wireshark JA3 plugin

---

## 13. Continual Learning

### 13.1 Data Collection

During live capture, **every flow** (benign and malicious) has its features stored in the `training_data` table via the batch writer. Fields: `features_json`, `predicted_label`, `confidence`, `feature_version`, `source`.

### 13.2 Human Labeling

Admin reviews samples in the Retrain dashboard, applies filters (label, date, labeled/unlabeled), and assigns `human_label` values. Only human-labeled samples are used for retraining.

### 13.3 Retraining Pipeline

1. Load original CIC-IDS-2017 CSV (full training set)
2. Load human-labeled samples from DB (minimum 10 required)
3. Combine datasets
4. 80/20 train/test split (stratified)
5. Scale with existing scaler
6. Apply SMOTE for class balancing (training set only)
7. Evaluate OLD model on test set (baseline)
8. Clone + retrain StackingClassifier and IsolationForest
9. Evaluate NEW model on test set
10. **Promotion gate**: promote only if `new_f1 >= 0.95` AND `FPR <= 0.05`
11. Save rollback copy of old model
12. Promote or save candidate for manual review

### 13.4 Risks

- **Data poisoning**: adversary could generate crafted traffic to corrupt training data
- **Label noise**: human errors in labeling propagate to model
- **Catastrophic forgetting**: mitigated by always including original training data
- **Scaler drift**: scaler is NOT retrained — if new data has different distributions, scaling may be suboptimal

---

## 14. Error Handling & Logging

- All operations wrapped in try/except blocks
- Errors printed to stdout with `[ERROR]`, `[WARN]`, `[CRITICAL]` prefixes
- No structured logging framework (no log files, no log levels)
- Flask flash messages for user-facing errors (legacy routes)
- JSON error responses with appropriate HTTP status codes (API routes)
- Graceful degradation: NTP failure → local time; SMOTE failure → no balancing; tshark missing → no TLS

---

## 15. Performance & Scalability

### 15.1 Bottlenecks

| Component | Bottleneck | Impact |
|---|---|---|
| SQLite | Single-writer, file-based | Concurrent writes may block |
| StackingClassifier | 4 base models + meta-learner | Slow inference per flow |
| Scapy sniff() | Single-threaded Python | Packet loss at >10k PPS |
| Feature extraction | Python-level computation per flow | CPU-bound |
| SHAP KernelExplainer | 100 samples perturbation | Slow explanation generation |
| Model files | 47 MB classifier loaded in memory | High RAM usage |

### 15.2 Scalability Limits

- **Single-node**: no distributed architecture
- **No connection pooling**: new SQLite connection per operation
- **No caching**: rules reloaded from DB on every dashboard request
- **No rate limiting**: API endpoints unprotected from DoS

---

## 16. Security Considerations

1. **PCAP handling**: PCAP files may contain malware traffic — files saved to `uploads/` without sandboxing
2. **TLS keylog files**: contain session secrets — deleted after use (`os.remove`)
3. **Default credentials**: `admin/admin` — must be changed in production
4. **Secret key**: hardcoded fallback; should use environment variable
5. **CSRF protection**: implemented for API mutations; not in legacy routes
6. **SQL injection**: mitigated by parameterized queries and whitelisted field names in analytics
7. **No input sanitization**: uploaded filenames secured via `werkzeug.secure_filename`
8. **Model poisoning**: training data from live capture could be adversarial

---

## 17. Known Issues & Bugs

1. **Rule re-instantiation**: `Rule(r)` created per-packet in live capture — wasteful
2. **Feature #10 and #19 are identical**: `AveragePacketSize` and `PacketLengthMean` compute the same value
3. **Log model has no `id` attribute**: but API serializer uses `getattr` safely
4. **`predict_from_pcap` returns dicts, not Alert objects**: API serializer handles both formats
5. **No flow timeout**: flows defined by buffer window, not by standard flow timeout (e.g., 120s idle)
6. **Scaler not retrained**: continual learning uses the original scaler even with new data
7. **Legacy Jinja2 routes still present**: both JSON API and HTML routes coexist in UI.py
8. **`live_capture.get_status()` was missing**: added in later version, but was being called before it existed

---

## 18. How to Run the Project

### 18.1 Prerequisites

- Python 3.10+
- Node.js 18+
- Npcap (Windows) for live packet capture
- Wireshark/tshark (optional, for TLS features)

### 18.2 Backend Setup

```bash
cd IDS-Grad-Helwan
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt

# Ensure DB and upload directories exist
mkdir -p DB uploads

# Load signature rules (if rules table is empty)
python RuleProcessor.py

# Start the backend
python UI.py
# → Listens on http://127.0.0.1:8000
# → Default login: admin / admin
```

### 18.3 Frontend Setup

```bash
cd frontend
npm install
npm run dev
# → Listens on http://localhost:5174
# → Proxies /api/* to Flask :8000
```

### 18.4 Production Build

```bash
cd frontend
npm run build
# → Output in frontend/dist/
# → Configure Flask to serve dist/ as static files
```

---

## 19. Evaluation & Testing

### 19.1 Model Evaluation

Run `python evaluate_anomaly.py` for:
- **Part 1**: Classifier accuracy, F1, precision, recall, confusion matrix on CIC-IDS-2017
- **Part 2**: Isolation Forest detection rate on `unknown_attacks_simulated.csv`
- **Part 3**: Combined pipeline (IsoForest gate + Classifier) on full dataset

### 19.2 Unit Tests

Located in `tests/`:
- `test_packet.py` — Packet parsing from mock Scapy packets
- `test_flow.py` — Flow grouping and feature extraction
- `test_rule.py` — Rule matching (header, content, pcre, flags, threshold)
- `test_match_rule.py` — Standalone match function tests
- `test_db.py` — Database CRUD operations

Run: `pytest tests/ -v`

### 19.3 Metrics

| Metric | Expected Value |
|---|---|
| Classifier Accuracy | ~99%+ (on CIC-IDS-2017) |
| Weighted F1 Score | ~99%+ |
| Unknown Attack Detection | Depends on threshold tuning |
| Retraining Promotion Gate | F1 ≥ 0.95 AND FPR ≤ 0.05 |

---

## 20. Future Improvements

### Architecture
- Replace SQLite with PostgreSQL for concurrent write support
- Add connection pooling (SQLAlchemy)
- Containerize with Docker for deployment
- Add WebSocket support for real-time alert push
- Implement BPF filters for targeted packet capture

### ML / Detection
- Add deep learning model (DNN already present but unused)
- Implement online/incremental learning instead of full retraining
- Add autoencoder-based anomaly detection
- Retrain scaler alongside model during continual learning
- Add adaptive threshold for Isolation Forest

### Security
- Replace default credentials with mandatory setup wizard
- Add rate limiting to API endpoints
- Implement HTTPS for production
- Add audit logging for all admin actions
- Sandbox PCAP processing in isolated environment

### Frontend
- Add real-time WebSocket alert notifications
- Add dashboard charts (alert trends, attack distribution)
- Add PCAP file replay visualization
- Export alerts to SIEM-compatible formats (CEF, STIX)

---