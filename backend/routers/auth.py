"""认证相关路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.auth import RequireRole, get_current_user
from backend.database import get_db
from backend.models.core import Role, User
from backend.schemas.response import success_response
from backend.services.auth_service import login_for_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict[str, str]:
    """登录并返回OAuth2标准令牌结构。"""
    return login_for_access_token(db=db, username=form_data.username, password=form_data.password)


@router.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    """返回当前登录用户信息。"""
    role = db.query(Role).filter(Role.id == current_user.role_id).first()
    return success_response(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "role_id": current_user.role_id,
            "role": role.name if role else "",
            "clinic_id": current_user.branch_code,
            "is_active": current_user.is_active,
        }
    )


@router.get("/admin-or-doctor")
def admin_or_doctor_only(
    current_user: User = Depends(RequireRole(["admin", "doctor"])),
) -> dict[str, object]:
    """受角色权限控制的示例接口。"""
    return success_response(data={"username": current_user.username, "authorized": True})

