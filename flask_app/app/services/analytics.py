"""Analytics service - per-user scoped SQL aggregations."""
import calendar
from sqlalchemy import func, case, extract, Numeric, cast
from app.extensions import db
from app.models.appointment import Appointment
from app.models.patient     import Patient
from app.models.department  import Department
from app.models.doctor      import Doctor


def _year_filter(q, year):
    if not year or year == "all":
        return q
    m = {"2024":(2024,1,12),"2023":(2023,1,12),"q1":(2024,1,3),
         "q2":(2024,4,6),"q3":(2024,7,9),"q4":(2024,10,12)}
    if year not in m:
        return q
    yr, lo, hi = m[year]
    return q.filter(extract("year", Appointment.appointment_date) == yr,
                    extract("month", Appointment.appointment_date).between(lo, hi))


def _rate(part, total):
    return round(part / total * 100, 1) if total else 0.0


def has_data(user_id):
    return Appointment.query.filter(
        Appointment.uploaded_by == user_id).first() is not None


def get_kpi_summary(year="all", user_id=0):
    q = _year_filter(db.session.query(
        func.count().label("total"),
        func.sum(case((Appointment.status == "Showed",    1), else_=0)).label("showed"),
        func.sum(case((Appointment.status == "No-Show",   1), else_=0)).label("no_show"),
        func.sum(case((Appointment.status == "Cancelled", 1), else_=0)).label("cancelled"),
        func.sum(case((Appointment.status == "Scheduled", 1), else_=0)).label("scheduled"),
        func.sum(case((Appointment.sms_received == True,  1), else_=0)).label("sms_total"),
        func.sum(case((Appointment.sms_received == False, 1), else_=0)).label("nosms_total"),
        func.sum(case(((Appointment.sms_received == True)  & (Appointment.status == "No-Show"), 1), else_=0)).label("sms_ns"),
        func.sum(case(((Appointment.sms_received == False) & (Appointment.status == "No-Show"), 1), else_=0)).label("nosms_ns"),
        func.sum(case((Appointment.risk_label == "High",  1), else_=0)).label("high_risk"),
        func.round(cast(func.avg(Appointment.wait_minutes), Numeric(10, 2)), 1).label("avg_wait"),
        func.round(cast(func.avg(Appointment.lead_days),    Numeric(10, 2)), 1).label("avg_lead"),
    ).filter(Appointment.uploaded_by == user_id), year)
    r = q.one(); t = r.total or 0
    return dict(total=t, showed=r.showed or 0, no_show=r.no_show or 0,
                cancelled=r.cancelled or 0, scheduled=r.scheduled or 0,
                no_show_rate=_rate(r.no_show or 0, t),
                attendance_rate=_rate(r.showed or 0, t),
                avg_wait=float(r.avg_wait or 0), avg_lead=float(r.avg_lead or 0),
                sms_no_show_rate=_rate(r.sms_ns or 0, r.sms_total or 0),
                no_sms_no_show_rate=_rate(r.nosms_ns or 0, r.nosms_total or 0),
                high_risk=r.high_risk or 0,
                high_risk_pct=_rate(r.high_risk or 0, t))


def get_monthly_chart(year="all", user_id=0):
    q = _year_filter(db.session.query(
        extract("year",  Appointment.appointment_date).label("yr"),
        extract("month", Appointment.appointment_date).label("mo"),
        func.count().label("total"),
        func.sum(case((Appointment.status == "Showed",  1), else_=0)).label("showed"),
        func.sum(case((Appointment.status == "No-Show", 1), else_=0)).label("no_show"),
    ).filter(Appointment.uploaded_by == user_id)
     .group_by("yr", "mo").order_by("yr", "mo"), year)
    rows = q.all()
    return dict(
        labels=[f"{calendar.month_abbr[int(r.mo)]} {int(r.yr)}" for r in rows],
        showed=[int(r.showed) for r in rows],
        no_show=[int(r.no_show) for r in rows],
        totals=[int(r.total) for r in rows],
        rates=[_rate(int(r.no_show), int(r.total)) for r in rows])


