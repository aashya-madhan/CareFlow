from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services import analytics as svc
from app.schemas.analytics import (
    KPISummary, DeptStat, DoctorStat, MonthlyBucket,
    AgeGroupStat, DowStat, RiskFactor, SmsImpact, LeadTimeBucket,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _year(y: Optional[str] = Query(None)) -> Optional[str]:
    return y


@router.get("/kpi", response_model=KPISummary)
def kpi(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_kpi_summary(db, year)


@router.get("/monthly", response_model=list[MonthlyBucket])
def monthly(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_monthly_buckets(db, year)


@router.get("/departments", response_model=list[DeptStat])
def departments(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_dept_stats(db, year)


@router.get("/doctors", response_model=list[DoctorStat])
def doctors(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_doctor_stats(db, year)


@router.get("/age-groups", response_model=list[AgeGroupStat])
def age_groups(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_age_group_stats(db, year)


@router.get("/dow", response_model=list[DowStat])
def dow(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_dow_stats(db, year)


@router.get("/risk-factors", response_model=list[RiskFactor])
def risk_factors(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_risk_factors(db, year)


@router.get("/sms-impact", response_model=SmsImpact)
def sms_impact(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_sms_impact(db, year)


@router.get("/lead-time", response_model=list[LeadTimeBucket])
def lead_time(year: Optional[str] = Query(None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_lead_time_stats(db, year)
