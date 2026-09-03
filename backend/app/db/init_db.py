from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.core.config import settings
from app.models.user import User
from app.models.department import Department
from app.models.doctor import Doctor


DEPARTMENTS = [
    "Cardiology", "Orthopedics", "Neurology", "Pediatrics",
    "General Medicine", "Dermatology", "Gynecology",
    "Ophthalmology", "Psychiatry", "ENT",
]

DOCTORS = {
    "Cardiology":       ["Dr. Smith", "Dr. Patel", "Dr. Chen"],
    "Orthopedics":      ["Dr. Johnson", "Dr. Williams", "Dr. Brown"],
    "Neurology":        ["Dr. Davis", "Dr. Martinez", "Dr. Wilson"],
    "Pediatrics":       ["Dr. Anderson", "Dr. Taylor", "Dr. Thomas"],
    "General Medicine": ["Dr. Jackson", "Dr. White", "Dr. Harris"],
    "Dermatology":      ["Dr. Martin", "Dr. Thompson", "Dr. Garcia"],
    "Gynecology":       ["Dr. Nguyen", "Dr. Lewis", "Dr. Lee"],
    "Ophthalmology":    ["Dr. Walker", "Dr. Hall", "Dr. Allen"],
    "Psychiatry":       ["Dr. Young", "Dr. Hernandez", "Dr. King"],
    "ENT":              ["Dr. Wright", "Dr. Lopez", "Dr. Hill"],
}


def init_db(db: Session) -> None:
    # Create admin user
    admin = db.query(User).filter(User.email == settings.FIRST_ADMIN_EMAIL).first()
    if not admin:
        db.add(User(
            email=settings.FIRST_ADMIN_EMAIL,
            hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
            full_name=settings.FIRST_ADMIN_NAME,
            role="admin",
            is_active=True,
        ))

    # Seed departments
    for name in DEPARTMENTS:
        if not db.query(Department).filter(Department.name == name).first():
            db.add(Department(name=name))
    db.flush()

    # Seed doctors
    for dept_name, doc_list in DOCTORS.items():
        dept = db.query(Department).filter(Department.name == dept_name).first()
        if dept:
            for doc_name in doc_list:
                if not db.query(Doctor).filter(Doctor.name == doc_name).first():
                    db.add(Doctor(name=doc_name, department_id=dept.id))

    db.commit()
