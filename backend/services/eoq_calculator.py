"""EOQ库存模型模块。"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.core import Drug, Prescription, PrescriptionItem
from backend.schemas.inventory import EoqResult


def calculate_eoq(annual_demand: float, order_cost: float, holding_cost: float) -> float:
    """按经典EOQ公式计算最优订货量。"""
    if annual_demand <= 0 or order_cost <= 0 or holding_cost <= 0:
        raise ValueError("EOQ参数必须为正数")
    return math.sqrt((2 * annual_demand * order_cost) / holding_cost)


def calculate_inventory_plan(
    annual_demand: float,
    order_cost: float,
    holding_cost: float,
    lead_time_days: float,
    daily_demand: float,
) -> EoqResult:
    """计算EOQ、再订货点和安全库存建议值。"""
    eoq = calculate_eoq(annual_demand, order_cost, holding_cost)
    demand_per_day = daily_demand if daily_demand > 0 else annual_demand / 365.0
    reorder_point = round(demand_per_day * max(lead_time_days, 0), 2)
    safety_stock = round(demand_per_day * 3, 2)
    return EoqResult(eoq=round(eoq, 2), reorder_point=reorder_point, safety_stock=safety_stock)


def calculate_dynamic_annual_demand(db: Session, drug_id: int, now: datetime | None = None) -> tuple[float, float]:
    """根据近30天真实出库量推算日均与年需求量。"""
    current = now or datetime.now()
    window_start = current - timedelta(days=30)
    total_outbound = (
        db.query(func.coalesce(func.sum(PrescriptionItem.quantity), 0.0))
        .join(Prescription, Prescription.id == PrescriptionItem.prescription_id)
        .filter(PrescriptionItem.drug_id == drug_id)
        .filter(Prescription.created_at >= window_start)
        .scalar()
    )
    if total_outbound and float(total_outbound) > 0:
        daily_avg = float(total_outbound) / 30.0
        annual_demand = daily_avg * 365.0
    else:
        annual_demand = 52.0
        daily_avg = annual_demand / 365.0
    return daily_avg, annual_demand


def calculate_drug_eoq(db: Session, drug_id: int, order_cost: float = 50.0) -> dict[str, float]:
    """按题设业务规则计算单药品EOQ参数。"""
    drug = db.query(Drug).filter(Drug.id == drug_id).first()
    if drug is None:
        raise ValueError("药品不存在")
    daily_avg, annual_demand = calculate_dynamic_annual_demand(db, drug_id)
    unit_price = max(float(getattr(drug, "unit_price", 0.0) or 0.0), 0.01)
    holding_cost = max(unit_price * 0.2, 0.01)
    eoq_raw = calculate_eoq(annual_demand, order_cost, holding_cost)
    eoq_qty = max(1, int(math.ceil(eoq_raw)))
    return {
        "daily_avg": round(daily_avg, 4),
        "annual_demand": round(annual_demand, 2),
        "order_cost": float(order_cost),
        "holding_cost": round(holding_cost, 4),
        "eoq_raw": round(eoq_raw, 4),
        "eoq_qty": float(eoq_qty),
        "unit_price": round(unit_price, 4),
    }

