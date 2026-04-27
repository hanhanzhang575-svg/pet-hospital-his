"""认证服务模块。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.auth import authenticate_user, create_access_token
from backend.exceptions import ApiError


def login_for_access_token(db: Session, username: str, password: str) -> dict[str, str]:
    """执行登录认证并返回OAuth2标准令牌响应。"""
    auth_result = authenticate_user(db=db, username=username, password=password)
    if auth_result is None:
        raise ApiError(code=401, message="用户名或密码错误")

    user, role, clinic_id = auth_result
    access_token = create_access_token(sub=user.username, role=role, clinic_id=clinic_id, user_id=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

