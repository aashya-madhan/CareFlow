from app.extensions import db
from datetime import datetime


class Patient(db.Model):
    __tablename__ = "patients"

    id            = db.Column(db.Integer,     primary_key=True)
    patient_code  = db.Column(db.String(50),  unique=True, nullable=False, index=True)
    full_name     = db.Column(db.String(255), nullable=False, index=True)
    age           = db.Column(db.Integer,     nullable=False)
    gender        = db.Column(db.String(10),  nullable=False)
    neighbourhood = db.Column(db.String(150))
    scholarship   = db.Column(db.Boolean, default=False)
    hypertension  = db.Column(db.Boolean, default=False)
    diabetes      = db.Column(db.Boolean, default=False)
    alcoholism    = db.Column(db.Boolean, default=False)
    handicap      = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    appointments = db.relationship("Appointment", back_populates="patient", lazy="dynamic")

    @property
    def age_group(self) -> str:
        if self.age <= 17:  return "0-17"
        if self.age <= 35:  return "18-35"
        if self.age <= 55:  return "36-55"
        return "56+"

    def __repr__(self):
        return f"<Patient {self.patient_code} {self.full_name}>"
