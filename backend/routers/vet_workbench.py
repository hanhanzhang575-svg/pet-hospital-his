"""兽医工作台路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.auth import RequireRole
from backend.database import get_db
from datetime import datetime

from backend.models.core import (
    User,
    MedicalRecord,
    Pet,
    Owner,
    Appointment,
    Prescription,
    PrescriptionItem,
    Drug,
    InpatientRecord,
)
from backend.schemas.appointment import AppointmentRead
from backend.schemas.medical_record import MedicalRecordCreate, MedicalRecordRead
from backend.schemas.response import success_response
from backend.services.vet_workbench_service import (
    create_medical_record,
    list_medical_records,
    list_pending_queue,
    start_consultation,
    void_medical_record,
)

router = APIRouter(prefix="/vet-workbench", tags=["vet-workbench"])


@router.get("/queue")
def pending_queue(
    current_user: User = Depends(RequireRole(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """查询当前登录医生待诊队列。"""
    data = []
    for item in list_pending_queue(db, current_user.id, current_user.branch_code):
        row = AppointmentRead.model_validate(item).model_dump()
        pet = db.query(Pet).filter(Pet.id == item.pet_id).first()
        if pet is not None:
            row["pet_name"] = pet.name
            row["pet_species"] = pet.species
            row["pet_breed"] = pet.breed
            row["pet_birth_date"] = pet.birth_date.isoformat() if getattr(pet, "birth_date", None) else ""
            row["allergy_history"] = pet.allergy_history or []
        else:
            row["pet_name"] = f"宠物#{item.pet_id}"
            row["pet_species"] = ""
            row["pet_breed"] = ""
            row["pet_birth_date"] = ""
            row["allergy_history"] = []
        doctor = db.query(User).filter(User.id == item.doctor_id).first()
        row["doctor_name"] = doctor.full_name if doctor else f"医生#{item.doctor_id}"
        data.append(row)
    return success_response(data=data)


@router.post("/start/{appointment_id}")
def start_visit(
    appointment_id: int,
    current_user: User = Depends(RequireRole(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """开始接诊并更新预约状态。"""
    data = AppointmentRead.model_validate(start_consultation(db, appointment_id, current_user.id)).model_dump()
    return success_response(data=data)


@router.post("/medical-record")
def create_record(
    payload: MedicalRecordCreate,
    current_user: User = Depends(RequireRole(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """录入病历并完成预约。"""
    if payload.vet_id != current_user.id:
        payload = payload.model_copy(update={"vet_id": current_user.id})
    data = MedicalRecordRead.model_validate(create_medical_record(db, payload)).model_dump()
    return success_response(data=data)


@router.get("/medical-records")
def medical_records(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    pet_id: int | None = None,
    vet_id: int | None = None,
    clinic_id: str | None = None,
    current_user: User = Depends(RequireRole(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """查询病历列表（带分页）。"""
    _ = current_user
    query = db.query(MedicalRecord)
    if pet_id:
        query = query.filter(MedicalRecord.pet_id == pet_id)
    if vet_id:
        query = query.filter(MedicalRecord.vet_id == vet_id)
    if clinic_id:
        vet_ids = [item.id for item in db.query(User.id).filter(User.branch_code == clinic_id).all()]
        if vet_ids:
            query = query.filter(MedicalRecord.vet_id.in_(vet_ids))
        else:
            return success_response(data=[], total=0)
    
    total = query.count()
    items = query.order_by(MedicalRecord.created_at.desc()).offset((page - 1) * size).limit(size).all()
    
    # 补充宠物、主人、医生信息
    result = []
    for record in items:
        rec_dict = MedicalRecordRead.model_validate(record).model_dump()
        pet = db.query(Pet).filter(Pet.id == record.pet_id).first()
        if pet:
            rec_dict["pet_name"] = pet.name
            rec_dict["pet_species"] = pet.species
            rec_dict["pet_breed"] = pet.breed
            owner = db.query(Owner).filter(Owner.id == pet.owner_id).first()
            if owner:
                rec_dict["owner_name"] = owner.name
                rec_dict["owner_phone"] = owner.phone
        vet = db.query(User).filter(User.id == record.vet_id).first()
        if vet:
            rec_dict["vet_name"] = vet.full_name
            rec_dict["clinic_id"] = vet.branch_code
        result.append(rec_dict)
    
    return success_response(data=result, total=total)


@router.get("/pet-history/{pet_id}")
def pet_history(
    pet_id: int,
    current_user: User = Depends(RequireRole(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """查询宠物全量病历时间轴（含急诊、处方、住院天数信息）。"""
    _ = current_user
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if pet is None:
        return success_response(code=404, message="宠物不存在")
    owner = db.query(Owner).filter(Owner.id == pet.owner_id).first()

    records = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.pet_id == pet_id)
        .order_by(MedicalRecord.created_at.desc())
        .all()
    )
    timeline: list[dict[str, object]] = []
    for record in records:
        appointment = db.query(Appointment).filter(Appointment.id == record.appointment_id).first()
        is_emergency = bool(appointment and appointment.urgency_level == "急诊")

        drug_rows = (
            db.query(Prescription, PrescriptionItem, Drug)
            .join(PrescriptionItem, PrescriptionItem.prescription_id == Prescription.id)
            .join(Drug, Drug.id == PrescriptionItem.drug_id)
            .filter(Prescription.medical_record_id == record.id)
            .all()
        )
        drug_tags = [f"{drug.name}×{item.quantity}" for _pres, item, drug in drug_rows]

        inpatient = (
            db.query(InpatientRecord)
            .filter(InpatientRecord.pet_id == pet_id)
            .order_by(InpatientRecord.admission_time.desc())
            .first()
        )
        inpatient_days = 0
        if inpatient and inpatient.admission_time:
            end_time = inpatient.discharge_time or datetime.now()
            inpatient_days = max((end_time - inpatient.admission_time).days, 0)

        timeline.append(
            {
                "record_id": record.id,
                "record_no": record.record_no,
                "created_at": record.created_at.isoformat() if record.created_at else "",
                "chief_complaint": record.chief_complaint or "",
                "exam_notes": record.exam_notes or "",
                "diagnosis": record.diagnosis or "",
                "is_voided": record.is_voided,
                "is_emergency": is_emergency,
                "urgency_level": appointment.urgency_level if appointment else "",
                "drug_tags": drug_tags,
                "inpatient_days": inpatient_days,
            }
        )

    data = {
        "pet_profile": {
            "id": pet.id,
            "pet_code": pet.pet_code,
            "name": pet.name,
            "species": pet.species,
            "breed": pet.breed,
            "gender": pet.gender,
            "birth_date": pet.birth_date.isoformat() if getattr(pet, "birth_date", None) else "",
            "color": pet.color,
            "owner_name": owner.name if owner else "",
            "owner_phone": owner.phone if owner else "",
        },
        "timeline": timeline,
    }
    return success_response(data=data)


@router.get("/medical-record/{record_id}")
def get_medical_record(
    record_id: int,
    current_user: User = Depends(RequireRole(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """获取病历详情。"""
    _ = current_user
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        return success_response(code=404, message="病历不存在")
    data = MedicalRecordRead.model_validate(record).model_dump()
    return success_response(data=data)


@router.put("/medical-record/{record_id}")
def update_medical_record(
    record_id: int,
    payload: dict,
    current_user: User = Depends(RequireRole(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """更新病历（仅限最新记录编辑）。"""
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        return success_response(code=404, message="病历不存在")
    if record.vet_id != current_user.id and current_user.role_id != 1:
        return success_response(code=403, message="无权限编辑他人病历")
    
    if "chief_complaint" in payload:
        record.chief_complaint = payload["chief_complaint"]
    if "exam_notes" in payload:
        record.exam_notes = payload["exam_notes"]
    if "diagnosis" in payload:
        record.diagnosis = payload.get("diagnosis")
    if "treatment_plan" in payload:
        record.treatment_plan = payload.get("treatment_plan")
    
    db.commit()
    data = MedicalRecordRead.model_validate(record).model_dump()
    return success_response(data=data)


@router.post("/medical-record/{record_id}/void")
def medical_record_void(
    record_id: int,
    payload: dict,
    current_user: User = Depends(RequireRole(["doctor", "admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """作废病历。"""
    reason = str(payload.get("reason") or "").strip()
    if not reason:
        return success_response(code=400, message="请输入作废原因")
    record = void_medical_record(db, record_id, current_user.id, reason)
    data = MedicalRecordRead.model_validate(record).model_dump()
    return success_response(data=data)

