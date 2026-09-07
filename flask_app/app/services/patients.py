"""
Patient profile service.
All queries are scoped to a single patient_id — computed in Python
since per-patient data is tiny (few hundred rows at most).
"""
import calendar
from app.models.appointment import Appointment
from app.models.department  import Department
from app.models.doctor      import Doctor


def get_patient_profile(patient_id: int) -> dict:
    """
    Returns a complete profile dict for one patient:
    - summary KPIs
    - full appointment history (latest first)
    - monthly history chart data
    - risk trend over time
    - per-department breakdown
    """
    appts = (
        Appointment.query
        .join(Department, Appointment.department_id == Department.id)
        .join(Doctor,     Appointment.doctor_id     == Doctor.id)
        .filter(Appointment.patient_id == patient_id)
        .order_by(Appointment.appointment_date.desc())
        .all()
    )

    total     = len(appts)
    showed    = sum(1 for a in appts if a.status == "Showed")
    no_show   = sum(1 for a in appts if a.status == "No-Show")
    cancelled = sum(1 for a in appts if a.status == "Cancelled")
    scheduled = sum(1 for a in appts if a.status == "Scheduled")

    def rate(p, t):
        return round(p / t * 100, 1) if t else 0.0

    # Latest appointment
    latest = appts[0] if appts else None

    # Average wait / lead
    avg_wait = round(sum(a.wait_minutes for a in appts) / total, 1) if total else 0
    avg_lead = round(sum(a.lead_days    for a in appts) / total, 1) if total else 0

    # Current risk score
    current_risk       = latest.risk_score if latest else 0
    current_risk_label = latest.risk_label if latest else "Low"

    # ── Monthly history chart (bar — showed vs no-show per month) ────────
    monthly: dict[tuple, dict] = {}
    for a in reversed(appts):           # oldest first for chart ordering
        key = (a.appointment_date.year, a.appointment_date.month)
        if key not in monthly:
            monthly[key] = {"showed": 0, "no_show": 0, "total": 0}
        monthly[key]["total"] += 1
        if a.status == "Showed":   monthly[key]["showed"]  += 1
        if a.status == "No-Show":  monthly[key]["no_show"] += 1

    sorted_keys = sorted(monthly)
    history_chart = dict(
        labels=[f"{calendar.month_abbr[m]} {y}" for y, m in sorted_keys],
        showed=[monthly[k]["showed"]  for k in sorted_keys],
        no_show=[monthly[k]["no_show"] for k in sorted_keys],
    )

    # ── Risk trend (line — risk_score over time, oldest → newest) ────────
    risk_appts = sorted(appts, key=lambda a: a.appointment_date)
    risk_trend = dict(
        labels=[str(a.appointment_date) for a in risk_appts],
        scores=[a.risk_score            for a in risk_appts],
    )

    # ── Per-department breakdown ──────────────────────────────────────────
    dept_map: dict[str, dict] = {}
    for a in appts:
        d = a.department.name
        if d not in dept_map:
            dept_map[d] = {"total": 0, "showed": 0, "no_show": 0}
        dept_map[d]["total"] += 1
        if a.status == "Showed":  dept_map[d]["showed"]  += 1
        if a.status == "No-Show": dept_map[d]["no_show"] += 1

    dept_breakdown = [
        dict(
            department=d,
            total=v["total"],
            showed=v["showed"],
            no_show=v["no_show"],
            rate=rate(v["no_show"], v["total"]),
        )
        for d, v in sorted(dept_map.items())
    ]

    # ── Appointment history rows ──────────────────────────────────────────
    history = [dict(
        id=a.id,
        date=str(a.appointment_date),
        time_slot=a.time_slot or "—",
        department=a.department.name,
        doctor=a.doctor.name,
        status=a.status,
        risk_label=a.risk_label,
        risk_score=a.risk_score,
        sms_received=a.sms_received,
        lead_days=a.lead_days,
        wait_minutes=a.wait_minutes,
        notes=a.notes or "",
    ) for a in appts]

    return dict(
        total=total,
        showed=showed,
        no_show=no_show,
        cancelled=cancelled,
        scheduled=scheduled,
        no_show_rate=rate(no_show, total),
        attendance_rate=rate(showed, total),
        avg_wait=avg_wait,
        avg_lead=avg_lead,
        current_risk=current_risk,
        current_risk_label=current_risk_label,
        latest=latest,
        history=history,
        history_chart=history_chart,
        risk_trend=risk_trend,
        dept_breakdown=dept_breakdown,
    )
