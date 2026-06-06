# HOLMES IDS

Hybrid Online Learning Model for Enhanced Security.

HOLMES IDS is a hybrid Intrusion Detection System that combines signature-based detection, anomaly-based machine learning detection, live packet capture, explainability, continual learning, and analytics in one web application.

## Main Features

- Signature-based IDS using custom rules for known attack patterns.
- Anomaly-based IDS using a trained stacking classifier and Isolation Forest.
- Live capture with Scapy, selectable network interface, signature checks, and flow-based anomaly detection.
- CSV upload for batch anomaly prediction.
- PCAP upload for signature detection and optional TLS analysis through `tshark`.
- SHAP/LIME explainability for anomaly alerts.
- Continual learning dashboard for reviewing captured samples, relabeling, retraining, and model promotion.
- Analytics query builder for alerts, logs, rules, users, and training data.
- React + Vite frontend with Flask JSON API backend.
- Authentication and role-based access control.

## Fresh Clone Quick Start

These steps are for a new user downloading the project from GitHub.

### Requirements

Install these first:

- Python 3.10 recommended
- Node.js 18 or newer
- npm
- Npcap on Windows, or libpcap on Linux, for live capture
- Wireshark/tshark only if TLS decryption features are needed

### 1. Clone The Repository

```powershell
git clone https://github.com/mohameddahmedd/IDS-Grad-Helwan.git
cd IDS-Grad-Helwan
```

### 2. Create And Activate Python Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\activate
```

### 3. Install Backend Requirements

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start The Backend

```powershell
python UI.py
```

The backend runs on:

```text
http://127.0.0.1:8000
```

On first startup, the app creates `DB/IDS.db`, creates all required tables, and creates the default admin account.

Default login:

```text
username: admin
password: admin
```

### 5. Start The Frontend

Open a second terminal:

```powershell
cd IDS-Grad-Helwan\frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal. The project is configured to use:

```text
http://127.0.0.1:5174
```

The frontend proxies `/api/*` requests to the Flask backend on port `8000`, so both backend and frontend must be running at the same time.

## Running Without A Virtual Environment

It is possible, but not recommended:

```powershell
pip install -r requirements.txt
python UI.py
```

Using a virtual environment is safer because this project depends on specific versions of Flask, scikit-learn, CatBoost, SHAP, LIME, Scapy, pandas, and NumPy.

## Project Structure

```text
IDS-Grad-Helwan/
├── DB/                         # Runtime SQLite database folder
├── Models/                     # Trained models, scaler, encoders, feature order, datasets
│   ├── Models/                 # tst1_stk_classifier.joblib, isolation_forest.joblib, dnn model
│   ├── Scaler/                 # MinMax scaler
│   ├── Label Encoder/          # Label encoders
│   ├── Features_Order/         # Feature order used by the ML pipeline
│   ├── Dt/                     # CIC-IDS-2017 dataset files used by evaluation/retraining
│   ├── ML/                     # Additional model/training files
│   └── test/                   # Small test/evaluation CSV files
├── frontend/                   # React + Vite frontend
│   ├── src/api/                # API client
│   ├── src/components/         # Shared UI components
│   ├── src/context/            # Authentication context
│   ├── src/pages/              # Main application pages
│   └── vite.config.js          # Dev server and API proxy config
├── tests/                      # pytest test suite
├── Rules/                      # Bundled default signature rules for fresh databases
├── UI.py                       # Flask backend entry point
├── api_auth.py                 # Auth API routes
├── api_routes.py               # Main JSON API routes
├── app_state.py                # Shared app paths, model state, runtime state
├── DB.py                       # SQLite connection and table creation
├── auth.py                     # Users, roles, password hashing, access control
├── signature_IDS.py            # Signature detection engine
├── anomaly_IDS.py              # ML anomaly detection engine
├── live_capture.py             # Live packet capture and detection loop
├── flow.py                     # Flow feature extraction
├── packet.py                   # Packet parsing and normalization
├── rule.py                     # Signature rule object and matching logic
├── RuleProcessor.py            # Rule loading/parsing helper
├── explainability.py           # SHAP/LIME alert explanations
├── continual_learning.py       # Relabeling, retraining, promotion, rollback
├── analytics.py                # Analytics query builder engine
├── tls_decrypt.py              # TLS metadata/decryption helper using tshark
├── requirements.txt            # Python dependencies
└── start_backend.bat           # Windows backend launcher
```

## Backend Data Flow

1. `UI.py` starts Flask, loads the trained models, scaler, label encoder, and feature order.
2. `DB.py` opens `DB/IDS.db` and creates missing tables.
3. If the `rules` table is empty, `RuleProcessor.py` loads bundled rules from `Rules/default_rules.json`.
4. `auth.py` creates the default `admin/admin` user if no users exist.
5. The React frontend calls Flask through `/api/*`.
6. Signature detection uses `signature_IDS.py`, `rule.py`, and `packet.py`.
7. Anomaly detection uses `anomaly_IDS.py`, `flow.py`, the scaler, the Isolation Forest, the stacking classifier, and the label encoder.
8. Live capture uses `live_capture.py` to sniff packets, build flows, run signature checks, run anomaly checks, and store alerts/logs in SQLite.
9. Explainability uses `explainability.py` to generate SHAP/LIME details for stored anomaly alert features.
10. Continual learning uses `continual_learning.py` to store flow samples, accept human labels, retrain candidate models, evaluate them, and promote/rollback models.

## Database

The SQLite database file is not committed to GitHub:

```text
DB/IDS.db
```

It is generated locally on first backend startup. The following runtime tables are created automatically:

- `rules`
- `logs`
- `alerts`
- `users`
- `alert_features`
- `training_data`
- `retrain_jobs`

The runtime database is not committed, but the default signature rules are committed in:

```text
Rules/default_rules.json
```

On first backend startup, those rules are inserted automatically if the `rules` table is empty. This allows signature-based detection, PCAP signature analysis, and live capture to work immediately after a fresh clone.

## Default Ports

```text
Backend:  http://127.0.0.1:8000
Frontend: http://127.0.0.1:5174
```

## Running Tests

Activate the virtual environment first, then run:

```powershell
python -m pytest tests -v
```

## Notes

- Live capture may require Administrator privileges on Windows.
- Install Npcap on Windows before using live capture.
- TLS decryption requires Wireshark/tshark to be installed and available on the system.
- The local database, uploaded files, logs, virtual environment, frontend build output, and generated model outputs are intentionally ignored by Git.
