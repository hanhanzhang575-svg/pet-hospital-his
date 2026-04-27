"""宠物主人档案Schema定义。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OwnerBase(BaseModel):
    """宠物主人基础字段。"""

    owner_code: str
    name: str
    phone: str
    id_card: str | None = None
    address: str | None = None
    member_level: str = "normal"
    latitude: float | None = None
    longitude: float | None = None


class OwnerCreate(OwnerBase):
    """创建宠物主人请求体。"""


class OwnerUpdate(BaseModel):
    """更新宠物主人请求体。"""

    name: str | None = None
    phone: str | None = None
    id_card: str | None = None
    address: str | None = None
    member_level: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class OwnerRead(OwnerBase):
    """宠物主人响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

