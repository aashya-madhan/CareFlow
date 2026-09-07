import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.patient     import Patient
from app.models.appointment import Appointment
from app.services.patients  import get_patient_profile

patients_bp = Blueprint("patients", __name__, url_prefix="/patients")


@patients_bp.route("/")
@login_required
def index():
    """Searchable patient list — scoped to the current user's uploaded data."""
    from flask_login import current_user
    search = request.args.get("search", "")
    page   = request.args.get("page", 1, type=int)

    # Only show patients who have at least one appointment uploaded by this user
    q = Patient.query.join(
        Appointment, Appointment.patient_id == Patient.id
    ).filter(
        Appointment.uploaded_by == current_user.id
    ).distinct()

    if search:
        q = q.filter(
            db.or_(
                Patient.full_name.ilike(f"%{search}%"),
                Patient.patient_code.ilike(f"%{search}%"),
            )
        )
    pagination = q.order_by(Patient.full_name).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template(
        "patients/index.html",
        patients=pagination.items,
        pagination=pagination,
        search=search,
    )


@patients_bp.route("/<int:patient_id>")
@login_required
def profile(patient_id):
    """Full patient profile page."""
    patient = Patient.query.get_or_404(patient_id)
    data    = get_patient_profile(patient_id)

    return render_template(
        "patients/profile.html",
        patient=patient,
        data=data,
        history_chart=json.dumps(data["history_chart"]),
        risk_trend=json.dumps(data["risk_trend"]),
    )
