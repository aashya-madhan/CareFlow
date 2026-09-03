from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import os

from app.db.session import engine, SessionLocal
from app.db.base import Base
from app.db.init_db import init_db
from app.api.routes import auth, appointments, analytics, patients, departments, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    Base.metadata.create_all(bind=engine)
    # Seed initial data
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Hospital Appointment Analytics API",
    description="No-Show & Operational Analysis — FastAPI + PostgreSQL",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the frontend (file:// or localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router,         prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(analytics.router,    prefix="/api")
app.include_router(patients.router,     prefix="/api")
app.include_router(departments.router,  prefix="/api")
app.include_router(upload.router,       prefix="/api")

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
if os.path.isdir(frontend_path):
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_path, "css"), html=False), name="css")
    app.mount("/js",     StaticFiles(directory=os.path.join(frontend_path, "js"),  html=False), name="js")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path: str):
        file_path = os.path.join(frontend_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "version": "1.0.0"}
