from app.extensions import db
from datetime import datetime


class Appointment(db.Model):
    __tablename__ = "appointments"

    id                = db.Column(db.Integer,     primary_key=True)
    patient_id        = db.Column(db.Integer,     db.ForeignKey("patients.id"),    nullable=False, index=True)
    department_id     = db.Column(db.Integer,     db.ForeignKey("departments.id"), nullable=False, index=True)
    doctor_id         = db.Column(db.Integer,     db.ForeignKey("doctors.id"),     nullable=False, index=True)

    # Every row is owned by the user who imported/created it
    uploaded_by       = db.Column(db.Integer,     db.ForeignKey("users.id"),       nullable=True,  index=True)

    appointment_date  = db.Column(db.Date,        nullable=False, index=True)
    time_slot         = db.Column(db.String(10))
    scheduled_date    = db.Column(db.Date)
    lead_days         = db.Column(db.Integer,  default=0)
    sms_received      = db.Column(db.Boolean,  default=False)
    previous_no_shows = db.Column(db.Integer,  default=0)
    wait_minutes      = db.Column(db.Integer,  default=0)
    status            = db.Column(db.String(20), default="Scheduled", index=True)
    risk_score        = db.Column(db.Integer,  default=0)
    risk_label        = db.Column(db.String(10), default="Low")
    notes             = db.Column(db.Text)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    patient    = db.relationship("Patient",    back_populates="appointments")
    department = db.relationship("Department", back_populates="appointments")
    doctor     = db.relationship("Doctor",     back_populates="appointments")
    owner      = db.relationship("User",       foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<Appointment {self.id} user={self.uploaded_by} {self.status}>"
