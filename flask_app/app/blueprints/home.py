from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from app.models.appointment import Appointment
from app.models.patient     import Patient
from app.models.department  import Department

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
@home_bp.route("/home")
def index():
    # Redirect logged-in users straight to dashboard
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    # Live headline stats (cheap COUNT queries — no auth needed)
    total_appts   = Appointment.query.count()
    total_patients = Patient.query.count()
    total_depts   = Department.query.count()
    noshow_count  = Appointment.query.filter_by(status="No-Show").count()
    noshow_rate   = round(noshow_count / total_appts * 100, 1) if total_appts else 0

    return render_template(
        "home/index.html",
        total_appts=total_appts,
        total_patients=total_patients,
        total_depts=total_depts,
        noshow_rate=noshow_rate,
    )
