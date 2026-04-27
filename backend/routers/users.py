"""用户查询路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.core import Role, User
from backend.schemas.response import success_response

router = APIRouter(prefix="/users", tags=["users"])
DOCTOR_DEPARTMENT_MAP = {
    ("C001", "张医生"): "内科",
    ("C001", "李医生"): "外科",
    ("C002", "王医生"): "皮肤科",
    ("C002", "赵医生"): "眼科",
    ("C003", "陈医生"): "内科",
    ("C003", "刘医生"): "齿科",
}


@router.get("/doctors")
def doctors(clinic_id: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询医生列表，可按院区过滤。"""
    doctor_role = db.query(Role).filter(Role.name == "doctor").first()
    if doctor_role is None:
        return success_response(data=[])
    query = db.query(User).filter(User.role_id == doctor_role.id, User.is_active.is_(True))
    if clinic_id:
        query = query.filter(User.branch_code == clinic_id)
    data = [
        {
            "id": item.id,
            "username": item.username,
            "full_name": item.full_name,
            "branch_code": item.branch_code,
            "department": DOCTOR_DEPARTMENT_MAP.get((item.branch_code, item.full_name), "综合门诊"),
        }
        for item in query.order_by(User.id.asc()).all()
    ]
    return success_response(data=data)


@router.get("/lab-techs")
def lab_techs(clinic_id: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询医技人员列表。"""
    role = db.query(Role).filter(Role.name == "lab_tech").first()
    if role is None:
        return success_response(data=[])
    query = db.query(User).filter(User.role_id == role.id, User.is_active.is_(True))
    if clinic_id:
        query = query.filter(User.branch_code == clinic_id)
    data = [
        {
            "id": item.id,
            "username": item.username,
            "full_name": item.full_name,
            "branch_code": item.branch_code,
        }
        for item in query.order_by(User.id.asc()).all()
    ]
    return success_response(data=data)


@router.get("")
def users(role: str | None = None, clinic_id: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询用户列表。"""
    query = db.query(User)
    if role:
        role_row = db.query(Role).filter(Role.name == role).first()
        if role_row is None:
            return success_response(data=[])
        query = query.filter(User.role_id == role_row.id)
    if clinic_id:
        query = query.filter(User.branch_code == clinic_id)
    rows = query.order_by(User.id.asc()).all()
    role_map = {item.id: item.name for item in db.query(Role).all()}
    data = [
        {
            "id": item.id,
            "employee_code": item.employee_code,
            "username": item.username,
            "full_name": item.full_name,
            "role": role_map.get(item.role_id, ""),
            "clinic_id": item.branch_code,
            "is_active": item.is_active,
            "is_licensed_vet": item.is_licensed_vet,
        }
        for item in rows
    ]
    return success_response(data=data)


@router.get("/{user_id}")
def user_detail(user_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询用户详情。"""
    row = db.query(User).filter(User.id == user_id).first()
    if row is None:
        return success_response(code=404, message="用户不存在")
    role = db.query(Role).filter(Role.id == row.role_id).first()
    data = {
        "id": row.id,
        "employee_code": row.employee_code,
        "username": row.username,
        "full_name": row.full_name,
        "role": role.name if role else "",
        "clinic_id": row.branch_code,
        "is_active": row.is_active,
        "is_licensed_vet": row.is_licensed_vet,
    }
    return success_response(data=data)

