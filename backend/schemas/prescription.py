"""处方开具Schema定义。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionItemCreate(BaseModel):
    """处方明细创建请求体。"""

    drug_id: int
    dosage: str
    frequency: str
    duration_days: int
    quantity: float


class PrescriptionCreate(BaseModel):
    """处方创建请求体。"""

    medical_record_id: int
    doctor_id: int
    clinic_id: str
    items: list[PrescriptionItemCreate] = Field(default_factory=list)


class PrescriptionRead(BaseModel):
    """处方响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prescription_code: str
    medical_record_id: int
    doctor_id: int
    status: str
    created_at: datetime
    expire_at: datetime
    locked_inventory: dict[str, float]

