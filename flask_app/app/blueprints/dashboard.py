import json
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.services import analytics as svc

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    year = request.args.get("year", "all")
    uid  = current_user.id

    # If the user has no data yet, render an empty-state page
    if not svc.has_data(uid):
        return render_template("dashboard/empty.html", year=year)

    kpi              = svc.get_kpi_summary(year, uid)
    monthly_chart    = svc.get_monthly_chart(year, uid)
    attendance_chart = svc.get_attendance_chart(year, uid)
    dept_chart       = svc.get_dept_chart(year, uid)
    dow_chart        = svc.get_dow_chart(year, uid)
    risk_chart       = svc.get_risk_factors_chart(year, uid)
    recent           = svc.get_appointments_page(page=1, per_page=10, year=year, user_id=uid)

    return render_template(
        "dashboard/index.html",
        year=year,
        kpi=kpi,
        monthly_chart=json.dumps(monthly_chart),
        attendance_chart=json.dumps(attendance_chart),
        dept_chart=json.dumps(dept_chart),
        dow_chart=json.dumps(dow_chart),
        risk_chart=json.dumps(risk_chart),
        recent=recent,
    )
