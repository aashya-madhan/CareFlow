import json
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.services import analytics as svc

demographics_bp = Blueprint("demographics", __name__, url_prefix="/demographics")


@demographics_bp.route("/")
@login_required
def index():
    year = request.args.get("year", "all")
    uid  = current_user.id

    if not svc.has_data(uid):
        return render_template("shared/no_data.html",
                               page_title="Patient Demographics", year=year)

    kpi                 = svc.get_kpi_summary(year, uid)
    age_chart           = svc.get_age_group_chart(year, uid)
    gender_chart        = svc.get_gender_chart(year, uid)
    neighbourhood_chart = svc.get_neighbourhood_chart(year, uid)
    condition_chart     = svc.get_condition_chart(year, uid)
    loyalty_chart       = svc.get_loyalty_chart(year, uid)
    sms_chart           = svc.get_sms_chart(year, uid)

    return render_template(
        "demographics/index.html",
        year=year, kpi=kpi,
        age_chart=json.dumps(age_chart),
        gender_chart=json.dumps(gender_chart),
        neighbourhood_chart=json.dumps(neighbourhood_chart),
        condition_chart=json.dumps(condition_chart),
        loyalty_chart=json.dumps(loyalty_chart),
        sms_chart=json.dumps(sms_chart),
    )
