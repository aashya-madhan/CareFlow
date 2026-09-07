"""Seed departments, doctors, and admin user on first run."""
from app.extensions import db
from app.models.user       import User
from app.models.department import Department
from app.models.doctor     import Doctor


DEPARTMENTS = [
    "Cardiology", "Orthopedics", "Neurology", "Pediatrics",
    "General Medicine", "Dermatology", "Gynecology",
    "Ophthalmology", "Psychiatry", "ENT",
]

DOCTORS = {
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


def run_seed(app):
    with app.app_context():
        # Admin user
        if not User.query.filter_by(email=app.config["ADMIN_EMAIL"]).first():
            admin = User(
                email=app.config["ADMIN_EMAIL"],
                full_name=app.config["ADMIN_NAME"],
                role="admin",
                is_active=True,
            )
            admin.set_password(app.config["ADMIN_PASSWORD"])
            db.session.add(admin)

        # Departments
        for name in DEPARTMENTS:
            if not Department.query.filter_by(name=name).first():
                db.session.add(Department(name=name))
        db.session.flush()

        # Doctors
        for dept_name, doc_list in DOCTORS.items():
            dept = Department.query.filter_by(name=dept_name).first()
            if dept:
                for doc_name in doc_list:
                    if not Doctor.query.filter_by(name=doc_name).first():
                        db.session.add(Doctor(name=doc_name, department_id=dept.id))

        db.session.commit()
        print("[seed] Admin, departments and doctors ready.")
