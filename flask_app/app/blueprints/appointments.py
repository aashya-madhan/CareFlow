from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash, jsonify)
from flask_login import login_required, current_user
from app.extensions import db
from app.models.appointment import Appointment
from app.models.patient     import Patient
from app.models.department  import Department
from app.models.doctor      import Doctor
from app.services.risk      import compute_risk_score, get_risk_label
from app.services.analytics import get_appointments_page

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")


@appointments_bp.route("/")
@login_required
def index():
    page    = request.args.get("page",    1,     type=int)
    search  = request.args.get("search",  "")
    status  = request.args.get("status",  "all")
    dept_id = request.args.get("dept_id", None,  type=int)
    year    = request.args.get("year",    "all")

    data    = get_appointments_page(page=page, per_page=15,
                                    search=search, status=status,
                                    dept_id=dept_id, year=year,
                                    user_id=current_user.id)
    departments = Department.query.order_by(Department.name).all()

    return render_template("appointments/index.html",
                           data=data, departments=departments,
                           search=search, status=status,
                           dept_id=dept_id, year=year)


@appointments_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    departments = Department.query.order_by(Department.name).all()
    patients    = Patient.query.order_by(Patient.full_name).all()
    doctors     = Doctor.query.order_by(Doctor.name).all()

    if request.method == "POST":
        try:
            patient    = Patient.query.get_or_404(int(request.form["patient_id"]))
            dept       = Department.query.get_or_404(int(request.form["department_id"]))
            doctor     = Doctor.query.get_or_404(int(request.form["doctor_id"]))

            from datetime import date as dt
            appt_date  = dt.fromisoformat(request.form["appointment_date"])
            lead_days  = int(request.form.get("lead_days", 0))
            prev_ns    = int(request.form.get("previous_no_shows", 0))
            wait_min   = int(request.form.get("wait_minutes", 0))
            sms        = "sms_received" in request.form
            status_val = request.form.get("status", "Scheduled")
            time_slot  = request.form.get("time_slot") or None
            notes      = request.form.get("notes") or None

            rs = compute_risk_score(
                previous_no_shows=prev_ns, lead_days=lead_days,
                sms_received=sms, scholarship=patient.scholarship,
                alcoholism=patient.alcoholism, age=patient.age,
            )

            appt = Appointment(
                patient_id=patient.id, department_id=dept.id,
                doctor_id=doctor.id, appointment_date=appt_date,
                time_slot=time_slot, lead_days=lead_days,
                sms_received=sms, previous_no_shows=prev_ns,
                wait_minutes=wait_min, status=status_val,
                risk_score=rs, risk_label=get_risk_label(rs),
                notes=notes,
                uploaded_by=current_user.id,
            )
            db.session.add(appt)
            db.session.commit()
            flash("Appointment created successfully.", "success")
            return redirect(url_for("appointments.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template("appointments/form.html",
                           action="new", appt=None,
                           departments=departments,
                           patients=patients, doctors=doctors)


@appointments_bp.route("/<int:appt_id>/edit", methods=["GET", "POST"])
@login_required
def edit(appt_id):
    appt        = Appointment.query.get_or_404(appt_id)
    departments = Department.query.order_by(Department.name).all()
    patients    = Patient.query.order_by(Patient.full_name).all()
    doctors     = Doctor.query.order_by(Doctor.name).all()

    if request.method == "POST":
        try:
            from datetime import date as dt
            appt.patient_id    = int(request.form["patient_id"])
            appt.department_id = int(request.form["department_id"])
            appt.doctor_id     = int(request.form["doctor_id"])
            appt.appointment_date = dt.fromisoformat(request.form["appointment_date"])
            appt.lead_days     = int(request.form.get("lead_days", 0))
            appt.previous_no_shows = int(request.form.get("previous_no_shows", 0))
            appt.wait_minutes  = int(request.form.get("wait_minutes", 0))
            appt.sms_received  = "sms_received" in request.form
            appt.status        = request.form.get("status", appt.status)
            appt.time_slot     = request.form.get("time_slot") or None
            appt.notes         = request.form.get("notes") or None

            patient = Patient.query.get(appt.patient_id)
            if patient:
                rs = compute_risk_score(
                    previous_no_shows=appt.previous_no_shows,
                    lead_days=appt.lead_days,
                    sms_received=appt.sms_received,
                    scholarship=patient.scholarship,
                    alcoholism=patient.alcoholism, age=patient.age,
                )
                appt.risk_score = rs
                appt.risk_label = get_risk_label(rs)

            db.session.commit()
            flash("Appointment updated.", "success")
            return redirect(url_for("appointments.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {e}", "danger")

    return render_template("appointments/form.html",
                           action="edit", appt=appt,
                           departments=departments,
                           patients=patients, doctors=doctors)


@appointments_bp.route("/<int:appt_id>/delete", methods=["POST"])
@login_required
def delete(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    db.session.delete(appt)
    db.session.commit()
    flash("Appointment deleted.", "success")
    return redirect(url_for("appointments.index"))


# AJAX: doctors for a given department
@appointments_bp.route("/doctors/<int:dept_id>")
@login_required
def doctors_for_dept(dept_id):
    doctors = Doctor.query.filter_by(department_id=dept_id)\
                          .order_by(Doctor.name).all()
    return jsonify([{"id": d.id, "name": d.name} for d in doctors])
