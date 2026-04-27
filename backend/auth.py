"""认证与鉴权依赖模块。"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Iterable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.exceptions import ApiError
from backend.models.core import Role, User


def _load_env_files() -> None:
    """优先加载 backend/.env，确保 SECRET_KEY 可用。"""
    backend_dir = Path(__file__).resolve().parent
    project_dir = backend_dir.parent
    for env_path in (backend_dir / ".env", project_dir / ".env", Path.cwd() / ".env"):
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)


def _secret_key() -> str:
    return os.getenv("SECRET_KEY", "CHANGE_ME_TO_A_STRONG_SECRET").strip()


_load_env_files()
SECRET_KEY = _secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# 说明：部分 Windows 环境下 bcrypt 后端与 passlib 版本组合存在兼容性问题，
# 这里优先使用 pbkdf2_sha256 生成新口令哈希，同时保留 bcrypt 以兼容历史数据校验。
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希值是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """对密码进行哈希加密。"""
    return pwd_context.hash(password)


def create_access_token(
    sub: str,
    role: str,
    clinic_id: str,
    user_id: int | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """生成包含sub、role、clinic_id、exp字段的JWT令牌。"""
    expire_time = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": sub, "role": role, "clinic_id": clinic_id, "exp": expire_time}
    if user_id is not None:
        payload["user_id"] = int(user_id)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(db: Session, username: str, password: str) -> tuple[User, str, str] | None:
    """根据用户名和密码认证用户并返回用户、角色标识、院区编码。"""
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if role is None:
        raise ApiError(code=403, message="用户角色未配置")
    return user, role.name, user.branch_code


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """解析JWT并返回当前登录用户对象。"""
    credentials_error = ApiError(code=401, message="未登录或令牌无效")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        token_role = payload.get("role")
        token_clinic_id = payload.get("clinic_id")
        if not sub or not token_role or not token_clinic_id:
            raise credentials_error
    except JWTError as exc:
        raise credentials_error from exc

    user = db.query(User).filter(User.username == sub, User.is_active.is_(True)).first()
    if user is None:
        raise credentials_error
    role_obj = db.query(Role).filter(Role.id == user.role_id).first()
    if role_obj is None or token_role != role_obj.name or token_clinic_id != user.branch_code:
        raise credentials_error
    return user


class RequireRole:
    """基于角色列表的权限依赖。"""

    def __init__(self, allowed_roles: Iterable[str]) -> None:
        self.allowed_roles = set(allowed_roles)

    def __call__(self, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        """校验当前用户角色是否在允许范围内。"""
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if role is None:
            raise ApiError(code=403, message="权限不足")
        if role.name not in self.allowed_roles:
            raise ApiError(code=403, message="权限不足")
        return user