def get_dept_stats(year="all", user_id=0):
    q = _year_filter(db.session.query(
        Department.name.label("dept"),
        func.count().label("total"),
        func.sum(case((Appointment.status == "Showed",    1), else_=0)).label("showed"),
        func.sum(case((Appointment.status == "No-Show",   1), else_=0)).label("no_show"),
        func.sum(case((Appointment.status == "Cancelled", 1), else_=0)).label("cancelled"),
        func.round(cast(func.avg(Appointment.wait_minutes), Numeric(10, 2)), 1).label("avg_wait"),
    ).filter(Appointment.uploaded_by == user_id)
     .join(Department, Appointment.department_id == Department.id)
     .group_by(Department.name).order_by(Department.name), year)
    return [dict(department=r.dept, total=r.total, showed=r.showed or 0,
                 no_show=r.no_show or 0, cancelled=r.cancelled or 0,
                 no_show_rate=_rate(r.no_show or 0, r.total),
                 avg_wait=float(r.avg_wait or 0)) for r in q.all()]


def get_dept_chart(year="all", user_id=0):
    s = get_dept_stats(year, user_id)
    return dict(labels=[x["department"] for x in s], totals=[x["total"] for x in s],
                no_show=[x["no_show"] for x in s], rates=[x["no_show_rate"] for x in s],
                avg_wait=[x["avg_wait"] for x in s])


def get_doctor_stats(year="all", user_id=0):
    q = _year_filter(db.session.query(
        Doctor.name.label("doctor"), Department.name.label("dept"),
        func.count().label("total"),
        func.sum(case((Appointment.status == "Showed",  1), else_=0)).label("showed"),
        func.sum(case((Appointment.status == "No-Show", 1), else_=0)).label("no_show"),
        func.round(cast(func.avg(Appointment.wait_minutes), Numeric(10, 2)), 1).label("avg_wait"),
    ).filter(Appointment.uploaded_by == user_id)
     .join(Doctor,     Appointment.doctor_id     == Doctor.id)
     .join(Department, Appointment.department_id == Department.id)
     .group_by(Doctor.name, Department.name).order_by(func.count().desc()), year)
    return [dict(doctor=r.doctor, department=r.dept, total=r.total,
                 showed=r.showed or 0, no_show=r.no_show or 0,
                 no_show_rate=_rate(r.no_show or 0, r.total),
                 avg_wait=float(r.avg_wait or 0)) for r in q.all()]


def get_doctor_chart(year="all", user_id=0):
    s = get_doctor_stats(year, user_id)[:12]
    return dict(labels=[x["doctor"].replace("Dr. ", "") for x in s],
                totals=[x["total"] for x in s], no_show=[x["no_show"] for x in s],
                rates=[x["no_show_rate"] for x in s])


def get_age_group_chart(year="all", user_id=0):
    ae = case((Patient.age <= 17, "0-17"), (Patient.age <= 35, "18-35"),
              (Patient.age <= 55, "36-55"), else_="56+")
    q = _year_filter(db.session.query(ae.label("grp"), func.count().label("total"),
        func.sum(case((Appointment.status == "No-Show", 1), else_=0)).label("no_show"))
        .select_from(Appointment).join(Patient, Appointment.patient_id == Patient.id)
        .filter(Appointment.uploaded_by == user_id).group_by("grp"), year)
    rows = {r.grp: r for r in q.all()}
    g = ["0-17", "18-35", "36-55", "56+"]
    t = [int(rows[x].total)   if x in rows else 0 for x in g]
    n = [int(rows[x].no_show) if x in rows else 0 for x in g]
    return dict(labels=g, totals=t, no_show=n,
                rates=[_rate(n[i], t[i]) for i in range(4)])


