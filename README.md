# 🏥 CareFlow — Hospital Appointment No-Show & Operational Analysis

Full-stack web application: **Flask + PostgreSQL + Jinja2 (server-rendered)**

---

## 📁 Project Structure

```
hosp_proj/
├── flask_app/                          # Flask application (the entire project)
│   ├── run.py                          # Entry point — runs on port 5000
│   ├── requirements.txt
│   ├── .env                            # Environment variables (not committed)
│   └── app/
│       ├── __init__.py                 # App factory — registers blueprints, seeds DB
│       ├── config.py                   # Loads settings from .env
│       ├── extensions.py               # SQLAlchemy db, Flask-Login login_manager
│       ├── seed.py                     # Seeds admin user, 10 departments, 30 doctors
│       ├── blueprints/
│       │   ├── auth.py                 # /login  /signup  /logout
│       │   ├── home.py                 # / (public landing page)
│       │   ├── dashboard.py            # /dashboard — KPI cards + recent appointments
│       │   ├── noshow.py               # /noshow — 7 no-show charts + AJAX filter
│       │   ├── operational.py          # /operational — capacity, workload, wait times
│       │   ├── demographics.py         # /demographics — age, gender, neighbourhood, conditions
│       │   ├── appointments.py         # /appointments — full CRUD + risk auto-calc
│       │   ├── patients.py             # /patients — list + individual profile page
│       │   ├── reminders.py            # /reminders — upcoming appointments, SMS tracking
│       │   ├── reports.py              # /reports — 5 report types, streamed CSV export
│       │   ├── upload.py               # /upload — CSV import (up to 150 MB)
│       │   └── admin.py                # /admin/users — admin-only user management
│       ├── models/
│       │   ├── user.py                 # Users (admin / staff)
│       │   ├── patient.py              # Patients + age_group property
│       │   ├── department.py           # Departments
│       │   ├── doctor.py               # Doctors (belong to a department)
│       │   └── appointment.py          # Appointments — includes uploaded_by (per-user isolation)
│       ├── services/
│       │   ├── analytics.py            # All SQL aggregations for charts & KPIs
│       │   ├── risk.py                 # Risk score algorithm (0-99, Low/Medium/High)
│       │   ├── csv_import.py           # Pandas CSV importer — Kaggle + custom formats
│       │   └── patients.py             # Patient profile aggregations
│       ├── static/
│       │   ├── css/
│       │   │   ├── style.css           # Main stylesheet
│       │   │   ├── home.css            # Landing page styles
│       │   │   └── print.css           # Print stylesheet
│       │   └── js/
│       │       ├── main.js             # Client-side interactions
│       │       └── charts.js           # Chart.js chart renderers
│       └── templates/
│           ├── base.html               # Base layout (sidebar, topbar, nav)
│           ├── auth/                   # login.html, signup.html
│           ├── home/                   # Landing page
│           ├── dashboard/              # index.html, empty.html (no data state)
│           ├── noshow/                 # index.html
│           ├── operational/            # index.html
│           ├── demographics/           # index.html
│           ├── appointments/           # index.html, form.html
│           ├── patients/               # index.html, profile.html
│           ├── reminders/              # index.html
│           ├── reports/                # index.html
│           ├── upload/                 # index.html
│           ├── admin/                  # users.html, user_form.html
│           ├── partials/               # kpi_grid.html, risk_pill.html, status_badge.html
│           └── shared/                 # no_data.html
└── README.md
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.11+
- PostgreSQL 14+ running locally

### 2. Create the Database
```sql
CREATE DATABASE hospital_db;
```

### 3. Configure Environment
```bash
cd flask_app
# Edit .env — set your database credentials
```

**.env:**
```
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/hospital_db
SECRET_KEY=your-secret-key-change-in-production
ADMIN_EMAIL=admin@hospital.com
ADMIN_PASSWORD=Admin@123
ADMIN_NAME=System Admin
```

### 4. Install Dependencies
```bash
cd flask_app
pip install -r requirements.txt
```

### 5. Run the App
```bash
cd flask_app
python run.py
```

The server starts at `http://localhost:5000`. On first run it will:
- Auto-create all database tables
- Seed 10 departments, 30 doctors, and the admin user

### 6. Login
| Field | Value |
|---|---|
| URL | `http://localhost:5000` |
| Email | `admin@hospital.com` |
| Password | `Admin@123` |

---

## 📊 Features

