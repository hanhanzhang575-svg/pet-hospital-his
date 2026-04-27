"""住院押金水位监控定时任务模块。"""

from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.orm import Session

from backend.models.core import InpatientRecord, Pet
from backend.schemas.inpatient import DepositWarningRead
from backend.services.realtime_hub import dispatch_async, hub


def evaluate_deposit_warnings(db: Session) -> list[DepositWarningRead]:
    """计算住院押金水位并返回预警列表。"""
    warnings: list[DepositWarningRead] = []
    records = db.query(InpatientRecord).filter(InpatientRecord.status != "已出院").all()
    for record in records:
        pet = db.query(Pet).filter(Pet.id == record.pet_id).first()
        pet_name = pet.name if pet else f"宠物#{record.pet_id}"
        balance = round(record.deposit_amount - record.consumed_amount, 2)
        if balance <= 0:
            dispatch_async(
                hub.send_to_roles(
                    ["nurse", "manager", "receptionist"],
                    title="欠费停药预警",
                    content=f"{pet_name}押金余额已归零，已触发停药流程，请立即处理",
                    level="error",
                )
            )
            warnings.append(
                DepositWarningRead(
                    inpatient_record_id=record.id,
                    balance=balance,
                    warning_level="critical",
                    message="余额归零，触发欠费停药预警并通知院区主任",
                )
            )
        elif balance < 500:
            dispatch_async(
                hub.send_to_roles(
                    ["nurse", "manager", "receptionist"],
                    title="欠费预警",
                    content=f"{pet_name}押金余额不足500元，请联系主人充值",
                    level="warning",
                )
            )
            warnings.append(
                DepositWarningRead(
                    inpatient_record_id=record.id,
                    balance=balance,
                    warning_level="warning",
                    message="余额低于500元，推送催缴通知并提醒护士站",
                )
            )
    return warnings


def daily_deposit_job(db_factory: Callable[[], Session]) -> list[DepositWarningRead]:
    """每日押金核算任务入口。"""
    db = db_factory()
    try:
        return evaluate_deposit_warnings(db)
    finally:
        db.close()

