from pydantic import BaseModel
from typing import Optional


class KPISummary(BaseModel):
    total: int
    showed: int
    no_show: int
    cancelled: int
    scheduled: int
    no_show_rate: float
    attendance_rate: float
    avg_wait_minutes: float
    avg_lead_days: float
    sms_no_show_rate: float
    no_sms_no_show_rate: float
    high_risk_count: int


class DeptStat(BaseModel):
    department: str
    total: int
    showed: int
    no_show: int
    cancelled: int
    no_show_rate: float
    avg_wait: float


class DoctorStat(BaseModel):
    doctor: str
    department: str
    total: int
    showed: int
    no_show: int
    no_show_rate: float
    avg_wait: float


class MonthlyBucket(BaseModel):
    label: str       # "Jan 2024"
    year: int
    month: int
    total: int
    showed: int
    no_show: int
    no_show_rate: float


class AgeGroupStat(BaseModel):
    age_group: str
    total: int
    no_show: int
    no_show_rate: float


class DowStat(BaseModel):
    day: str
    total: int
    no_show: int
    no_show_rate: float


class RiskFactor(BaseModel):
    factor: str
    no_show_count: int


class SmsImpact(BaseModel):
    sms_sent_rate: float
    no_sms_rate: float
    sms_total: int
    no_sms_total: int


class LeadTimeBucket(BaseModel):
    bucket: str
    total: int
    no_show: int
    no_show_rate: float