def get_dow_chart(year="all", user_id=0):
    q = _year_filter(db.session.query(
        func.to_char(Appointment.appointment_date, "Dy").label("dow"),
        func.count().label("total"),
        func.sum(case((Appointment.status == "No-Show", 1), else_=0)).label("no_show"))
        .filter(Appointment.uploaded_by == user_id).group_by("dow"), year)
    rows = {r.dow: r for r in q.all()}
    d = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    t = [int(rows[x].total)   if x in rows else 0 for x in d]
    n = [int(rows[x].no_show) if x in rows else 0 for x in d]
    return dict(labels=d, totals=t, no_show=n,
                rates=[_rate(n[i], t[i]) for i in range(7)])


def get_sms_chart(year="all", user_id=0):
    q = _year_filter(db.session.query(
        Appointment.sms_received.label("sms"), func.count().label("total"),
        func.sum(case((Appointment.status == "No-Show", 1), else_=0)).label("no_show"))
        .filter(Appointment.uploaded_by == user_id)
        .group_by(Appointment.sms_received), year)
    rows = {r.sms: r for r in q.all()}
    s = rows.get(True); ns = rows.get(False)
    sr = _rate(int(s.no_show)  if s  else 0, int(s.total)  if s  else 0)
    nr = _rate(int(ns.no_show) if ns else 0, int(ns.total) if ns else 0)
    return dict(labels=["SMS Sent", "No SMS"], rates=[sr, nr],
                totals=[int(s.total) if s else 0, int(ns.total) if ns else 0],
                no_show=[int(s.no_show) if s else 0, int(ns.no_show) if ns else 0],
                sms_rate=sr, nosms_rate=nr)


def get_lead_time_chart(year="all", user_id=0):
    be = case((Appointment.lead_days <= 7,  "0-7d"),
              (Appointment.lead_days <= 14, "8-14d"),
              (Appointment.lead_days <= 30, "15-30d"),
              (Appointment.lead_days <= 45, "31-45d"), else_="46-60d")
    q = _year_filter(db.session.query(be.label("bucket"), func.count().label("total"),
        func.sum(case((Appointment.status == "No-Show", 1), else_=0)).label("no_show"))
        .filter(Appointment.uploaded_by == user_id).group_by("bucket"), year)
    rows = {r.bucket: r for r in q.all()}
    o = ["0-7d", "8-14d", "15-30d", "31-45d", "46-60d"]
    t = [int(rows[b].total)   if b in rows else 0 for b in o]
    n = [int(rows[b].no_show) if b in rows else 0 for b in o]
    return dict(labels=o, totals=t, no_show=n,
                rates=[_rate(n[i], t[i]) for i in range(5)])


def get_risk_factors_chart(year="all", user_id=0):
    q = _year_filter(db.session.query(
        func.sum(case((Appointment.sms_received == False,   1), else_=0)).label("no_sms"),
        func.sum(case((Appointment.previous_no_shows >= 3,  1), else_=0)).label("prev3"),
        func.sum(case((Appointment.lead_days > 30,          1), else_=0)).label("lead30"),
        func.sum(case((Patient.scholarship == True,         1), else_=0)).label("scholar"),
        func.sum(case((Patient.alcoholism  == True,         1), else_=0)).label("alcohol"),
        func.sum(case(((Patient.age >= 18) & (Patient.age <= 35), 1), else_=0)).label("age1835"),
    ).select_from(Appointment).join(Patient, Appointment.patient_id == Patient.id)
     .filter(Appointment.uploaded_by == user_id)
     .filter(Appointment.status == "No-Show"), year)
    r = q.one()
    f = {"No SMS": int(r.no_sms or 0), "3+ Prev No-Shows": int(r.prev3 or 0),
         "Lead > 30d": int(r.lead30 or 0), "Scholarship": int(r.scholar or 0),
         "Alcoholism": int(r.alcohol or 0), "Age 18-35": int(r.age1835 or 0)}
    sf = sorted(f.items(), key=lambda x: -x[1])
    return dict(labels=[x[0] for x in sf], values=[x[1] for x in sf])


