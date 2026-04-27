"""采购与回访任务Schema定义。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PurchaseTaskCreate(BaseModel):
    """采购任务创建项。"""

    drug_id: int
    branch_code: str
    current_stock: float
    safety_stock: float
    suggested_qty: float


class PurchaseTaskRead(BaseModel):
    """采购任务响应体。"""

    id: int
    drug_id: int
    branch_code: str
    current_stock: float
    safety_stock: float
    suggested_qty: float
    status: str
    created_at: datetime


class FollowupTaskCreate(BaseModel):
    """回访任务创建项。"""

    owner_id: int
    owner_name: str
    risk_score: float
    risk_level: str
    recency_days: int
    frequency: int
    monetary: float
    assignee_id: int | None = None
    script_text: str


class FollowupTaskRead(BaseModel):
    """回访任务响应体。"""

    id: int
    owner_id: int
    owner_name: str
    risk_score: float
    risk_level: str
    recency_days: int
    frequency: int
    monetary: float
    assignee_id: int | None = None
    script_text: str
    status: str
    created_at: datetime

