"""处方超时释放定时任务模块。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.core import Appointment, DrugInventory, MedicalRecord, Pet, Prescription
from backend.services.realtime_hub import dispatch_async, hub


def scan_expired_prescriptions(db: Session, now: datetime | None = None) -> int:
    """扫描2小时未缴费处方并释放冻结库存。"""
    current_time = now or datetime.utcnow()
    expired = (
        db.query(Prescription)
        .filter(Prescription.status == "待缴费", Prescription.expire_at <= current_time)
        .all()
    )

    released_count = 0
    for prescription in expired:
        pet_name = "该宠物"
        medical_record = db.query(MedicalRecord).filter(MedicalRecord.id == prescription.medical_record_id).first()
        if medical_record is not None:
            appointment = db.query(Appointment).filter(Appointment.id == medical_record.appointment_id).first()
            if appointment is not None:
                pet = db.query(Pet).filter(Pet.id == appointment.pet_id).first()
                if pet is not None:
                    pet_name = pet.name
        locked_inventory = prescription.locked_inventory or {}
        for drug_id_str, quantity in locked_inventory.items():
            inventory = db.query(DrugInventory).filter(DrugInventory.drug_id == int(drug_id_str)).first()
            if inventory is None:
                continue
            inventory.stock_qty += float(quantity)
            inventory.frozen_for_prescription = False
        prescription.status = "已失效"
        prescription.locked_inventory = {}
        dispatch_async(
            hub.send_to_roles(
                ["receptionist"],
                title="处方失效提醒",
                content=f"{pet_name}处方即将失效，请提醒客户缴费",
                level="warning",
            )
        )
        released_count += 1

    if released_count > 0:
        db.commit()
    return released_count


def expired_prescription_job(db_factory: Callable[[], Session]) -> int:
    """处方超时释放定时任务入口。"""
    db = db_factory()
    try:
        return scan_expired_prescriptions(db)
    finally:
        db.close()

