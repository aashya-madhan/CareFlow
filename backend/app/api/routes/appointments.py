from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from typing import Optional
from math import ceil

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentOut, AppointmentListResponse
from app.services.risk import compute_risk_score, get_risk_label

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _enrich(appt: Appointment) -> AppointmentOut:
    out = AppointmentOut.model_validate(appt)
    if appt.patient:
        out.patient_name   = appt.patient.full_name
        out.patient_code   = appt.patient.patient_code
        out.patient_age    = appt.patient.age
        out.patient_gender = appt.patient.gender
    if appt.department:
        out.department_name = appt.department.name
    if appt.doctor:
        out.doctor_name = appt.doctor.name
    return out


@router.get("", response_model=AppointmentListResponse)
def list_appointments(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    department_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    year: Optional[str] = None,
    risk_label: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Appointment).options(
        joinedload(Appointment.patient),
        joinedload(Appointment.department),
        joinedload(Appointment.doctor),
    )

    if search:
        q = q.join(Patient).filter(
            or_(
                Patient.full_name.ilike(f"%{search}%"),
                Patient.patient_code.ilike(f"%{search}%"),
            )
        )
    if status and status != "all":
        q = q.filter(Appointment.status == status)
    if department_id:
        q = q.filter(Appointment.department_id == department_id)
    if doctor_id:
        q = q.filter(Appointment.doctor_id == doctor_id)
    if risk_label:
        q = q.filter(Appointment.risk_label == risk_label)
    if year and year != "all":
        from sqlalchemy import extract
        if year == "2024":
            q = q.filter(extract("year", Appointment.appointment_date) == 2024)
        elif year == "2023":
            q = q.filter(extract("year", Appointment.appointment_date) == 2023)
        elif year.startswith("q"):
            quarters = {"q1": (1,3), "q2": (4,6), "q3": (7,9), "q4": (10,12)}
            lo, hi = quarters.get(year, (1, 12))
            q = q.filter(
                extract("year", Appointment.appointment_date) == 2024,
                extract("month", Appointment.appointment_date).between(lo, hi),
            )

    total = q.count()
    items = q.order_by(Appointment.appointment_date.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return AppointmentListResponse(
        total=total, page=page, per_page=per_page,
        pages=ceil(total / per_page) if total else 1,
        items=[_enrich(a) for a in items],
    )


@router.post("", response_model=AppointmentOut, status_code=201)
def create_appointment(
    body: AppointmentCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == body.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not db.query(Department).filter(Department.id == body.department_id).first():
        raise HTTPException(status_code=404, detail="Department not found")
    if not db.query(Doctor).filter(Doctor.id == body.doctor_id).first():
        raise HTTPException(status_code=404, detail="Doctor not found")

    rs = compute_risk_score(
        previous_no_shows=body.previous_no_shows,
        lead_days=body.lead_days,
        sms_received=body.sms_received,
        scholarship=patient.scholarship,
        alcoholism=patient.alcoholism,
        age=patient.age,
    )

    appt = Appointment(**body.model_dump(), risk_score=rs, risk_label=get_risk_label(rs))
    db.add(appt)
    db.commit()
    db.refresh(appt)

    db.refresh(appt, ["patient", "department", "doctor"])
    return _enrich(appt)


@router.get("/{appt_id}", response_model=AppointmentOut)
def get_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    appt = db.query(Appointment).options(
        joinedload(Appointment.patient),
        joinedload(Appointment.department),
        joinedload(Appointment.doctor),
    ).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return _enrich(appt)


@router.put("/{appt_id}", response_model=AppointmentOut)
def update_appointment(
    appt_id: int,
    body: AppointmentUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    appt = db.query(Appointment).options(
        joinedload(Appointment.patient),
        joinedload(Appointment.department),
        joinedload(Appointment.doctor),
    ).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(appt, field, val)

    patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
    if patient:
        appt.risk_score = compute_risk_score(
            previous_no_shows=appt.previous_no_shows,
            lead_days=appt.lead_days,
            sms_received=appt.sms_received,
            scholarship=patient.scholarship,
            alcoholism=patient.alcoholism,
            age=patient.age,
        )
        appt.risk_label = get_risk_label(appt.risk_score)

    db.commit()
    db.refresh(appt)
    return _enrich(appt)


@router.delete("/{appt_id}", status_code=204)
def delete_appointment(
    appt_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appt)
    db.commit()