def get_attendance_chart(year="all", user_id=0):
    k = get_kpi_summary(year, user_id)
    return dict(labels=["Showed", "No-Show", "Cancelled"],
                values=[k["showed"], k["no_show"], k["cancelled"]],
                colors=["#16a34a", "#dc2626", "#ca8a04"])


def get_prev_noshow_chart(year="all", user_id=0):
    q = _year_filter(db.session.query(
        Appointment.previous_no_shows.label("prev"),
        func.count().label("total"),
        func.sum(case((Appointment.status == "No-Show", 1), else_=0)).label("no_show"))
        .filter(Appointment.uploaded_by == user_id)
        .filter(Appointment.previous_no_shows <= 4)
        .group_by(Appointment.previous_no_shows)
        .order_by(Appointment.previous_no_shows), year)
    rows = {int(r.prev): r for r in q.all()}
    t = [int(rows[i].total)   if i in rows else 0 for i in range(5)]
    n = [int(rows[i].no_show) if i in rows else 0 for i in range(5)]
    return dict(labels=["0 prev","1 prev","2 prev","3 prev","4 prev"],
                totals=t, no_show=n,
                rates=[_rate(n[i], t[i]) for i in range(5)])


def get_gender_chart(year="all", user_id=0):
    q = _year_filter(db.session.query(
        Patient.gender.label("g"), func.count().label("total"),
        func.sum(case((Appointment.status == "No-Show", 1), else_=0)).label("no_show"))
        .select_from(Appointment).join(Patient, Appointment.patient_id == Patient.id)
        .filter(Appointment.uploaded_by == user_id).group_by(Patient.gender), year)
    rows = {r.g: r for r in q.all()}
    m = rows.get("Male"); f = rows.get("Female")
    mv = int(m.total)   if m else 0; fv = int(f.total)   if f else 0
    mn = int(m.no_show) if m else 0; fn = int(f.no_show) if f else 0
    return dict(labels=["Male","Female"], values=[mv, fv],
                no_show=[mn, fn], rates=[_rate(mn, mv), _rate(fn, fv)])


def get_neighbourhood_chart(year="all", user_id=0):
    q = _year_filter(db.session.query(
        Patient.neighbourhood.label("n"), func.count().label("cnt"))
        .select_from(Appointment).join(Patient, Appointment.patient_id == Patient.id)
        .filter(Appointment.uploaded_by == user_id)
        .group_by(Patient.neighbourhood).order_by(func.count().desc()).limit(10), year)
    rows = q.all()
    return dict(labels=[r.n or "Unknown" for r in rows],
                values=[int(r.cnt) for r in rows])


def get_condition_chart(year="all", user_id=0):
    q = _year_filter(db.session.query(
        func.sum(case((Patient.hypertension == True,  1), else_=0)).label("h_with"),
        func.sum(case((Patient.hypertension == False, 1), else_=0)).label("h_wo"),
        func.sum(case(((Patient.hypertension == True)  & (Appointment.status == "No-Show"), 1), else_=0)).label("h_ns_w"),
        func.sum(case(((Patient.hypertension == False) & (Appointment.status == "No-Show"), 1), else_=0)).label("h_ns_wo"),
        func.sum(case((Patient.diabetes == True,  1), else_=0)).label("d_with"),
        func.sum(case((Patient.diabetes == False, 1), else_=0)).label("d_wo"),
        func.sum(case(((Patient.diabetes == True)  & (Appointment.status == "No-Show"), 1), else_=0)).label("d_ns_w"),
        func.sum(case(((Patient.diabetes == False) & (Appointment.status == "No-Show"), 1), else_=0)).label("d_ns_wo"),
        func.sum(case((Patient.alcoholism == True,  1), else_=0)).label("a_with"),
        func.sum(case((Patient.alcoholism == False, 1), else_=0)).label("a_wo"),
        func.sum(case(((Patient.alcoholism == True)  & (Appointment.status == "No-Show"), 1), else_=0)).label("a_ns_w"),
        func.sum(case(((Patient.alcoholism == False) & (Appointment.status == "No-Show"), 1), else_=0)).label("a_ns_wo"),
        func.sum(case((Patient.handicap == True,  1), else_=0)).label("hc_with"),
        func.sum(case((Patient.handicap == False, 1), else_=0)).label("hc_wo"),
        func.sum(case(((Patient.handicap == True)  & (Appointment.status == "No-Show"), 1), else_=0)).label("hc_ns_w"),
        func.sum(case(((Patient.handicap == False) & (Appointment.status == "No-Show"), 1), else_=0)).label("hc_ns_wo"),
    ).select_from(Appointment).join(Patient, Appointment.patient_id == Patient.id)
     .filter(Appointment.uploaded_by == user_id), year)
    r = q.one()
    def w(ns, tot): return _rate(int(ns or 0), int(tot or 0))
    return dict(
        labels=["Hypertension","Diabetes","Alcoholism","Disability"],
        with_rate=[w(r.h_ns_w, r.h_with), w(r.d_ns_w, r.d_with),
                   w(r.a_ns_w, r.a_with), w(r.hc_ns_w, r.hc_with)],
        without_rate=[w(r.h_ns_wo, r.h_wo), w(r.d_ns_wo, r.d_wo),
                      w(r.a_ns_wo, r.a_wo), w(r.hc_ns_wo, r.hc_wo)])


