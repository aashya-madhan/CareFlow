from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PatientCreate(BaseModel):
    patient_code: str
    full_name: str
    age: int
    gender: str
    neighbourhood: Optional[str] = None
    scholarship: bool = False
    hypertension: bool = False
    diabetes: bool = False
    alcoholism: bool = False
    handicap: bool = False


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    neighbourhood: Optional[str] = None
    scholarship: Optional[bool] = None
    hypertension: Optional[bool] = None
    diabetes: Optional[bool] = None
    alcoholism: Optional[bool] = None
    handicap: Optional[bool] = None


class PatientOut(BaseModel):
    id: int
    patient_code: str
    full_name: str
    age: int
    gender: str
    neighbourhood: Optional[str] = None
    scholarship: bool
    hypertension: bool
    diabetes: bool
    alcoholism: bool
    handicap: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
