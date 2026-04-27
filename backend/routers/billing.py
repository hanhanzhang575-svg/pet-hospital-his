"""收费与催缴路由。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends

from backend.database import get_db
from backend.models.core import MedicalRecord, Pet, Prescription
from backend.schemas.response import success_response
from backend.services.realtime_hub import dispatch_async, hub

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/urge-payment")
def urge_payment(prescription_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """触发处方催缴提醒（示例实现，返回成功回执）。"""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    pet_name = "该宠物"
    if prescription is not None:
        mr = db.query(MedicalRecord).filter(MedicalRecord.id == prescription.medical_record_id).first()
        if mr is not None:
            pet = db.query(Pet).filter(Pet.id == mr.pet_id).first()
            if pet is not None:
                pet_name = pet.name
        dispatch_async(
            hub.send_to_roles(
                ["receptionist"],
                title="处方失效提醒",
                content=f"{pet_name}处方即将失效，请提醒客户缴费",
                level="warning",
            )
        )
    return success_response(
        data={
            "prescription_id": prescription_id,
            "status": "queued",
            "message": "已向前台推送催缴提醒",
            "triggered_at": datetime.utcnow().isoformat(),
        }
    )


@router.post("/settlement-complete")
def settlement_complete(settled_count: int, total_income: float) -> dict[str, object]:
    """收费结算完成后通知院区主任。"""
    dispatch_async(
        hub.send_to_roles(
            ["manager"],
            title="结算完成",
            content=f"今日已结算{settled_count}笔，累计收入{total_income:.2f}元",
            level="info",
        )
    )
    return success_response(data={"settled_count": settled_count, "total_income": total_income})