def get_capacity_chart(year="all", user_id=0):
    s = get_dept_stats(year, user_id)
    if not s:
        return dict(labels=[], values=[], colors=[])
    mx = max(x["total"] for x in s) or 1
    cap = [min(99, round(x["total"] / mx * 90 + 10)) for x in s]
    colors = ["#dc2626" if c >= 85 else "#ca8a04" if c >= 70 else "#16a34a" for c in cap]
    return dict(labels=[x["department"] for x in s], values=cap, colors=colors)


def get_loyalty_chart(year="all", user_id=0):
    sub = _year_filter(db.session.query(
        Appointment.patient_id.label("pid"), func.count().label("visits"))
        .filter(Appointment.uploaded_by == user_id)
        .group_by(Appointment.patient_id), year).subquery()
    fe = case((sub.c.visits == 1, "1 visit"), (sub.c.visits <= 3, "2-3 visits"),
              (sub.c.visits <= 5, "4-5 visits"), else_="6+ visits")
    rows = {r.freq: int(r.cnt) for r in
            db.session.query(fe.label("freq"), func.count().label("cnt"))
            .group_by("freq").all()}
    o = ["1 visit","2-3 visits","4-5 visits","6+ visits"]
    return dict(labels=o, values=[rows.get(l, 0) for l in o],
                colors=["#dc2626","#ca8a04","#2563eb","#16a34a"])


def get_appointments_page(page=1, per_page=15, search="", status="",
                           dept_id=None, year="all", user_id=0):
    q = Appointment.query.filter(Appointment.uploaded_by == user_id)\
        .join(Patient,    Appointment.patient_id    == Patient.id)\
        .join(Department, Appointment.department_id == Department.id)\
        .join(Doctor,     Appointment.doctor_id     == Doctor.id)
    q = _year_filter(q, year)
    if search:
        q = q.filter(db.or_(Patient.full_name.ilike(f"%{search}%"),
                             Patient.patient_code.ilike(f"%{search}%")))
    if status and status != "all":
        q = q.filter(Appointment.status == status)
    if dept_id:
        q = q.filter(Appointment.department_id == dept_id)
    total = q.count()
    pg = q.order_by(Appointment.appointment_date.desc())\
           .paginate(page=page, per_page=per_page, error_out=False)
    rows = [dict(
        id=a.id, patient_name=a.patient.full_name, patient_code=a.patient.patient_code,
        patient_age=a.patient.age, patient_gender=a.patient.gender,
        department=a.department.name, doctor=a.doctor.name,
        appointment_date=str(a.appointment_date), time_slot=a.time_slot or "--",
        sms_received=a.sms_received, previous_no_shows=a.previous_no_shows,
        lead_days=a.lead_days, wait_minutes=a.wait_minutes, status=a.status,
        risk_score=a.risk_score, risk_label=a.risk_label, notes=a.notes or "",
    ) for a in pg.items]
    return dict(rows=rows, total=total, page=page, per_page=per_page,
                pages=pg.pages, has_prev=pg.has_prev, has_next=pg.has_next)


