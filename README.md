# ☀️🔋 PassportOS — DPP-ERP Intelligence Platform

> **Winner — Best European Idea Award @ViennaUP Europe Tech Hackathon 2026**
> Built in under 24 hours by Team PassportOS

---

PassportOS works on connecting the EU Digital Product Passport with existing ERP solutions.

Two functional prototypes built from scratch:

| Platform             | Description                                         | Port |
| -------------------- | --------------------------------------------------- | ---- |
| 🔋 Battery DPP-ERP   | EV battery procurement, EOL decisions, compliance   | 8501 |
| ☀️ SolarPassport     | PV solar panel procurement, DPP data, ESG reporting | 8502 |
| 🔗 Mock ERP REST API | Flask API simulating SAP/weclapp/Odoo integration   | 5000 |

---

## Problem Statement

Every time a procurement manager needs to verify a battery or solar panel:

- Carbon footprint data is scattered across several supplier PDFs
- Supply chain ethics info is buried in audit reports or do not exist
- Compliance certificates are on separate regulatory websites
- Manual work synchronising all the info takes **3–5 hours per decision**

## Our Solution

```
Product Name / QR Code
        ↓
PassportOS Engine
  ├── Automatoc data collection (IEC/ISO registries, manufacturer databases)
  ├── EU compliance verification (CE, IEC 61215/61730, WEEE, RoHS, REACH)
  ├── AI validation algorithm (weighted scoring: Ethics × Carbon × Performance × Compliance × Price)
  └── DPP auto-generation
        ↓
Output: EU-verified DPP · Ranked procurement list · Auto ERP order via REST API
```

**Result: 3 clicks · Under 10 seconds · Full ERP record · Audit-ready · Zero manual research**

---

## Features

### 🔋 Battery DPP-ERP Platform (`app_v2.py`)

- **Procurement Advisor** — weighted scoring engine across compliance, ethics, sustainability, quality, price
- **EOL Decision Engine** — repair / second life / recycle / scrap based on State of Health data
- **Compliance Report** — EU Battery Regulation 2023/1542 verification
- **ESG Report** — auto-generated E, S, G scores from DPP data
- **AI Procurement Assistant** — Groq/LLaMA grounded in real passport data
- **ERP Order History** — live data pulled from REST API

### ☀️ SolarPassport PV Platform (`pv_prototype/pv_app.py`)

- **Dashboard** — panel cards with Best Choice / Acceptable / Least Optimal ranking
- **Procurement Page** — full DPP data view (carbon, materials, compliance, EOL, supplier ethics)
- **PDF Order Confirmation** — generated with full DPP data on order
- **EOL Engine** — continue / repair / second life / recycle based on efficiency degradation
- **ESG Report** — radar chart + auto executive summary
- **AI Assistant** — geopolitical risk analysis, sustainability advice, supply chain questions

### 🔗 Mock ERP REST API (`mock_erp_api.py`)

Follows the same integration pattern as SAP S/4HANA REST, weclapp AuthenticationToken, and Odoo JSON-RPC.

| Endpoint                 | Method | Description              |
| ------------------------ | ------ | ------------------------ |
| `/api/health`            | GET    | API status check         |
| `/api/purchase-orders`   | POST   | Create purchase order    |
| `/api/purchase-orders`   | GET    | List all purchase orders |
| `/api/eol-decisions`     | POST   | Record EOL decision      |
| `/api/eol-decisions`     | GET    | List all EOL decisions   |
| `/api/products`          | POST   | Register product         |
| `/api/dashboard/summary` | GET    | Live ERP summary stats   |

---

## Tech Stack

| Layer           | Technology                                                       |
| --------------- | ---------------------------------------------------------------- |
| Frontend / App  | Python 3.11, Streamlit, Plotly, Pandas                           |
| ERP Integration | Flask REST API, Flask-CORS                                       |
| Local Database  | SQLite (fallback when API offline)                               |
| AI Layer        | Groq API — LLaMA 3.3 70B                                         |
| PDF Generation  | ReportLab                                                        |
| DPP Standards   | EU Battery Reg. 2023/1542, IEC 61215, IEC 61730, WEEE 2012/19/EU |

---

## Project Structure

