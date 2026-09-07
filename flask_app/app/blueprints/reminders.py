from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import date, timedelta
from sqlalchemy import func, case
from app.extensions import db
from app.models.appointment import Appointment
from app.models.patient     import Patient
from app.models.department  import Department
from app.models.doctor      import Doctor

reminders_bp = Blueprint("reminders", __name__, url_prefix="/reminders")


def _get_upcoming(days_ahead: int = 7, user_id: int = 0):
    today     = date.today()
    cutoff    = today + timedelta(days=days_ahead)
    return (
        Appointment.query
        .join(Patient,    Appointment.patient_id    == Patient.id)
        .join(Department, Appointment.department_id == Department.id)
        .join(Doctor,     Appointment.doctor_id     == Doctor.id)
        .filter(
            Appointment.uploaded_by == user_id,
            Appointment.status == "Scheduled",
            Appointment.appointment_date >= today,
            Appointment.appointment_date <= cutoff,
        )
        .order_by(Appointment.appointment_date.asc())
        .all()
    )


def _get_reminder_stats(user_id: int = 0):
    today    = date.today()
    tomorrow = today + timedelta(days=1)
    week     = today + timedelta(days=7)

    base = Appointment.query.filter(
        Appointment.uploaded_by == user_id,
        Appointment.status == "Scheduled",
        Appointment.appointment_date >= today,
    )
    total_upcoming = base.count()
    due_today      = base.filter(Appointment.appointment_date == today).count()
    due_tomorrow   = Appointment.query.filter(
        Appointment.uploaded_by == user_id,
        Appointment.status == "Scheduled",
        Appointment.appointment_date == tomorrow,
    ).count()
    due_this_week  = Appointment.query.filter(
        Appointment.uploaded_by == user_id,
        Appointment.status == "Scheduled",
        Appointment.appointment_date > today,
        Appointment.appointment_date <= week,
    ).count()
    no_sms = Appointment.query.filter(
        Appointment.uploaded_by == user_id,
        Appointment.status == "Scheduled",
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= week,
        Appointment.sms_received == False,
    ).count()
    high_risk = Appointment.query.filter(
        Appointment.uploaded_by == user_id,
        Appointment.status == "Scheduled",
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= week,
        Appointment.risk_label == "High",
    ).count()
    return dict(
        total_upcoming=total_upcoming, due_today=due_today,
        due_tomorrow=due_tomorrow, due_this_week=due_this_week,
        no_sms=no_sms, high_risk=high_risk,
    )


@reminders_bp.route("/")
@login_required
def index():
    days   = request.args.get("days", 7, type=int)
    days   = max(1, min(days, 30))          # clamp 1-30
    filter_risk = request.args.get("risk", "all")
    filter_sms  = request.args.get("sms",  "all")

    appts  = _get_upcoming(days, current_user.id)

    if filter_risk != "all":
        appts = [a for a in appts if a.risk_label == filter_risk]
    if filter_sms == "no":
        appts = [a for a in appts if not a.sms_received]
    elif filter_sms == "yes":
        appts = [a for a in appts if a.sms_received]

    stats  = _get_reminder_stats(current_user.id)
    today  = date.today()
    return render_template(
        "reminders/index.html",
        appts=appts,
        stats=stats,
        days=days,
        filter_risk=filter_risk,
        filter_sms=filter_sms,
        today=today,
    )


@reminders_bp.route("/mark-sent/<int:appt_id>", methods=["POST"])
@login_required
def mark_sms_sent(appt_id):
    """Mark an appointment's SMS reminder as sent."""
    appt = Appointment.query.get_or_404(appt_id)
    appt.sms_received = True
    db.session.commit()
    flash(f"SMS marked as sent for appointment #{appt_id}.", "success")
    return redirect(request.referrer or url_for("reminders.index"))


@reminders_bp.route("/api/upcoming")
@login_required
def api_upcoming():
    today  = date.today()
    cutoff = today + timedelta(days=1)
    count  = Appointment.query.filter(
        Appointment.uploaded_by == current_user.id,
        Appointment.status == "Scheduled",
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= cutoff,
    ).count()
    return jsonify({"due_soon": count})
