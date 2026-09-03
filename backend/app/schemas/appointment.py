from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class AppointmentCreate(BaseModel):
    patient_id: int
    department_id: int
    doctor_id: int
    appointment_date: date
    time_slot: Optional[str] = None
    scheduled_date: Optional[date] = None
    lead_days: int = 0
    sms_received: bool = False
    previous_no_shows: int = 0
    wait_minutes: int = 0
    status: str = "Scheduled"
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    patient_id: Optional[int] = None
    department_id: Optional[int] = None
    doctor_id: Optional[int] = None
    appointment_date: Optional[date] = None
    time_slot: Optional[str] = None
    scheduled_date: Optional[date] = None
    lead_days: Optional[int] = None
    sms_received: Optional[bool] = None
    previous_no_shows: Optional[int] = None
    wait_minutes: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    department_id: int
    doctor_id: int
    appointment_date: date
    time_slot: Optional[str] = None
    lead_days: int
    sms_received: bool
    previous_no_shows: int
    wait_minutes: int
    status: str
    risk_score: int
    risk_label: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    # Nested names for frontend
    patient_name: Optional[str] = None
    patient_code: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    department_name: Optional[str] = None
    doctor_name: Optional[str] = None

    model_config = {"from_attributes": True}


class AppointmentListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    items: list[AppointmentOut]
