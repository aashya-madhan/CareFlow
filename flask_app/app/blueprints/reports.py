import csv
import io
from flask import Blueprint, render_template, request, Response, stream_with_context
from flask_login import login_required, current_user
from app.services.analytics import get_export_rows

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

REPORT_META = {
    "summary":    {"title": "Executive Summary",        "icon": "fa-file-lines",        "color": "blue"},
    "noshow":     {"title": "No-Show Detail Report",    "icon": "fa-user-xmark",        "color": "red"},
    "department": {"title": "Department Performance",   "icon": "fa-building-columns",  "color": "green"},
    "doctor":     {"title": "Doctor Workload Report",   "icon": "fa-user-tie",          "color": "purple"},
    "full":       {"title": "Full Appointments Dataset","icon": "fa-database",          "color": "teal"},
}


@reports_bp.route("/")
@login_required
def index():
    year = request.args.get("year", "all")
    return render_template("reports/index.html", year=year, reports=REPORT_META)


@reports_bp.route("/export/<report_type>")
@login_required
def export(report_type: str):
    if report_type not in REPORT_META:
        return "Invalid report type", 400

    year    = request.args.get("year", "all")
    uid     = current_user.id
    headers, rows = get_export_rows(report_type, year, uid)

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        yield buf.getvalue(); buf.seek(0); buf.truncate()
        for row in rows:
            writer.writerow(row)
            yield buf.getvalue(); buf.seek(0); buf.truncate()

    filename = f"hospital_{report_type}_report.csv"
    return Response(
        stream_with_context(generate()),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
