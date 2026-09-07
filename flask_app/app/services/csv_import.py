"""
CSV import service — handles Kaggle Medical No-Show dataset
and any flexible CSV format with auto column mapping.
"""
import io
import re
import random
from datetime import date

import pandas as pd

from app.extensions       import db
from app.models.patient    import Patient
from app.models.department import Department
from app.models.doctor     import Doctor
from app.models.appointment import Appointment
from app.services.risk      import compute_risk_score, get_risk_label

# ── column name normaliser map ───────────────────────────────────────────────
COLUMN_MAP = {
    "patientid": "patient_code", "patient_id": "patient_code",
    "name": "full_name", "patient_name": "full_name", "full_name": "full_name",
    "age": "age", "gender": "gender", "sex": "gender",
    "neighbourhood": "neighbourhood", "neighborhood": "neighbourhood",
    "scholarship": "scholarship",
    "hipertension": "hypertension", "hypertension": "hypertension",
    "diabetes": "diabetes", "alcoholism": "alcoholism",
    "handcap": "handicap", "handicap": "handicap", "disability": "handicap",
    "scheduledday": "scheduled_date", "scheduled_date": "scheduled_date",
    "appointmentday": "appointment_date", "appointment_date": "appointment_date",
    "no_show": "status", "noshow": "status", "status": "status",
    "sms_received": "sms_received", "smssent": "sms_received",
    "sms_sent": "sms_received", "sms received": "sms_received",
    "department": "department", "doctor": "doctor",
    "wait_minutes": "wait_minutes", "waitminutes": "wait_minutes",
    "lead_days": "lead_days", "leaddays": "lead_days",
    "previous_no_shows": "previous_no_shows",
    "previousnoshow": "previous_no_shows",
    "time_slot": "time_slot", "timeslot": "time_slot",
}

DEPARTMENTS = [
    "Cardiology", "Orthopedics", "Neurology", "Pediatrics",
    "General Medicine", "Dermatology", "Gynecology",
    "Ophthalmology", "Psychiatry", "ENT",
]

DOCTORS_BY_DEPT = {
    "Cardiology":       ["Dr. Smith",    "Dr. Patel",     "Dr. Chen"],
    "Orthopedics":      ["Dr. Johnson",  "Dr. Williams",  "Dr. Brown"],
    "Neurology":        ["Dr. Davis",    "Dr. Martinez",  "Dr. Wilson"],
    "Pediatrics":       ["Dr. Anderson", "Dr. Taylor",    "Dr. Thomas"],
    "General Medicine": ["Dr. Jackson",  "Dr. White",     "Dr. Harris"],
    "Dermatology":      ["Dr. Martin",   "Dr. Thompson",  "Dr. Garcia"],
    "Gynecology":       ["Dr. Nguyen",   "Dr. Lewis",     "Dr. Lee"],
    "Ophthalmology":    ["Dr. Walker",   "Dr. Hall",      "Dr. Allen"],
    "Psychiatry":       ["Dr. Young",    "Dr. Hernandez", "Dr. King"],
    "ENT":              ["Dr. Wright",   "Dr. Lopez",     "Dr. Hill"],
}


def _normalise_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [re.sub(r"[\s\-]", "_", c).lower().strip() for c in df.columns]
    return df.rename(columns={c: COLUMN_MAP[c] for c in df.columns if c in COLUMN_MAP})


def _parse_bool(val) -> bool:
    if isinstance(val, bool): return val
    if isinstance(val, (int, float)): return bool(int(val))
    return str(val).strip().lower() in ("1", "yes", "true", "y", "sim")


def _parse_status(val) -> str:
    s = str(val).strip().lower()
    if s in ("yes", "1", "true", "no-show", "noshow"): return "No-Show"
    if s in ("no",  "0", "false", "showed", "show"):   return "Showed"
    if s in ("cancelled", "canceled"):                  return "Cancelled"
    return "Showed"


