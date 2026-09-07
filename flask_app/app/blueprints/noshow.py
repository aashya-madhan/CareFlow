import json
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.services import analytics as svc

noshow_bp = Blueprint("noshow", __name__, url_prefix="/noshow")


@noshow_bp.route("/")
@login_required
def index():
    year = request.args.get("year", "all")
    uid  = current_user.id

    if not svc.has_data(uid):
        return render_template("shared/no_data.html",
                               page_title="No-Show Analysis", year=year)

    kpi          = svc.get_kpi_summary(year, uid)
    dept_chart   = svc.get_dept_chart(year, uid)
    sms_chart    = svc.get_sms_chart(year, uid)
    age_chart    = svc.get_age_group_chart(year, uid)
    gender_chart = svc.get_gender_chart(year, uid)
    dow_chart    = svc.get_dow_chart(year, uid)
    lead_chart   = svc.get_lead_time_chart(year, uid)
    prev_chart   = svc.get_prev_noshow_chart(year, uid)

    return render_template(
        "noshow/index.html",
        year=year, kpi=kpi,
        dept_chart=json.dumps(dept_chart),
        sms_chart=json.dumps(sms_chart),
        age_chart=json.dumps(age_chart),
        gender_chart=json.dumps(gender_chart),
        dow_chart=json.dumps(dow_chart),
        lead_chart=json.dumps(lead_chart),
        prev_chart=json.dumps(prev_chart),
    )


@noshow_bp.route("/filter")
@login_required
def filter_data():
    year = request.args.get("year", "all")
    uid  = current_user.id
    return jsonify(dict(
        kpi=svc.get_kpi_summary(year, uid),
        dept_chart=svc.get_dept_chart(year, uid),
        sms_chart=svc.get_sms_chart(year, uid),
        age_chart=svc.get_age_group_chart(year, uid),
        gender_chart=svc.get_gender_chart(year, uid),
        dow_chart=svc.get_dow_chart(year, uid),
        lead_chart=svc.get_lead_time_chart(year, uid),
        prev_chart=svc.get_prev_noshow_chart(year, uid),
    ))
