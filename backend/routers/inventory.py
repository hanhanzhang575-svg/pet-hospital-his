"""库存管理与预警路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.core import Drug, DrugInventory
from backend.schemas.inventory import EoqRequest
from backend.schemas.response import success_response
from backend.services.eoq_calculator import calculate_inventory_plan
from backend.services.expiry_monitor import scan_expiry_warnings
from backend.services.realtime_hub import dispatch_async, hub

router = APIRouter(prefix="/inventory", tags=["inventory"])
CLINIC_NAME_MAP = {
    "C001": "沙河口院区",
    "C002": "甘井子院区",
    "C003": "高新园区院区",
}


@router.post("/eoq")
def eoq_calculate(payload: EoqRequest) -> dict[str, object]:
    """计算EOQ库存计划。"""
    result = calculate_inventory_plan(
        annual_demand=payload.annual_demand,
        order_cost=payload.order_cost,
        holding_cost=payload.holding_cost,
        lead_time_days=payload.lead_time_days,
        daily_demand=payload.daily_demand,
    )
    return success_response(data=result.model_dump())


@router.get("/expiry-warnings")
def expiry_warnings(warning_days: int = 30, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询药品效期预警结果。"""
    data = [item.model_dump() for item in scan_expiry_warnings(db, warning_days=warning_days)]
    return success_response(data=data)


@router.get("/overview")
def inventory_overview(branch_code: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询库存总览（含药品基础信息）。"""
    query = db.query(DrugInventory, Drug).join(Drug, Drug.id == DrugInventory.drug_id)
    if branch_code:
        query = query.filter(DrugInventory.branch_code == branch_code)
    rows = query.order_by(DrugInventory.id.asc()).all()
    data = [
        {
            "inventory_id": inv.id,
            "drug_id": inv.drug_id,
            "drug_code": drug.drug_code,
            "drug_name": drug.name,
            "branch_code": inv.branch_code,
            "clinic_name": CLINIC_NAME_MAP.get(inv.branch_code, inv.branch_code),
            "stock_qty": inv.stock_qty,
            "safety_stock": inv.safety_stock,
            "frozen_for_prescription": inv.frozen_for_prescription,
            "expiry_date": inv.expiry_date.isoformat() if inv.expiry_date else None,
        }
        for inv, drug in rows
    ]
    for row in data:
        if float(row["stock_qty"]) < float(row["safety_stock"]):
            dispatch_async(
                hub.send_to_roles(
                    ["manager"],
                    title="库存预警",
                    content=f'{row["drug_name"]}库存仅剩{row["stock_qty"]}，低于安全阈值，请审批采购申请',
                    level="warning",
                )
            )
    return success_response(data=data)

