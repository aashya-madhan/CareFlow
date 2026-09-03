"""
CSV import service.
Accepts the Kaggle Medical Appointment No Shows dataset OR
any CSV with columns mapped via the column_map parameter.

Expected canonical columns (case-insensitive, flexible naming):
  patient_code, full_name, age, gender, neighbourhood,
  scholarship, hypertension, diabetes, alcoholism, handicap,
  department, doctor, appointment_date, scheduled_date,
  lead_days, sms_received, previous_no_shows, wait_minutes, status
"""

import pandas as pd
import io
import re
from datetime import date
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.services.risk import compute_risk_score, get_risk_label


# Flexible column name normalizer
COLUMN_MAP = {
    # patient fields
    "patientid": "patient_code",
    "patient_id": "patient_code",
    "patient_code": "patient_code",
    "name": "full_name",
    "full_name": "full_name",
    "patient_name": "full_name",
    "age": "age",
    "gender": "gender",
    "sex": "gender",
    "neighbourhood": "neighbourhood",
    "neighborhood": "neighbourhood",
    "scholarship": "scholarship",
    "hipertension": "hypertension",
    "hypertension": "hypertension",
    "diabetes": "diabetes",
    "alcoholism": "alcoholism",
    "handcap": "handicap",
    "handicap": "handicap",
    "disability": "handicap",
    # appointment fields
    "appointmentid": "appointment_id",
    "scheduledday": "scheduled_date",
    "scheduled_date": "scheduled_date",
    "appointmentday": "appointment_date",
    "appointment_date": "appointment_date",
    "no_show": "status",
    "noshow": "status",
    "status": "status",
    "sms_received": "sms_received",
    "smssent": "sms_received",
    "sms_sent": "sms_received",
    "department": "department",
    "doctor": "doctor",
    "wait_minutes": "wait_minutes",
    "waitminutes": "wait_minutes",
    "lead_days": "lead_days",
    "leaddays": "lead_days",
    "previous_no_shows": "previous_no_shows",
    "previousnoshow": "previous_no_shows",
    "no_of_no_shows": "previous_no_shows",
    "time_slot": "time_slot",
    "timeslot": "time_slot",
}

DEPARTMENTS = [
    "Cardiology", "Orthopedics", "Neurology", "Pediatrics",
    "General Medicine", "Dermatology", "Gynecology",
    "Ophthalmology", "Psychiatry", "ENT",
]

DOCTORS_BY_DEPT = {
    "Cardiology": ["Dr. Smith", "Dr. Patel", "Dr. Chen"],
    "Orthopedics": ["Dr. Johnson", "Dr. Williams", "Dr. Brown"],
    "Neurology": ["Dr. Davis", "Dr. Martinez", "Dr. Wilson"],
    "Pediatrics": ["Dr. Anderson", "Dr. Taylor", "Dr. Thomas"],
    "General Medicine": ["Dr. Jackson", "Dr. White", "Dr. Harris"],
    "Dermatology": ["Dr. Martin", "Dr. Thompson", "Dr. Garcia"],
    "Gynecology": ["Dr. Nguyen", "Dr. Lewis", "Dr. Lee"],
    "Ophthalmology": ["Dr. Walker", "Dr. Hall", "Dr. Allen"],
    "Psychiatry": ["Dr. Young", "Dr. Hernandez", "Dr. King"],
    "ENT": ["Dr. Wright", "Dr. Lopez", "Dr. Hill"],
}

import random


def _normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [re.sub(r"[\s\-]", "_", c).lower().strip() for c in df.columns]
    renamed = {}
    for col in df.columns:
        if col in COLUMN_MAP:
            renamed[col] = COLUMN_MAP[col]
    return df.rename(columns=renamed)


def _parse_bool(val) -> bool:
    if isinstance(val, bool): return val
    if isinstance(val, (int, float)): return bool(val)
    s = str(val).strip().lower()
    return s in ("1", "yes", "true", "y", "sim")


def _parse_status(val) -> str:
    s = str(val).strip()
    # Kaggle uses "No" = showed, "Yes" = no-show (confusingly)
    if s.lower() in ("yes", "1", "true", "no-show", "noshow"):
        return "No-Show"
    if s.lower() in ("no", "0", "false", "showed", "show"):
        return "Showed"
    if s.lower() in ("cancelled", "canceled"):
        return "Cancelled"
    return "Showed"


