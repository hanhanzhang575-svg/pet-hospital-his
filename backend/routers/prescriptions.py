"""处方管理路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.core import Appointment, Drug, MedicalRecord, Owner, Pet, PrescriptionItem, User
from backend.schemas.prescription import PrescriptionCreate, PrescriptionRead
from backend.schemas.response import success_response
from backend.services.realtime_hub import dispatch_async, hub
from backend.services.prescription_service import create_prescription, invalidate_prescription, list_prescriptions, restore_prescription

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])
CLINIC_NAME_MAP = {
    "C001": "沙河口院区",
    "C002": "甘井子院区",
    "C003": "高新园区院区",
}


@router.post("", status_code=status.HTTP_201_CREATED)
def prescription_create(payload: PrescriptionCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    """创建处方并冻结库存。"""
    record = create_prescription(db, payload)
    medical_record = db.query(MedicalRecord).filter(MedicalRecord.id == record.medical_record_id).first()
    pet_name = "该宠物"
    if medical_record is not None:
        pet = db.query(Pet).filter(Pet.id == medical_record.pet_id).first()
        if pet is not None:
            pet_name = pet.name
    dispatch_async(
        hub.send_to_roles(
            ["pharmacy", "pharmacist"],
            title="新处方",
            content=f"{pet_name}处方待配药，2小时内有效",
            level="info",
        )
    )
    data = PrescriptionRead.model_validate(record).model_dump()
    return success_response(code=201, data=data)


@router.get("")
def prescriptions(clinic_id: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询处方列表。"""
    data = []
    for item in list_prescriptions(db, clinic_id):
        base = PrescriptionRead.model_validate(item).model_dump()
        medical_record = db.query(MedicalRecord).filter(MedicalRecord.id == item.medical_record_id).first()
        appointment = None
        pet = None
        owner = None
        doctor = db.query(User).filter(User.id == item.doctor_id).first()
        if medical_record is not None:
            appointment = db.query(Appointment).filter(Appointment.id == medical_record.appointment_id).first()
        if appointment is not None:
            pet = db.query(Pet).filter(Pet.id == appointment.pet_id).first()
        if pet is not None:
            owner = db.query(Owner).filter(Owner.id == pet.owner_id).first()
        details = (
            db.query(PrescriptionItem, Drug)
            .join(Drug, Drug.id == PrescriptionItem.drug_id)
            .filter(PrescriptionItem.prescription_id == item.id)
            .all()
        )
        base.update(
            {
                "pet_id": pet.id if pet else None,
                "pet_name": f'{pet.name}({pet.breed or pet.species})' if pet else "",
                "pet_breed": pet.breed if pet else "",
                "pet_birth_date": pet.birth_date if pet else "",
                "owner_name": owner.name if owner else "",
                "doctor_name": doctor.full_name if doctor else f"医生#{item.doctor_id}",
                "clinic_id": appointment.clinic_id if appointment else "",
                "clinic_name": CLINIC_NAME_MAP.get(appointment.clinic_id, appointment.clinic_id) if appointment else "",
                "drug_list": [f"{drug.name} x {detail.quantity}" for detail, drug in details],
            }
        )
        data.append(base)
    return success_response(data=data)


@router.post("/{prescription_id}/invalidate")
def prescription_invalidate(prescription_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """作废处方并释放冻结库存。"""
    data = PrescriptionRead.model_validate(invalidate_prescription(db, prescription_id)).model_dump()
    return success_response(data=data)


@router.post("/{prescription_id}/restore")
def prescription_restore(prescription_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """撤销处方作废。"""
    data = PrescriptionRead.model_validate(restore_prescription(db, prescription_id)).model_dump()
    return success_response(data=data, message="撤销作废成功")

