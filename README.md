# 🏥 MediTrack — Hospital Appointment No-Show & Operational Analysis

Full-stack web application: **FastAPI + PostgreSQL + Vanilla JS**

---

## 📁 Project Structure

```
hosp_proj/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/routes/         # auth, appointments, analytics, patients, departments, upload
│   │   ├── core/               # config, security (JWT), dependencies
│   │   ├── db/                 # session, base, init_db (seeder)
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # analytics engine, risk scorer, CSV importer
│   │   └── main.py             # FastAPI app entry point
│   ├── alembic/                # DB migrations
│   ├── .env.example            # Environment variable template
│   ├── alembic.ini
│   └── requirements.txt
└── frontend/                   # HTML/CSS/JS SPA
    ├── index.html
    ├── css/style.css
    └── js/
        ├── api.js              # All fetch() calls to the API
        ├── app.js              # App bootstrap, navigation, page renders
        ├── charts.js           # Chart.js chart renderers
        ├── tables.js           # Paginated data tables
        ├── modals.js           # CRUD modals (appointments, users)
        └── reports.js          # CSV export from live API data
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 14+ running locally
- Node not required (pure HTML/JS frontend)

### 2. Create PostgreSQL Database
```sql
CREATE DATABASE hospital_db;
```

### 3. Configure Environment
```bash
cd backend
copy .env.example .env
# Edit .env — set your DATABASE_URL and SECRET_KEY
```

**.env example:**
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/hospital_db
SECRET_KEY=your-super-secret-key-min-32-chars-long
FIRST_ADMIN_EMAIL=admin@hospital.com
FIRST_ADMIN_PASSWORD=Admin@123
```

### 4. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 5. Start the Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The server will:
- Auto-create all database tables
- Seed departments, doctors, and the admin user

### 6. Open the Frontend
Open your browser and go to:
```
http://localhost:8000
```
The FastAPI server serves the frontend automatically.

**OR** open `frontend/index.html` directly in your browser (works too, API is on localhost:8000).

### 7. Login
- Email: `admin@hospital.com`
- Password: `Admin@123`

---

## 📊 Features

| Feature | Description |
|---|---|
| **Login / Auth** | JWT-based login with access + refresh tokens |
| **Dashboard** | Live KPI cards, monthly trend, dept no-show, risk factors |
| **No-Show Analysis** | Filter by dept/age/gender/SMS, 7 interactive charts |
| **Operational Analysis** | Capacity, doctor workload, wait times, peak hours |
| **Patient Demographics** | Age, gender, neighbourhood, condition charts |
| **Appointments CRUD** | Add, edit, delete appointments with risk auto-calculation |
| **CSV Upload** | Import Kaggle dataset or any custom CSV format |
| **Reports Export** | Download 5 report types as CSV |
| **User Management** | Admin can create/edit/delete staff users |
| **Risk Scoring** | Auto-computed on every appointment create/update |

---

## 📤 CSV Upload

Supports the **Kaggle Medical Appointment No Shows** dataset directly.
Also accepts custom CSVs — column names are automatically mapped.

Download Kaggle dataset: https://www.kaggle.com/datasets/joniarroba/noshowappointments

---

## 🔌 API Endpoints

Full interactive docs at: `http://localhost:8000/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login, get JWT tokens |
| GET | `/api/auth/me` | Current user info |
| GET | `/api/analytics/kpi` | Summary KPIs |
| GET | `/api/analytics/monthly` | Monthly buckets |
| GET | `/api/analytics/departments` | Dept stats |
| GET | `/api/analytics/doctors` | Doctor workload |
| GET | `/api/analytics/age-groups` | Age group breakdown |
| GET | `/api/analytics/dow` | Day-of-week stats |
| GET | `/api/analytics/risk-factors` | Risk factor counts |
| GET | `/api/analytics/sms-impact` | SMS vs no-SMS rates |
| GET | `/api/analytics/lead-time` | Lead time buckets |
| GET/POST | `/api/appointments` | List / create appointments |
| GET/PUT/DELETE | `/api/appointments/{id}` | Get / update / delete |
| GET/POST | `/api/patients` | List / create patients |
| POST | `/api/upload/csv` | Import CSV file |
| GET | `/api/departments` | List departments |
| GET | `/api/departments/doctors` | List doctors |

All endpoints accept `?year=2024|2023|q1|q2|q3|q4|all` filter.
