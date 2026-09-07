from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id              = db.Column(db.Integer,     primary_key=True)
    email           = db.Column(db.String(255), unique=True, nullable=False, index=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    full_name       = db.Column(db.String(255), nullable=False)
    role            = db.Column(db.String(50),  nullable=False, default="staff")  # admin | staff
    is_active       = db.Column(db.Boolean,     nullable=False, default=True)
    created_at      = db.Column(db.DateTime,    default=datetime.utcnow)

    def set_password(self, password: str):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.hashed_password, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self):
        return f"<User {self.email}>"