def _get_or_create(model, **kwargs):
    obj = model.query.filter_by(**kwargs).first()
    if not obj:
        obj = model(**kwargs)
        db.session.add(obj)
        db.session.flush()
    return obj


def import_csv(file_bytes: bytes, user_id: int) -> dict:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        return {"success": False, "error": str(e), "inserted": 0, "skipped": 0}

    df       = _normalise_cols(df)
    inserted = skipped = 0
    errors   = []

    for idx, row in df.iterrows():
        try:
            p_code     = str(row.get("patient_code", f"P{idx+1000}")).strip()
            full_name  = str(row.get("full_name",   f"Patient {p_code}")).strip()
            age        = max(0, min(120, int(float(row.get("age", 30)))))
            gender_raw = str(row.get("gender", "Male")).strip().lower()
            gender     = "Female" if gender_raw in ("f", "female", "feminino") else "Male"
            neighbourhood = str(row.get("neighbourhood", "Unknown")).strip()

            # upsert patient
            patient = Patient.query.filter_by(patient_code=p_code).first()
            if not patient:
                patient = Patient(
                    patient_code=p_code, full_name=full_name,
                    age=age, gender=gender, neighbourhood=neighbourhood,
                    scholarship=_parse_bool(row.get("scholarship",  False)),
                    hypertension=_parse_bool(row.get("hypertension", False)),
                    diabetes=_parse_bool(row.get("diabetes",   False)),
                    alcoholism=_parse_bool(row.get("alcoholism", False)),
                    handicap=_parse_bool(row.get("handicap",   False)),
                )
                db.session.add(patient)
                db.session.flush()

            # dates
            try:
                appt_date  = pd.to_datetime(row.get("appointment_date")).date()
            except Exception:
                appt_date  = date.today()
            try:
                sched_date = pd.to_datetime(row.get("scheduled_date")).date()
            except Exception:
                sched_date = appt_date

            lead_days = max(0, int(row.get("lead_days",
                           max(0, (appt_date - sched_date).days))))

            sms_received      = _parse_bool(row.get("sms_received",      False))
            prev_no_shows     = int(float(row.get("previous_no_shows",   0)))
            wait_minutes      = int(float(row.get("wait_minutes",
                                random.randint(5, 60))))
            status            = _parse_status(row.get("status", "Showed"))
            time_slot         = str(row.get("time_slot",
                                f"{random.randint(8,17):02d}:{'00' if random.random()>.5 else '30'}"))

            # department / doctor
            dept_name = str(row.get("department", random.choice(DEPARTMENTS))).strip()
            if dept_name not in DEPARTMENTS:
                dept_name = random.choice(DEPARTMENTS)
            dept   = _get_or_create(Department, name=dept_name)
            doc_name = str(row.get("doctor",
                          random.choice(DOCTORS_BY_DEPT[dept_name]))).strip()
            doctor = _get_or_create(Doctor, name=doc_name, department_id=dept.id)

            rs = compute_risk_score(
                previous_no_shows=prev_no_shows, lead_days=lead_days,
                sms_received=sms_received,
                scholarship=patient.scholarship,
                alcoholism=patient.alcoholism,
                age=patient.age,
            )

            db.session.add(Appointment(
                patient_id=patient.id, department_id=dept.id,
                doctor_id=doctor.id, appointment_date=appt_date,
                time_slot=time_slot, scheduled_date=sched_date,
                lead_days=lead_days, sms_received=sms_received,
                previous_no_shows=prev_no_shows,
                wait_minutes=wait_minutes, status=status,
                risk_score=rs, risk_label=get_risk_label(rs),
                uploaded_by=user_id,
            ))
            inserted += 1

            # commit in batches of 500 for performance
            if inserted % 500 == 0:
                db.session.commit()

        except Exception as e:
            skipped += 1
            if len(errors) < 5:
                errors.append(f"Row {idx}: {e}")

    db.session.commit()
    return {"success": True, "inserted": inserted,
            "skipped": skipped, "errors": errors}
