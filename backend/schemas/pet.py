"""宠物档案Schema定义。"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PetBase(BaseModel):
    """宠物基础字段。"""

    name: str
    species: str
    breed: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    color: str | None = None
    type_id: int | None = None
    weight: float | None = None
    allergy_history: list[str] = Field(default_factory=list)
    owner_id: int
    clinic_id: str


class PetCreate(PetBase):
    """创建宠物请求体。"""


class PetUpdate(BaseModel):
    """更新宠物请求体。"""

    name: str | None = None
    species: str | None = None
    breed: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    color: str | None = None
    type_id: int | None = None
    weight: float | None = None
    allergy_history: list[str] | None = None
    owner_id: int | None = None
    clinic_id: str | None = None


class PetRead(PetBase):
    """宠物响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_code: str
    created_at: datetime

