from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.department import Department
from app.models.doctor import Doctor
from app.schemas.analytics import (
    KPISummary, DeptStat, DoctorStat, MonthlyBucket,
    AgeGroupStat, DowStat, RiskFactor, SmsImpact, LeadTimeBucket,
)
from typing import Optional
import calendar


def _base_query(db: Session, year: Optional[str] = None):
    q = db.query(Appointment)
    if year and year != "all":
        if year == "2024":
            q = q.filter(extract("year", Appointment.appointment_date) == 2024)
        elif year == "2023":
            q = q.filter(extract("year", Appointment.appointment_date) == 2023)
        elif year == "q1":
            q = q.filter(
                extract("year",  Appointment.appointment_date) == 2024,
                extract("month", Appointment.appointment_date) <= 3,
            )
        elif year == "q2":
            q = q.filter(
                extract("year",  Appointment.appointment_date) == 2024,
                extract("month", Appointment.appointment_date).between(4, 6),
            )
        elif year == "q3":
            q = q.filter(
                extract("year",  Appointment.appointment_date) == 2024,
                extract("month", Appointment.appointment_date).between(7, 9),
            )
        elif year == "q4":
            q = q.filter(
                extract("year",  Appointment.appointment_date) == 2024,
                extract("month", Appointment.appointment_date) >= 10,
            )
    return q


def get_kpi_summary(db: Session, year: Optional[str] = None) -> KPISummary:
    q = _base_query(db, year)
    rows = q.all()

    total     = len(rows)
    showed    = sum(1 for r in rows if r.status == "Showed")
    no_show   = sum(1 for r in rows if r.status == "No-Show")
    cancelled = sum(1 for r in rows if r.status == "Cancelled")
    scheduled = sum(1 for r in rows if r.status == "Scheduled")

    no_show_rate    = round(no_show   / total * 100, 1) if total else 0
    attendance_rate = round(showed    / total * 100, 1) if total else 0
    avg_wait  = round(sum(r.wait_minutes for r in rows) / total, 1) if total else 0
    avg_lead  = round(sum(r.lead_days   for r in rows) / total, 1) if total else 0

    sms_rows     = [r for r in rows if r.sms_received]
    no_sms_rows  = [r for r in rows if not r.sms_received]
    sms_ns_rate  = round(sum(1 for r in sms_rows    if r.status == "No-Show") / len(sms_rows)   * 100, 1) if sms_rows   else 0
    nsms_ns_rate = round(sum(1 for r in no_sms_rows if r.status == "No-Show") / len(no_sms_rows) * 100, 1) if no_sms_rows else 0

    high_risk = sum(1 for r in rows if r.risk_label == "High")

    return KPISummary(
        total=total, showed=showed, no_show=no_show,
        cancelled=cancelled, scheduled=scheduled,
        no_show_rate=no_show_rate, attendance_rate=attendance_rate,
        avg_wait_minutes=avg_wait, avg_lead_days=avg_lead,
        sms_no_show_rate=sms_ns_rate, no_sms_no_show_rate=nsms_ns_rate,
        high_risk_count=high_risk,
    )


def get_dept_stats(db: Session, year: Optional[str] = None) -> list[DeptStat]:
    q = _base_query(db, year).join(Department)
    rows = q.all()

    grouped: dict[str, list] = {}
    for r in rows:
        name = r.department.name
        grouped.setdefault(name, []).append(r)

    result = []
    for dept, appts in sorted(grouped.items()):
        total  = len(appts)
        showed = sum(1 for a in appts if a.status == "Showed")
        ns     = sum(1 for a in appts if a.status == "No-Show")
        canc   = sum(1 for a in appts if a.status == "Cancelled")
        rate   = round(ns / total * 100, 1) if total else 0
        avg_w  = round(sum(a.wait_minutes for a in appts) / total, 1) if total else 0
        result.append(DeptStat(
            department=dept, total=total, showed=showed,
            no_show=ns, cancelled=canc, no_show_rate=rate, avg_wait=avg_w,
        ))
    return result


def get_doctor_stats(db: Session, year: Optional[str] = None) -> list[DoctorStat]:
    q = _base_query(db, year).join(Doctor).join(Department)
    rows = q.all()

    grouped: dict[str, list] = {}
    for r in rows:
        grouped.setdefault(r.doctor.name, []).append(r)

    result = []
    for doc, appts in sorted(grouped.items()):
        total  = len(appts)
        showed = sum(1 for a in appts if a.status == "Showed")
        ns     = sum(1 for a in appts if a.status == "No-Show")
        rate   = round(ns / total * 100, 1) if total else 0
        avg_w  = round(sum(a.wait_minutes for a in appts) / total, 1) if total else 0
        dept   = appts[0].doctor.department.name if appts else ""
        result.append(DoctorStat(
            doctor=doc, department=dept, total=total,
            showed=showed, no_show=ns, no_show_rate=rate, avg_wait=avg_w,
        ))
    return sorted(result, key=lambda x: x.total, reverse=True)


