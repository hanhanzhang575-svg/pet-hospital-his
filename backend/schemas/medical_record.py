"""病历录入Schema定义。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MedicalRecordCreate(BaseModel):
    """创建病历请求体。"""

    appointment_id: int
    pet_id: int
    vet_id: int
    chief_complaint: str | None = None
    exam_notes: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    kg_evidence_id: str | None = None


class MedicalRecordRead(BaseModel):
    """病历响应体。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    record_no: str
    appointment_id: int
    pet_id: int
    vet_id: int
    chief_complaint: str | None = None
    exam_notes: str | None = None
    diagnosis: str | None = None
    treatment_plan: str | None = None
    kg_evidence_id: str | None = None
    is_voided: bool = False
    void_reason: str | None = None
    voided_at: datetime | None = None
    created_at: datetime

