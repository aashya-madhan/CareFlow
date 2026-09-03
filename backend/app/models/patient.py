from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id            = Column(Integer, primary_key=True, index=True)
    patient_code  = Column(String(50), unique=True, index=True, nullable=False)
    full_name     = Column(String(255), nullable=False, index=True)
    age           = Column(Integer, nullable=False)
    gender        = Column(String(10), nullable=False)   # Male | Female
    neighbourhood = Column(String(150))
    scholarship   = Column(Boolean, default=False)
    hypertension  = Column(Boolean, default=False)
    diabetes      = Column(Boolean, default=False)
    alcoholism    = Column(Boolean, default=False)
    handicap      = Column(Boolean, default=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    appointments = relationship("Appointment", back_populates="patient")
