"""笼舍分配与状态机Schema定义。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CageAllocationRequest(BaseModel):
    """笼舍分配请求体。"""

    pet_id: int
    clinic_id: str
    preferred_zone_type: str
    is_emergency: bool = False


class CageStatusUpdateRequest(BaseModel):
    """笼舍状态更新请求体。"""

    target_status: str


class CageUnitRead(BaseModel):
    """笼舍响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cage_code: str
    clinic_id: str
    zone_type: str
    status: str
    current_pet_id: int | None
    adjacent_cage_ids: list[int]
    created_at: datetime

