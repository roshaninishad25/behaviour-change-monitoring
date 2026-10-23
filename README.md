# Behavioural Change Monitoring System (PRJ_221)

> **Predictive Longitudinal Learning Analytics, Anomaly Detection & Decision Support Platform**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.3-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4%2B-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org)

---

## 📖 Overview

The **Behavioural Change Monitoring System (PRJ_221)** is an end-to-end full-stack machine learning software designed to observe, analyze, and predict student learning behavior over sequential course periods. 

By modeling longitudinal student interaction data (course access, lecture views, forum engagement, session counts, and regularity), the platform identifies learning state transitions (*Improving*, *Stable*, *Declining*), flags irregular drop-offs via unsupervised anomaly detection, and provides explainable AI insights (SHAP) alongside automated actionable recommendations for educators and students.

---

## 🎯 Core Features

### 🎓 1. Student Portal
- **Real-Time Behavioral Dashboard:** Displays current Behavioral State (*Improving*, *Stable*, or *Declining*) and Behavioral Change Index (BCI score).
- **Anomaly Monitoring:** Flags sudden deviations in engagement or irregular activity patterns using an Isolation Forest model.
- **Sequential Trend Analysis:** Interactive visual charts tracking 8 distinct metrics across sequential course periods (Session count, active days, video views, forum contributions, final grade).
- **Explainable AI (SHAP):** Visual breakdown of top behavioral factors contributing to the student's predicted trajectory.
- **Actionable Recommendations & Alerts:** Automated, rule-based feedback guiding students on study habits and resource utilization.
- **Strict Data Ownership (Anti-IDOR):** Students can only access their own records. Changing the user ID parameter returns `403 Forbidden`.

### 🏫 2. Faculty Portal
- **Cohort Overview:** Comprehensive view of the entire student cohort with distribution of behavioral states and risk categories (*Low*, *Medium*, *High*).
- **Student Inspection & Filtering:** Search, filter, and inspect detailed profiles, behavioral history, and anomaly history for any individual student.
- **Elevated Monitoring Alerts:** Dedicated alerts queue for students requiring immediate review.
- **Manual Assessment Simulator:** Interactive tool allowing faculty to input multi-sequence student behavioral data to run on-demand predictions and SHAP explanations.

### 🔐 3. Security & Architecture
- **JWT Role-Based Access Control:** Role-restricted API endpoints with bearer token validation.
- **Secure Password Hashing:** PBKDF2-HMAC-SHA256 with 310,000 iterations and constant-time digest comparison.
- **Gated Faculty Registration:** Faculty signup is strictly protected via server-side `FACULTY_INVITE_CODE`.
- **Identity Derivation:** User identities are derived strictly from cryptographically signed JWT claims, not client-supplied query parameters.

---

## 🏗️ Architecture & Workflow

```
+-------------------------------------------------------------------------+
|                              USER BROWSER                               |
|   React 19 + Vite Dashboard  (Student View / Faculty Cohort Overview)   |
+------------------------------------+------------------------------------+
                                     |
                                     | HTTP Requests + JWT Bearer Token
                                     v
+-------------------------------------------------------------------------+
|                           FASTAPI BACKEND                               |
|                                                                         |
|   +-------------------+  +--------------------+  +------------------+   |
|   |   Auth & RBAC     |  |   Data Validation  |  | Recommendation   |   |
|   |  (PyJWT / PBKDF2) |  |    (Pydantic)      |  | & Alert Engine   |   |
|   +-------------------+  +--------------------+  +------------------+   |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |                     ML Inference Engine                         |   |
|   |  - Random Forest Classifier (Behavioral Trajectory Prediction)  |   |
|   |  - Isolation Forest (Unsupervised Anomaly Detection)            |   |
|   |  - TreeSHAP (Feature Importance & Explainability)               |   |
|   +-----------------------------------------------------------------+   |
+-------------------+---------------------------------+-------------------+
                    |                                 |
                    v                                 v
+-----------------------------------+ +-----------------------------------+
|        POSTGRESQL DATABASE        | |         SAVED ML MODELS           |
|  - Users & Credentials            | |  - random_forest_v2.pkl           |
|  - Behaviour Records (8 periods)  | |  - isolation_forest.pkl           |
|  - Predictions & Anomalies        | |  - anomaly_scaler.pkl             |
|  - Alerts & Recommendations       | |  - feature_columns.json           |
+-----------------------------------+ +-----------------------------------+
```

---

## 💻 Tech Stack

| Layer | Component | Technologies |
| :--- | :--- | :--- |
| **Frontend** | User Interface | React 19, Vite, Recharts, Lucide React, Modern CSS3 |
| **Backend** | REST API & Auth | FastAPI, Uvicorn, PyJWT, Pydantic, Python 3.10+ |
| **Database** | Relational Store | PostgreSQL 14+, Psycopg2 |
| **Machine Learning**| Analytics & Models | Scikit-Learn (Random Forest, Isolation Forest), SHAP, NumPy, Pandas, Joblib |
| **Testing** | Automated Quality Assurance | Python `unittest` suite (20 tests), ESLint, Vite build pipeline |

---

## 📂 Project Directory Structure

