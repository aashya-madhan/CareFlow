from app.extensions import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    id            = db.Column(db.Integer,     primary_key=True)
    name          = db.Column(db.String(150), nullable=False, index=True)
    department_id = db.Column(db.Integer,     db.ForeignKey("departments.id"), nullable=False)

    department   = db.relationship("Department", back_populates="doctors")
    appointments = db.relationship("Appointment", back_populates="doctor", lazy="dynamic")

    def __repr__(self):
        return f"<Doctor {self.name}>"