```
ViennaUP_Hackathon/
│
├── start.sh                        # One-command launcher (choose Battery / Solar / Both)
├── mock_erp_api.py                 # 🔗 Flask mock ERP REST API (shared by both apps)
├── erp_connector.py                # ERP integration layer (swap URL for real ERP)
├── config.py                       # Shared config — reads GROQ_API_KEY from environment
├── requirements.txt
│
├── dpp_erp_prototype/
│   ├── app_v2.py                   # 🔋 Battery DPP-ERP Streamlit app
│   └── passports.json              # 6 EV battery DPP records
│
└── pv_prototype/
    ├── pv_app.py                   # ☀️ SolarPassport Streamlit app
    └── pv_passports.json           # 6 PV panel DPP records
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- pip

### 1. Clone the repo

```bash
git clone https://github.com/MpyK/ViennaUP_Hackathon.git
cd ViennaUP_Hackathon
```

### 2. Install dependencies

```bash
pip install streamlit plotly pandas flask flask-cors requests reportlab
```

Or install everything at once:

```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key

Get a free key at **console.groq.com** → API Keys → create key, then set it as an environment variable:

**Windows (PowerShell):**

```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
```

**Mac / Linux:**

```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

To persist it across sessions, add it to your shell profile or system environment variables.

---

## Running the App

Activate your Python environment, then run:

```bash
bash start.sh
```

You'll be prompted to choose:

```
  PassportOS
  ----------
  1) Battery DPP
  2) Solar Passport
  3) Both
```

The ERP API always starts in the background. Ctrl+C stops everything at once.

| App         | URL                   |
| ----------- | --------------------- |
| Battery DPP | http://localhost:8501 |
| Solar DPP   | http://localhost:8502 |
| ERP API     | http://localhost:5000 |

---

## requirements.txt

```
streamlit>=1.28.0
plotly>=5.18.0
pandas>=2.0.0
flask>=3.0.0
flask-cors>=4.0.0
requests>=2.31.0
reportlab>=4.0.0
```

---

## ERP Integration

The `erp_connector.py` file is the integration layer between the app and any ERP system.

To connect to a **real ERP** (weclapp, SAP, Odoo), change one line:

```python
# Current (mock)
ERP_BASE_URL = "http://localhost:5000/api"

# weclapp
ERP_BASE_URL = "https://your-tenant.weclapp.com/webapp/api/v1"

# SAP S/4HANA
ERP_BASE_URL = "https://your-sap-instance.com/sap/opu/odata/sap"
```

---

## DPP Data

### Battery Passports (`passports.json`)

6 batteries with full EU Battery Regulation 2023/1542 fields:

| ID      | Manufacturer         | Compliance       |
| ------- | -------------------- | ---------------- |
| BAT-001 | Volvo Cars AB        | ✅ Compliant     |
| BAT-002 | Northvolt AB         | ✅ Compliant     |
| BAT-003 | Samsung SDI          | ✅ Compliant     |
| BAT-004 | EuroBattery Minerals | ✅ Compliant     |
| BAT-005 | CATL Europe GmbH     | ✅ Compliant     |
| BAT-006 | Unknown Origin       | ❌ Non-Compliant |

### PV Panel Passports (`pv_prototype/pv_passports.json`)

6 solar panels with EU Ecodesign + IEC 61215/61730 fields:

| ID     | Manufacturer            | Carbon Class | Compliance       |
| ------ | ----------------------- | ------------ | ---------------- |
| PV-001 | LONGi Solar             | A            | ✅ Compliant     |
| PV-002 | Meyer Burger Technology | A+           | ✅ Compliant     |
| PV-003 | Jinko Solar             | B            | ✅ Compliant     |
| PV-004 | REC Group               | A            | ✅ Compliant     |
| PV-005 | SunPower (Maxeon Solar) | A+           | ✅ Compliant     |
| PV-006 | SolarMax Generic        | Not declared | ❌ Non-Compliant |

---

## Regulatory Standards Covered

- **EU Battery Regulation** (Reg. EU 2023/1542) — mandatory DPP from 2027
- **IEC 61215** — PV module design qualification and type approval
- **IEC 61730** — PV module safety qualification
- **EU Ecodesign Regulation** — energy-related products sustainability
- **WEEE Directive** (2012/19/EU) — waste electrical equipment take-back
- **RoHS Directive** — restriction of hazardous substances
- **REACH Regulation** — chemical substance safety

---

## Scalability

Started with EV batteries. Extended to solar PV panels in **under 4 hours** — completely different suppliers, materials, EU standards, and CO₂ metrics. The ERP integration, AI layer, and ESG engine required zero changes.

Next product categories the architecture supports: wind turbines · EV chargers · heat pumps · industrial equipment — any product the EU mandates a DPP for.

---

## Team

**Muthukrishnan Jayakumar** — Tech Lead / Full-Stack Developer
**Sidharth** — Validation

Built at **ViennaUP Europe Tech Hackathon 2026** — Challenge 1: Product Passport meets ERP

---

## License

MIT License — free to use, modify, and distribute.

---
