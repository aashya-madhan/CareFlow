import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services import analytics as svc

operational_bp = Blueprint("operational", __name__, url_prefix="/operational")


@operational_bp.route("/")
@login_required
def index():
    year = request.args.get("year", "all")
    uid  = current_user.id

    if not svc.has_data(uid):
        return render_template("shared/no_data.html",
                               page_title="Operational Analysis", year=year)

    kpi            = svc.get_kpi_summary(year, uid)
    monthly_chart  = svc.get_monthly_chart(year, uid)
    dept_stats     = svc.get_dept_stats(year, uid)
    doctor_chart   = svc.get_doctor_chart(year, uid)
    capacity_chart = svc.get_capacity_chart(year, uid)
    dow_chart      = svc.get_dow_chart(year, uid)
    wait_chart     = svc.get_dept_chart(year, uid)

    return render_template(
        "operational/index.html",
        year=year, kpi=kpi,
        monthly_chart=json.dumps(monthly_chart),
        dept_stats=dept_stats,
        doctor_chart=json.dumps(doctor_chart),
        capacity_chart=json.dumps(capacity_chart),
        dow_chart=json.dumps(dow_chart),
        wait_chart=json.dumps(wait_chart),
    )


@operational_bp.route("/filter")
@login_required
def filter_data():
    year = request.args.get("year", "all")
    uid  = current_user.id
    return jsonify(dict(
        kpi=svc.get_kpi_summary(year, uid),
        monthly_chart=svc.get_monthly_chart(year, uid),
        doctor_chart=svc.get_doctor_chart(year, uid),
        capacity_chart=svc.get_capacity_chart(year, uid),
        dow_chart=svc.get_dow_chart(year, uid),
        dept_stats=svc.get_dept_stats(year, uid),
    ))
