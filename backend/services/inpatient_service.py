"""住院记录管理业务服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.exceptions import ApiError
from backend.models.core import CageUnit, InpatientRecord, Pet, User
from backend.schemas.inpatient import InpatientRecordCreate, InpatientRecordUpdate
from backend.services.cage_allocator import CAGE_STATUS_IDLE, CAGE_STATUS_IN_USE


def list_inpatient_records(db: Session, clinic_id: str | None = None) -> list[InpatientRecord]:
    """查询住院记录列表。"""
    query = db.query(InpatientRecord)
    if clinic_id:
        query = query.filter(InpatientRecord.clinic_id == clinic_id)
    return query.order_by(InpatientRecord.id.desc()).all()


def get_inpatient_record(db: Session, record_id: int) -> InpatientRecord:
    """根据ID查询住院记录。"""
    record = db.query(InpatientRecord).filter(InpatientRecord.id == record_id).first()
    if record is None:
        raise ApiError(code=404, message="住院记录不存在")
    return record


def create_inpatient_record(db: Session, payload: InpatientRecordCreate) -> InpatientRecord:
    """创建住院记录并占用笼舍。"""
    if payload.deposit_amount < 0:
        raise ApiError(code=400, message="押金金额不能为负数")
    if payload.consumed_amount < 0:
        raise ApiError(code=400, message="已消费金额不能为负数")
    if payload.consumed_amount > payload.deposit_amount:
        raise ApiError(code=400, message="已消费金额不能大于押金金额")

    pet = db.query(Pet).filter(Pet.id == payload.pet_id).first()
    if pet is None:
        raise ApiError(code=404, message="宠物档案不存在")
    doctor = db.query(User).filter(User.id == payload.doctor_id, User.is_active.is_(True)).first()
    if doctor is None:
        raise ApiError(code=404, message="医生不存在")
    cage = db.query(CageUnit).filter(CageUnit.id == payload.cage_id).first()
    if cage is None:
        raise ApiError(code=404, message="笼舍不存在")
    if cage.clinic_id != payload.clinic_id:
        raise ApiError(code=409, message="禁止跨院区住院分配")
    if cage.current_pet_id not in (None, payload.pet_id):
        raise ApiError(code=409, message="笼舍已被其他宠物占用")

    record = InpatientRecord(**payload.model_dump())
    db.add(record)

    cage.current_pet_id = payload.pet_id
    cage.status = CAGE_STATUS_IN_USE

    db.commit()
    db.refresh(record)
    return record


def update_inpatient_record(db: Session, record_id: int, payload: InpatientRecordUpdate) -> InpatientRecord:
    """更新住院记录，并在出院时释放笼舍。"""
    record = get_inpatient_record(db, record_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "deposit_amount" in update_data and update_data["deposit_amount"] is not None and update_data["deposit_amount"] < 0:
        raise ApiError(code=400, message="押金金额不能为负数")
    if "consumed_amount" in update_data and update_data["consumed_amount"] is not None and update_data["consumed_amount"] < 0:
        raise ApiError(code=400, message="已消费金额不能为负数")

    deposit_amount = update_data.get("deposit_amount", record.deposit_amount)
    consumed_amount = update_data.get("consumed_amount", record.consumed_amount)
    if deposit_amount is not None and consumed_amount is not None and consumed_amount > deposit_amount:
        raise ApiError(code=400, message="已消费金额不能大于押金金额")

    discharge_time = update_data.get("discharge_time")
    if discharge_time is not None and discharge_time < record.admission_time:
        raise ApiError(code=400, message="出院时间不能早于入院时间")

    for key, value in update_data.items():
        setattr(record, key, value)

    if "status" in update_data and update_data["status"] == "已出院":
        cage = db.query(CageUnit).filter(CageUnit.id == record.cage_id).first()
        if cage is not None:
            cage.current_pet_id = None
            cage.status = CAGE_STATUS_IDLE

    db.commit()
    db.refresh(record)
    return record