def get_export_rows(report_type, year="all", user_id=0):
    if report_type == "summary":
        kpi = get_kpi_summary(year, user_id)
        depts = get_dept_stats(year, user_id)
        headers = ["Metric", "Value"]
        rows = [["Total Appointments", kpi["total"]], ["Showed", kpi["showed"]],
                ["No-Show", kpi["no_show"]], ["Cancelled", kpi["cancelled"]],
                ["No-Show Rate (%)", kpi["no_show_rate"]],
                ["Attendance Rate (%)", kpi["attendance_rate"]],
                ["Avg Wait Time (min)", kpi["avg_wait"]], ["Avg Lead Days", kpi["avg_lead"]],
                ["SMS No-Show Rate (%)", kpi["sms_no_show_rate"]],
                ["No-SMS No-Show Rate (%)", kpi["no_sms_no_show_rate"]],
                ["High Risk Count", kpi["high_risk"]], [],
                ["Department", "No-Show Rate (%)"]]
        rows += [[d["department"], d["no_show_rate"]] for d in depts]
        return headers, rows
    bq = Appointment.query.filter(Appointment.uploaded_by == user_id)\
         .join(Patient).join(Department).join(Doctor)
    q = _year_filter(bq, year)
    if report_type == "noshow":
        rdb = q.filter(Appointment.status == "No-Show").all()
        headers = ["ID","Patient Code","Patient Name","Age","Gender","Department",
                   "Doctor","Date","Lead Days","SMS","Prev No-Shows","Risk Score","Risk Level"]
        rows = [[a.id,a.patient.patient_code,a.patient.full_name,a.patient.age,
                 a.patient.gender,a.department.name,a.doctor.name,a.appointment_date,
                 a.lead_days,"Yes" if a.sms_received else "No",
                 a.previous_no_shows,a.risk_score,a.risk_label] for a in rdb]
        return headers, rows
    elif report_type == "department":
        s = get_dept_stats(year, user_id)
        headers = ["Department","Total","Showed","No-Show","Cancelled","No-Show Rate (%)","Avg Wait (min)"]
        return headers, [[x["department"],x["total"],x["showed"],x["no_show"],
                          x["cancelled"],x["no_show_rate"],x["avg_wait"]] for x in s]
    elif report_type == "doctor":
        s = get_doctor_stats(year, user_id)
        headers = ["Doctor","Department","Total","Showed","No-Show","No-Show Rate (%)","Avg Wait (min)"]
        return headers, [[x["doctor"],x["department"],x["total"],x["showed"],
                          x["no_show"],x["no_show_rate"],x["avg_wait"]] for x in s]
    elif report_type == "full":
        rdb = q.order_by(Appointment.appointment_date.desc()).all()
        headers = ["ID","Patient Code","Patient Name","Age","Gender","Neighbourhood",
                   "Scholarship","Hypertension","Diabetes","Alcoholism","Disability",
                   "Department","Doctor","Date","Time Slot","Lead Days","SMS",
                   "Prev No-Shows","Wait Min","Status","Risk Score","Risk Level"]
        rows = [[a.id,a.patient.patient_code,a.patient.full_name,a.patient.age,
                 a.patient.gender,a.patient.neighbourhood,a.patient.scholarship,
                 a.patient.hypertension,a.patient.diabetes,a.patient.alcoholism,
                 a.patient.handicap,a.department.name,a.doctor.name,a.appointment_date,
                 a.time_slot or "",a.lead_days,"Yes" if a.sms_received else "No",
                 a.previous_no_shows,a.wait_minutes,a.status,a.risk_score,a.risk_label]
                for a in rdb]
        return headers, rows
    return [], []
