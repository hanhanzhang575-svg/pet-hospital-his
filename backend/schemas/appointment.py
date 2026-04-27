"""门诊挂号Schema定义。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AppointmentCreate(BaseModel):
    """创建预约挂号请求体。"""

    pet_id: int
    doctor_id: int
    clinic_id: str
    scheduled_time: datetime
    urgency_level: str = "常规"


class AppointmentRead(BaseModel):
    """预约挂号响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    record_code: str
    pet_id: int
    doctor_id: int
    clinic_id: str
    scheduled_time: datetime
    urgency_level: str
    status: str
    priority_score: float
    max_capacity: int | None = None
    is_leave: bool | None = None
    schedule_note: str | None = None
    created_at: datetime


class AppointmentUpdate(BaseModel):
    """预约更新请求体。"""

    doctor_id: int | None = None
    scheduled_time: datetime | None = None
    clinic_id: str | None = None
    urgency_level: str | None = None
    max_capacity: int | None = None
    is_leave: bool | None = None
    schedule_note: str | None = None

