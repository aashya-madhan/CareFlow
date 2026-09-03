from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(150), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    department   = relationship("Department", back_populates="doctors")
    appointments = relationship("Appointment", back_populates="doctor")
