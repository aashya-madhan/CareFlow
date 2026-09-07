import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY          = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/hospital_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED    = True
    MAX_CONTENT_LENGTH  = 150 * 1024 * 1024   # 150 MB max upload
    ADMIN_EMAIL         = os.getenv("ADMIN_EMAIL",    "admin@hospital.com")
    ADMIN_PASSWORD      = os.getenv("ADMIN_PASSWORD", "Admin@123")
    ADMIN_NAME          = os.getenv("ADMIN_NAME",     "System Admin")