| Feature | Description |
|---|---|
| **Login / Auth** | Session-based auth with Flask-Login; admin and staff roles |
| **Dashboard** | KPI cards, monthly trend chart, department no-show, risk summary |
| **No-Show Analysis** | 7 interactive charts — dept, SMS, age, gender, day-of-week, lead time, previous no-shows |
| **Operational Analysis** | Capacity utilisation, doctor workload, avg wait times, peak-day analysis |
| **Patient Demographics** | Age groups, gender split, top-10 neighbourhoods, chronic condition impact, visit loyalty |
| **Appointments CRUD** | Add, edit, delete appointments; risk score auto-computed on every save |
| **Patient Profiles** | Individual patient page with full appointment history, monthly chart, risk trend |
| **Reminders** | Upcoming appointments within 1–30 days; filter by risk/SMS; mark SMS as sent |
| **CSV Upload** | Import Kaggle dataset or any custom CSV; column names auto-mapped; up to 150 MB |
| **Reports Export** | 5 report types (summary, no-show, department, doctor, full) streamed as CSV |
| **User Management** | Admin creates/edits/deletes staff users |
| **Risk Scoring** | Score 0–99 based on previous no-shows, lead days, SMS, scholarship, age, alcoholism |
| **Per-User Data** | Each user's uploaded data is isolated — `uploaded_by` scopes all queries |

---

## 📤 CSV Upload

Supports the **Kaggle Medical Appointment No Shows** dataset directly.  
Also accepts custom CSVs — column names are automatically normalised.

Download Kaggle dataset: https://www.kaggle.com/datasets/joniarroba/noshowappointments

---

## 🗺️ URL Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/login` | Login page |
| GET/POST | `/signup` | Create staff account |
| GET | `/logout` | Logout |
| GET | `/` | Public landing page |
| GET | `/dashboard` | Main dashboard |
| GET | `/noshow` | No-show analysis charts |
| POST | `/noshow/filter` | AJAX — re-fetch no-show charts by year |
| GET | `/operational` | Operational analysis charts |
| POST | `/operational/filter` | AJAX — re-fetch operational charts by year |
| GET | `/demographics` | Demographics charts |
| GET | `/appointments` | Appointment list (paginated, filterable) |
| GET/POST | `/appointments/new` | Create appointment |
| GET/POST | `/appointments/<id>/edit` | Edit appointment |
| POST | `/appointments/<id>/delete` | Delete appointment |
| GET | `/appointments/doctors/<dept_id>` | AJAX — doctors for a department |
| GET | `/patients` | Patient list (searchable) |
| GET | `/patients/<id>` | Patient profile page |
| GET | `/reminders` | Upcoming appointment reminders |
| POST | `/reminders/mark-sent/<id>` | Mark SMS reminder as sent |
| GET | `/reminders/api/upcoming` | AJAX — upcoming count badge |
| GET | `/reports` | Reports page |
| GET | `/reports/export/<type>` | Download CSV (`summary`/`noshow`/`department`/`doctor`/`full`) |
| GET/POST | `/upload` | Upload CSV file |
| GET | `/admin/users` | User management (admin only) |
| GET/POST | `/admin/users/new` | Create user (admin only) |
| GET/POST | `/admin/users/<id>/edit` | Edit user (admin only) |
| POST | `/admin/users/<id>/delete` | Delete user (admin only) |

---

## 🔒 Risk Score Algorithm

Scores are computed automatically on every appointment create/update.

| Factor | Points |
|---|---|
| 1 previous no-show | +12 |
| 2 previous no-shows | +22 |
| 3+ previous no-shows | +35 |
| Lead days 8–14 | +6 |
| Lead days 15–30 | +12 |
| Lead days 31+ | +20 |
| No SMS reminder | +15 |
| Patient on scholarship | +8 |
| Patient alcoholism | +10 |
| Age 18–35 | +8 |
| Age under 18 | +5 |

**Labels:** `Low` (0–29) · `Medium` (30–54) · `High` (55–99)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Web framework | Flask 3.0 |
| ORM | Flask-SQLAlchemy 3.1 (SQLAlchemy 2.0) |
| Auth | Flask-Login 0.6 |
| Forms | Flask-WTF 1.2 + WTForms 3.1 |
| Database | PostgreSQL 14+ |
| CSV processing | Pandas 2.2 |
| Password hashing | Werkzeug |
| Templates | Jinja2 (server-rendered) |
| Charts | Chart.js (CDN) |
