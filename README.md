<div align="center">

# 🕵️ HOLMES IDS

### Hybrid Online Learning Model for Enhanced Security

**A hybrid Intrusion Detection System combining signature-based detection, ML-driven anomaly detection, explainability, continual learning, and role-based analytics — in one web application.**

![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![SQLite](https://img.shields.io/badge/SQLite-Database-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-Academic-orange?style=for-the-badge)

![HOLMES IDS home page](docs/screenshots/home-page.png)

</div>

> ⚠️ **Graduation Project Notice** — This repository is a graduation project for **Capital University, Faculty of Computers and Artificial Intelligence, Medical Informatics Department**. It is an **academic prototype** for IDS research, experimentation, and demonstration — **not** an enterprise production security platform.

---

## 🧭 Table of Contents

- [Project Scope](#-project-scope)
- [Key Features](#-key-features)
- [Evaluation Results](#-corrected-evaluation-summary)
- [Architecture](#%EF%B8%8F-architecture-overview)
- [Repository Structure](#-repository-structure)
- [Requirements](#-requirements)
- [Quick Start](#-fresh-clone-quick-start)
- [Demo Login](#-default-demo-login)
- [Workflows / Routes](#-common-workflows)
- [Testing](#-running-tests)
- [Live Capture](#-live-capture-notes)
- [TLS Analysis](#-tls-analysis-notes)
- [Troubleshooting](#-troubleshooting)
- [Git Hygiene](#-git-hygiene)
- [Disclaimer](#-academic-disclaimer)

---

## 🎯 Project Scope

HOLMES IDS explores a practical **hybrid IDS workflow**, built around six core pillars:

| 🛡️ | Capability |
| :--: | --- |
| 🔍 | Detect **known attacks** with signature rules |
| 🤖 | Detect **behavioral anomalies** with trained ML models |
| 📁 | Analyze uploaded **CSV flow records** and **PCAP files** |
| 📡 | Monitor **live traffic** when capture drivers/permissions are available |
| 💡 | **Explain** anomaly alerts via SHAP/LIME-style feature contribution views |
| 🔁 | Support **human-in-the-loop continual learning** — label, retrain, promote, rollback |

---

## ⚡ Key Features

| Area | What HOLMES IDS Provides |
| --- | --- |
| 🧩 **Signature IDS** | Rule-based matching for known attack patterns using bundled default rules |
| 🧠 **Anomaly IDS** | Flow-based anomaly prediction using trained models, scaler, label encoder, and feature order files |
| 📊 **CSV Analysis** | Batch prediction for uploaded CSV samples |
| 📦 **PCAP Analysis** | Signature detection for uploaded packet captures, with optional TLS metadata via `tshark` |
| 🎥 **Live Capture** | Interface selection, capture start/stop controls, signature + anomaly checks, alert storage |
| 🔬 **Explainability** | Alert explanation views for stored anomaly alert features |
| 🔄 **Continual Learning** | Human labels, candidate retraining, model evaluation, promotion, and rollback |
| 📈 **Analytics** | Query builder across alerts, logs, rules, users, and training data |
| 🔐 **Security Controls** | Authentication, session handling, CSRF-aware API flow, and role-based access control |

---

## 📊 Corrected Evaluation Summary

> Dissertation and defense materials use the following **corrected Chapter 4** values.

<div align="center">

| Metric | Result |
| --- | ---: |
| Stacking Classifier — Accuracy | **92.74%** |
| Stacking Classifier — Precision | **92.74%** |
| Stacking Classifier — Recall | **92.74%** |
| Stacking Classifier — F1-score | **92.74%** |
| Full Hybrid Pipeline — Accuracy | **94.40%** |
| Full Hybrid Pipeline — Precision | **92.74%** |
| Full Hybrid Pipeline — Recall | **92.85%** |
| Full Hybrid Pipeline — F1-score | **92.02%** |
| Benign False Positive Rate | ≈ **7.65%** |
| Simulated Out-of-Distribution Detection | **92 / 100** samples detected |

</div>

> ℹ️ These results describe the project's evaluation setup only and should **not** be interpreted as guaranteed zero-day detection or production readiness.

---

## 🏗️ Architecture Overview

```text
                    ┌─────────────────────────┐
                    │   React + Vite Frontend │
                    └────────────┬────────────┘
                                 │  /api/*
                                 ▼
                    ┌─────────────────────────┐
                    │       Flask Backend      │
                    ├───────────────────────────┤
                    │ • Authentication & RBAC   │
                    │ • Signature Detection      │
                    │ • Anomaly Detection        │
                    │ • Live Capture Service     │
                    │ • Explainability Module    │
                    │ • Continual Learning       │
                    │ • Analytics Query Engine   │
                    └────────────┬───────────────┘
                                 ▼
            ┌────────────────────────────────────────┐
            │ SQLite Database + Model Artifacts + Rules │
            └────────────────────────────────────────┘
```

---

## 📂 Repository Structure

```text
Holmes-IDS-Helwan/
├── frontend/                  React + Vite web interface
├── tests/                     pytest test suite
├── Rules/                     bundled default signature rules
├── Models/                    trained models, scaler, encoders, feature order, datasets
├── DB/                        local SQLite database folder
├── uploads/                   runtime upload folder
├── docs/screenshots/          README screenshots
├── UML/                       original UML/design assets
├── UI.py                      Flask backend entry point
├── api_auth.py                authentication API routes
├── api_routes.py              main JSON API routes
├── auth.py                    users, roles, password hashing, access control
├── DB.py                      SQLite connection and table creation
├── signature_IDS.py           signature detection engine
├── anomaly_IDS.py             anomaly detection engine
├── live_capture.py            live packet capture workflow
├── explainability.py          alert explanation support
├── continual_learning.py      relabeling, retraining, promotion, rollback
├── analytics.py                analytics query builder
├── requirements.txt           Python dependencies
├── start_backend.bat          Windows backend launcher
└── start_frontend.bat         Windows frontend launcher
```

---

## 🧰 Requirements

| Requirement | Notes |
| --- | --- |
| 🐍 Python | 3.10 recommended |
| 🟢 Node.js | 18 or newer |
| 📦 npm | bundled with Node.js |
| 📡 Npcap / libpcap | Npcap on Windows, libpcap on Linux — required for live capture |
| 🦈 Wireshark / tshark | Only needed for TLS analysis |

---

## 🚀 Fresh Clone Quick Start

**1. Clone the repository**

```powershell
git clone https://github.com/Mazen2004212/Holmes-IDS-Helwan.git
cd Holmes-IDS-Helwan
```

**2. Create and activate a virtual environment**

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

> If PowerShell blocks activation:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> .\.venv\Scripts\activate
> ```

**3. Install backend dependencies**

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**4. Start the backend**

```powershell
python UI.py
```

```text
🌐 Backend running at: http://127.0.0.1:8000
```

**5. Start the frontend** *(in a second terminal)*

```powershell
cd frontend
npm install
npm run dev
```

```text
🌐 Frontend running at: http://127.0.0.1:5174
```

---

## 🔑 Default Demo Login

```text
username: admin
password: admin
```

> 🚨 **Security Notice** — The default account is for local academic/demo use only. **Change it** before any real deployment or public demonstration environment.

---

## 🗺️ Common Workflows

| Workflow | Route |
| --- | --- |
| 🏠 Signature dashboard | `/` |
| 🧠 Anomaly dashboard | `/anomaly` |
| 📊 CSV anomaly detection | `/csv` |
| 📦 PCAP signature detection | `/upload_pcap` |
| 📡 Live capture | `/live` |
| 📜 Rules dashboard | `/rules` |
| 📈 Analytics query builder | `/analytics` |
| 🔁 Continual learning | `/retrain` |
| 👤 User management | `/admin` |

---

## ✅ Running Tests

After activating the Python environment:

```powershell
python -m pytest tests -v
```

---

## 📡 Live Capture Notes

**On Windows:**
- Install **Npcap**
- Restart the machine after installation
- Run the terminal, VS Code, or PowerShell **as Administrator**
- Select the correct network interface inside the application

**On Linux:**
- Install **libpcap**
- Run with suitable packet capture permissions, or use `sudo` when required

---

## 🔒 TLS Analysis Notes

TLS-related PCAP functionality requires **Wireshark/tshark** to be installed and available on the system `PATH`.

Check availability with:

```powershell
tshark -v
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
| --- | --- |
| Backend does not start | Activate `.venv`, install `requirements.txt`, then run `python UI.py` |
| Frontend does not start | Run `npm install` inside `frontend/`, then `npm run dev` |
| Frontend cannot call APIs | Make sure the backend is running on `http://127.0.0.1:8000` |
| Live capture stops immediately (Windows) | Install Npcap, restart Windows, run terminal as Administrator |
| No capture interfaces appear | Reinstall Npcap and enable WinPcap API-compatible mode |
| TLS analysis fails | Install Wireshark and confirm `tshark -v` works |
| Database is missing | Start the backend once — `DB/IDS.db` is created automatically |

---

## 🧹 Git Hygiene

The project should **not** commit local runtime files such as:

- `.venv/`
- `node_modules/`
- `__pycache__/`
- local `.env` files
- generated frontend builds
- local logs
- runtime uploads
- local SQLite runtime databases

---

## 🎓 Academic Disclaimer

HOLMES IDS is a **graduation project prototype**, designed for academic demonstration, controlled experiments, and IDS workflow exploration. It should be hardened, audited, tested on broader datasets, and deployed with secure operational controls before any real-world security use.

---

<div align="center">
<sub>Built for academic research at Capital University — Faculty of Computers and Artificial Intelligence, Medical Informatics Department.</sub>
</div>
