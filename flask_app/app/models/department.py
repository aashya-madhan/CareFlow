from app.extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id   = db.Column(db.Integer,     primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)

    doctors      = db.relationship("Doctor",      back_populates="department", lazy="dynamic")
    appointments = db.relationship("Appointment", back_populates="department", lazy="dynamic")

    def __repr__(self):
        return f"<Department {self.name}>"
