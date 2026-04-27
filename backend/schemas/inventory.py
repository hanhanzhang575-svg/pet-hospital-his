"""库存与效期预警Schema定义。"""

from __future__ import annotations

from pydantic import BaseModel


class EoqRequest(BaseModel):
    """EOQ计算请求体。"""

    annual_demand: float
    order_cost: float
    holding_cost: float
    lead_time_days: float = 7
    daily_demand: float = 0


class EoqResult(BaseModel):
    """EOQ计算结果。"""

    eoq: float
    reorder_point: float
    safety_stock: float


class ExpiryWarningRead(BaseModel):
    """效期预警结果。"""

    inventory_id: int
    drug_id: int
    branch_code: str
    days_to_expiry: int
    warning_level: str
    message: str

