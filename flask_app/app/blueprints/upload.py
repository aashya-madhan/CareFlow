from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.services.csv_import import import_csv
from app.extensions import db
from app.models.appointment import Appointment
from app.models.patient import Patient

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")

ALLOWED = {"csv"}


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


@upload_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    result = None

    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file or file.filename == "":
            flash("No file selected.", "warning")
        elif not _allowed(file.filename):
            flash("Only CSV files are accepted.", "danger")
        else:
            data = file.read()
            if len(data) > 150 * 1024 * 1024:
                flash("File too large (max 150 MB).", "danger")
            else:
                # Every row is stamped with the current user's id
                result = import_csv(data, user_id=current_user.id)
                if result["success"]:
                    flash(
                        f"Import complete: {result['inserted']:,} records inserted, "
                        f"{result['skipped']} skipped.",
                        "success",
                    )
                else:
                    flash(f"Import failed: {result.get('error')}", "danger")

    return render_template("upload/index.html", result=result)


@upload_bp.route("/clear", methods=["POST"])
@login_required
def clear_data():
    """Delete all appointments and orphaned patients for the current user."""
    uid = current_user.id

    # Delete this user's appointments
    appt_count = Appointment.query.filter_by(uploaded_by=uid).delete(synchronize_session=False)
    db.session.flush()  # apply deletions so the orphan check below sees the updated state

    # Delete patients who now have zero appointments from any user
    orphan_ids = (
        db.session.query(Patient.id)
        .outerjoin(Appointment, Appointment.patient_id == Patient.id)
        .filter(Appointment.id.is_(None))
        .all()
    )
    patient_count = 0
    if orphan_ids:
        ids = [r[0] for r in orphan_ids]
        patient_count = Patient.query.filter(Patient.id.in_(ids)).delete(synchronize_session=False)

    db.session.commit()
    flash(
        f"All your data has been cleared — "
        f"{appt_count:,} appointments and {patient_count:,} patients removed.",
        "success",
    )
    return redirect(url_for("upload.index"))
