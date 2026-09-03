from sqlalchemy import (
    Column, Integer, String, Boolean, Date, DateTime,
    ForeignKey, Float, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id                 = Column(Integer, primary_key=True, index=True)
    patient_id         = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    department_id      = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    doctor_id          = Column(Integer, ForeignKey("doctors.id"), nullable=False, index=True)

    appointment_date   = Column(Date, nullable=False, index=True)
    time_slot          = Column(String(10))           # e.g. "09:30"
    scheduled_date     = Column(Date)
    lead_days          = Column(Integer, default=0)

    sms_received       = Column(Boolean, default=False)
    previous_no_shows  = Column(Integer, default=0)
    wait_minutes       = Column(Integer, default=0)

    status             = Column(String(20), default="Scheduled", index=True)
    # Scheduled | Showed | No-Show | Cancelled

    risk_score         = Column(Integer, default=0)
    risk_label         = Column(String(10), default="Low")  # Low | Medium | High

    notes              = Column(Text)

    created_at         = Column(DateTime(timezone=True), server_default=func.now())
    updated_at         = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient    = relationship("Patient",    back_populates="appointments")
    department = relationship("Department", back_populates="appointments")
    doctor     = relationship("Doctor",     back_populates="appointments")

    __table_args__ = (
        Index("ix_appt_date_status", "appointment_date", "status"),
        Index("ix_appt_dept_status", "department_id",    "status"),
    )