```text
PRJ_221/
├── backend/
│   └── app/
│       ├── database.py               # PostgreSQL connection pool & helpers
│       ├── schemas.py                # Pydantic models for data validation
│       └── main.py                   # FastAPI endpoints, auth & ML inference pipeline
├── frontend/
│   ├── src/
│   │   ├── api.js                    # Authenticated fetch wrapper (auto JWT attachment & 401 handler)
│   │   ├── App.jsx                   # Core router, student dashboard & layout
│   │   ├── App.css                   # Application styling
│   │   ├── AuthPage.jsx              # Login & registration with quick portal presets & invite codes
│   │   ├── FacultyOverview.jsx       # Faculty cohort dashboard & risk metrics
│   │   ├── FacultyDashboard.jsx      # Student directory & management
│   │   ├── FacultyStudentDetails.jsx # Detailed student drill-down view
│   │   └── NewPredictionPage.jsx     # Manual behavioral sequence assessment tool
│   ├── package.json
│   └── vite.config.js
├── models/                           # Serialized ML models and scaler artifacts
│   ├── random_forest_v2.pkl          # Trained Random Forest classifier
│   ├── isolation_forest.pkl          # Trained Isolation Forest anomaly detector
│   ├── anomaly_scaler.pkl            # Feature standardizer for anomaly scoring
│   └── feature_columns.json          # Expected 44-feature order & definitions
├── tests/                            # Automated test suite (Phase E)
│   ├── test_backend_api.py           # 12 API & RBAC endpoint tests
│   ├── test_ml_pipeline.py           # 5 ML inference and feature transformation tests
│   ├── test_database.py              # 2 Database schema and connection tests
│   └── test_e2e.py                   # 1 Full-lifecycle end-to-end integration test
├── scripts/
│   ├── health_check.py               # Production system readiness validator
│   └── seed_database.py              # Unified database migration and seeding
├── deployment/                       # Cloud & container deployment assets (Phase G)
│   ├── Dockerfile.backend            # Production backend container definition
│   ├── Dockerfile.frontend           # Production frontend Nginx container definition
│   ├── docker-compose.yml            # Multi-service local/cloud orchestration
│   └── nginx/default.conf            # Reverse proxy configuration
├── data/
│   ├── raw/
│   │   └── LongitudinalEngagement.csv # Simulated student sequence dataset
│   └── processed/
│       └── decision_results.csv
├── docs/
│   └── ml_methodology.md             # Theoretical & mathematical documentation
├── requirements.txt                  # Pinned Python production dependencies
├── .env.example                      # Template environment variables file
├── .gitignore
└── README.md
```

---

## ⚡ Quick Start Guide

### 1. Prerequisites
* **Python 3.10+** (with virtual environment `.venv`)
* **Node.js 18+ and npm**
* **PostgreSQL 14+**

---

### 2. Environment Setup

Create `.env` in the root directory:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prj_221
DB_USER=postgres
DB_PASSWORD=your_postgres_password

VITE_API_BASE_URL=http://127.0.0.1:8000
JWT_SECRET_KEY=your_secure_random_jwt_secret_key
FACULTY_INVITE_CODE=faculty_secret_passphrase
```

---

### 3. Automated System Health Check & Test Suite (Phase E)

Run the comprehensive health check:
```powershell
.venv\Scripts\python.exe scripts/health_check.py
```

Run the automated test suite (20 tests covering ML, Backend, DB, and E2E):
```powershell
.venv\Scripts\python.exe -m unittest discover tests
```

Run frontend linting and build checks:
```powershell
cd frontend
npm run lint
npm run build
cd ..
```

---

### 4. Running the Development Servers

**Backend:**
```powershell
.venv\Scripts\uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
* **API Root:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Frontend:**
```powershell
cd frontend
npm run dev
```
* **Web Portal:** [http://localhost:5173/](http://localhost:5173/)

---

## 🔑 Demo Access & Login Credentials

| Role | Email | Password | Features Accessible |
| :--- | :--- | :--- | :--- |
| **Student** | `00050f0e@example.com` | `Student123!` | Personal dashboard, longitudinal trends (8 periods), anomaly scores, SHAP explanations, recommendations |
| **Faculty** | `testfaculty@example.com` | `Faculty123!` | Cohort analytics, risk distributions, student profile inspector, manual sequence assessment simulator |

---

## 📡 API Reference Summary

All secured endpoints require the header: `Authorization: Bearer <access_token>`.

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Public | Authenticates credentials and returns JWT token & user profile |
| `POST` | `/auth/signup` | Public | Registers a new student account (role: Student) |
| `POST` | `/auth/signup/faculty` | Invite Code | Registers a faculty account using `FACULTY_INVITE_CODE` |
| `GET` | `/auth/me` | Authenticated | Derives current user identity directly from verified JWT |
| `GET` | `/dashboard/{user_id}` | Student (Self) / Faculty | Retrieves latest prediction, anomaly score, recommendation & alert |
| `GET` | `/trend/{user_id}` | Student (Self) / Faculty | Fetches longitudinal metrics across sequential periods |
| `GET` | `/explanation/{user_id}`| Student (Self) / Faculty | Returns SHAP feature attribution weights for explainable AI |
| `GET` | `/users/{user_id}` | Student (Self) / Faculty | Fetches student profile data |
| `GET` | `/faculty/students` | Faculty Only | Retrieves summary metrics and status for all cohort students |
| `POST` | `/predict` | Faculty Only | Evaluates manual multi-sequence behavioral inputs |
| `POST` | `/behavior` | Faculty Only | Adds a new sequential behavioral observation for a student |

---

## 📄 License
This project was developed for educational and academic research purposes (PRJ_221).
