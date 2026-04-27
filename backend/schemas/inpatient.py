"""住院记录Schema定义。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InpatientRecordCreate(BaseModel):
    """创建住院记录请求体。"""

    pet_id: int
    cage_id: int
    doctor_id: int
    clinic_id: str
    admission_time: datetime
    deposit_amount: float
    consumed_amount: float = 0
    status: str = "待入院"


class InpatientRecordUpdate(BaseModel):
    """更新住院记录请求体。"""

    discharge_time: datetime | None = None
    deposit_amount: float | None = None
    consumed_amount: float | None = None
    status: str | None = None


class InpatientRecordRead(BaseModel):
    """住院记录响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pet_id: int
    cage_id: int
    doctor_id: int
    clinic_id: str
    admission_time: datetime
    discharge_time: datetime | None = None
    deposit_amount: float
    consumed_amount: float
    status: str
    created_at: datetime


class DepositWarningRead(BaseModel):
    """押金预警响应体。"""

    inpatient_record_id: int
    balance: float
    warning_level: str
    message: str