def _get_or_create_dept(db: Session, name: str) -> Department:
    dept = db.query(Department).filter(Department.name == name).first()
    if not dept:
        dept = Department(name=name)
        db.add(dept)
        db.flush()
    return dept


def _get_or_create_doctor(db: Session, name: str, dept_id: int) -> Doctor:
    doc = db.query(Doctor).filter(Doctor.name == name).first()
    if not doc:
        doc = Doctor(name=name, department_id=dept_id)
        db.add(doc)
        db.flush()
    return doc


def import_csv(db: Session, file_bytes: bytes, filename: str) -> dict:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return {"success": False, "error": f"Could not parse CSV: {e}", "inserted": 0, "skipped": 0}

    df = _normalize_cols(df)
    inserted = 0
    skipped = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            # ---- patient_code ----
            p_code = str(row.get("patient_code", f"P{idx+1000}")).strip()

            # ---- patient fields ----
            full_name    = str(row.get("full_name", f"Patient {p_code}")).strip()
            age          = int(float(row.get("age", 30)))
            gender_raw   = str(row.get("gender", "Male")).strip()
            gender       = "Female" if gender_raw.lower() in ("f", "female", "feminino") else "Male"
            neighbourhood = str(row.get("neighbourhood", "Unknown")).strip()
            scholarship  = _parse_bool(row.get("scholarship", False))
            hypertension = _parse_bool(row.get("hypertension", False))
            diabetes     = _parse_bool(row.get("diabetes", False))
            alcoholism   = _parse_bool(row.get("alcoholism", False))
            handicap     = _parse_bool(row.get("handicap", False))

            # ---- get or create patient ----
            patient = db.query(Patient).filter(Patient.patient_code == p_code).first()
            if not patient:
                patient = Patient(
                    patient_code=p_code, full_name=full_name, age=max(0, min(120, age)),
                    gender=gender, neighbourhood=neighbourhood,
                    scholarship=scholarship, hypertension=hypertension,
                    diabetes=diabetes, alcoholism=alcoholism, handicap=handicap,
                )
                db.add(patient)
                db.flush()

            # ---- appointment date ----
            appt_date_raw = row.get("appointment_date")
            try:
                appt_date = pd.to_datetime(appt_date_raw).date()
            except Exception:
                appt_date = date.today()

            sched_date_raw = row.get("scheduled_date")
            try:
                sched_date = pd.to_datetime(sched_date_raw).date()
            except Exception:
                sched_date = appt_date

            lead_days = int(row.get("lead_days", max(0, (appt_date - sched_date).days)))
            lead_days = max(0, lead_days)

            sms_received      = _parse_bool(row.get("sms_received", False))
            prev_no_shows     = int(float(row.get("previous_no_shows", 0)))
            wait_minutes      = int(float(row.get("wait_minutes", random.randint(5, 60))))
            status            = _parse_status(row.get("status", "Showed"))
            time_slot         = str(row.get("time_slot", f"{random.randint(8,17):02d}:{'00' if random.random() > 0.5 else '30'}"))

            # ---- department / doctor ----
            dept_name = str(row.get("department", random.choice(DEPARTMENTS))).strip()
            if dept_name not in DEPARTMENTS:
                dept_name = random.choice(DEPARTMENTS)
            dept = _get_or_create_dept(db, dept_name)

            doc_name = str(row.get("doctor", random.choice(DOCTORS_BY_DEPT[dept_name]))).strip()
            doctor = _get_or_create_doctor(db, doc_name, dept.id)

            # ---- risk score ----
            rs = compute_risk_score(
                previous_no_shows=prev_no_shows, lead_days=lead_days,
                sms_received=sms_received, scholarship=scholarship,
                alcoholism=alcoholism, age=patient.age,
            )

            appt = Appointment(
                patient_id=patient.id,
                department_id=dept.id,
                doctor_id=doctor.id,
                appointment_date=appt_date,
                time_slot=time_slot,
                scheduled_date=sched_date,
                lead_days=lead_days,
                sms_received=sms_received,
                previous_no_shows=prev_no_shows,
                wait_minutes=wait_minutes,
                status=status,
                risk_score=rs,
                risk_label=get_risk_label(rs),
            )
            db.add(appt)
            inserted += 1

        except Exception as e:
            skipped += 1
            if len(errors) < 5:
                errors.append(f"Row {idx}: {e}")

    db.commit()
    return {
        "success": True,
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
    }