def get_monthly_buckets(db: Session, year: Optional[str] = None) -> list[MonthlyBucket]:
    q = _base_query(db, year)
    rows = q.all()

    grouped: dict[tuple, list] = {}
    for r in rows:
        key = (r.appointment_date.year, r.appointment_date.month)
        grouped.setdefault(key, []).append(r)

    result = []
    for (y, m), appts in sorted(grouped.items()):
        total  = len(appts)
        showed = sum(1 for a in appts if a.status == "Showed")
        ns     = sum(1 for a in appts if a.status == "No-Show")
        rate   = round(ns / total * 100, 1) if total else 0
        label  = f"{calendar.month_abbr[m]} {y}"
        result.append(MonthlyBucket(
            label=label, year=y, month=m,
            total=total, showed=showed, no_show=ns, no_show_rate=rate,
        ))
    return result


def get_age_group_stats(db: Session, year: Optional[str] = None) -> list[AgeGroupStat]:
    q = _base_query(db, year).join(Patient)
    rows = q.all()

    def age_group(age: int) -> str:
        if age <= 17: return "0-17"
        if age <= 35: return "18-35"
        if age <= 55: return "36-55"
        return "56+"

    grouped: dict[str, list] = {}
    for r in rows:
        key = age_group(r.patient.age)
        grouped.setdefault(key, []).append(r)

    result = []
    for g in ["0-17", "18-35", "36-55", "56+"]:
        appts = grouped.get(g, [])
        total = len(appts)
        ns    = sum(1 for a in appts if a.status == "No-Show")
        rate  = round(ns / total * 100, 1) if total else 0
        result.append(AgeGroupStat(age_group=g, total=total, no_show=ns, no_show_rate=rate))
    return result


def get_dow_stats(db: Session, year: Optional[str] = None) -> list[DowStat]:
    import datetime as dt
    q = _base_query(db, year)
    rows = q.all()

    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    grouped: dict[str, list] = {d: [] for d in days}
    for r in rows:
        dow = r.appointment_date.strftime("%a")
        if dow in grouped:
            grouped[dow].append(r)

    result = []
    for day in days:
        appts = grouped[day]
        total = len(appts)
        ns    = sum(1 for a in appts if a.status == "No-Show")
        rate  = round(ns / total * 100, 1) if total else 0
        result.append(DowStat(day=day, total=total, no_show=ns, no_show_rate=rate))
    return result


def get_risk_factors(db: Session, year: Optional[str] = None) -> list[RiskFactor]:
    q = _base_query(db, year).join(Patient).filter(Appointment.status == "No-Show")
    rows = q.all()

    factors = {
        "No SMS":            sum(1 for r in rows if not r.sms_received),
        "3+ Prev No-Shows":  sum(1 for r in rows if r.previous_no_shows >= 3),
        "Lead > 30d":        sum(1 for r in rows if r.lead_days > 30),
        "Scholarship":       sum(1 for r in rows if r.patient.scholarship),
        "Alcoholism":        sum(1 for r in rows if r.patient.alcoholism),
        "Age 18-35":         sum(1 for r in rows if 18 <= r.patient.age <= 35),
    }
    return sorted(
        [RiskFactor(factor=k, no_show_count=v) for k, v in factors.items()],
        key=lambda x: x.no_show_count, reverse=True,
    )


def get_sms_impact(db: Session, year: Optional[str] = None) -> SmsImpact:
    q = _base_query(db, year)
    rows = q.all()
    sms   = [r for r in rows if r.sms_received]
    no_s  = [r for r in rows if not r.sms_received]
    sr    = round(sum(1 for r in sms  if r.status == "No-Show") / len(sms)  * 100, 1) if sms  else 0
    nr    = round(sum(1 for r in no_s if r.status == "No-Show") / len(no_s) * 100, 1) if no_s else 0
    return SmsImpact(sms_sent_rate=sr, no_sms_rate=nr, sms_total=len(sms), no_sms_total=len(no_s))


def get_lead_time_stats(db: Session, year: Optional[str] = None) -> list[LeadTimeBucket]:
    q = _base_query(db, year)
    rows = q.all()

    buckets_def = [("0-7d", 0, 7), ("8-14d", 8, 14), ("15-30d", 15, 30), ("31-45d", 31, 45), ("46-60d", 46, 60)]
    result = []
    for label, lo, hi in buckets_def:
        appts = [r for r in rows if lo <= r.lead_days <= hi]
        total = len(appts)
        ns    = sum(1 for a in appts if a.status == "No-Show")
        rate  = round(ns / total * 100, 1) if total else 0
        result.append(LeadTimeBucket(bucket=label, total=total, no_show=ns, no_show_rate=rate))
    return result
