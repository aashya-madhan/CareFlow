from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.department import Department
from app.models.doctor import Doctor
from app.models.user import User

router = APIRouter(prefix="/departments", tags=["departments"])


class DeptOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class DoctorOut(BaseModel):
    id: int
    name: str
    department_id: int
    department_name: Optional[str] = None
    model_config = {"from_attributes": True}


@router.get("", response_model=list[DeptOut])
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Department).order_by(Department.name).all()


@router.post("", response_model=DeptOut, status_code=201)
def create_department(name: str, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    if db.query(Department).filter(Department.name == name).first():
        raise HTTPException(status_code=400, detail="Department already exists")
    dept = Department(name=name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Doctor)
    if department_id:
        q = q.filter(Doctor.department_id == department_id)
    doctors = q.order_by(Doctor.name).all()
    result = []
    for d in doctors:
        o = DoctorOut.model_validate(d)
        o.department_name = d.department.name if d.department else None
        result.append(o)
    return result
