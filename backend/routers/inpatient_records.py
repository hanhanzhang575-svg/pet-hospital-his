"""住院记录管理路由。"""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models.core import CageUnit, InpatientRecord, NursingLog, Pet, User
from backend.schemas.cage import CageAllocationRequest, CageUnitRead
from backend.schemas.inpatient import InpatientRecordCreate, InpatientRecordRead, InpatientRecordUpdate
from backend.schemas.response import success_response
from backend.services.cage_allocator import allocate_cage
from backend.services.inpatient_service import create_inpatient_record, list_inpatient_records, update_inpatient_record
from backend.services.realtime_hub import dispatch_async, hub

router = APIRouter(prefix="/inpatient-records", tags=["inpatient-records"])
NURSING_LOG_UNDO_WINDOW_MINUTES = 5
CLINIC_NAME_MAP = {
    "C001": "沙河口院区",
    "C002": "甘井子院区",
    "C003": "高新园区院区",
}


@router.get("")
def inpatient_records(clinic_id: str | None = None, medical_record_id: int | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询住院记录列表。"""
    _ = medical_record_id
    data = []
    for item in list_inpatient_records(db, clinic_id):
        base = InpatientRecordRead.model_validate(item).model_dump()
        pet_row = db.query(Pet).filter(Pet.id == item.pet_id).first()
        doctor_row = db.query(User).filter(User.id == item.doctor_id).first()
        base.update(
            {
                "pet_name": f'{pet_row.name}({pet_row.breed or pet_row.species})' if pet_row else f"宠物#{item.pet_id}",
                "doctor_name": doctor_row.full_name if doctor_row else f"医生#{item.doctor_id}",
                "clinic_name": CLINIC_NAME_MAP.get(item.clinic_id, item.clinic_id),
            }
        )
        data.append(base)
    return success_response(data=data)


@router.post("", status_code=status.HTTP_201_CREATED)
def inpatient_create(payload: InpatientRecordCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    """创建住院记录。"""
    record = create_inpatient_record(db, payload)
    cage = db.query(CageUnit).filter(CageUnit.id == record.cage_id).first()
    pet = db.query(Pet).filter(Pet.id == record.pet_id).first()
    pet_name = pet.name if pet else f"宠物#{record.pet_id}"
    cage_code = cage.cage_code if cage else f"#{record.cage_id}"
    dispatch_async(
        hub.send_to_roles(
            ["nurse"],
            title="新护理任务",
            content=f"{pet_name}已入住{cage_code}号笼舍，请查看护理计划",
            level="info",
        )
    )
    data = InpatientRecordRead.model_validate(record).model_dump()
    return success_response(code=201, data=data)


@router.put("/{record_id}")
def inpatient_update(record_id: int, payload: InpatientRecordUpdate, db: Session = Depends(get_db)) -> dict[str, object]:
    """更新住院记录。"""
    record = update_inpatient_record(db, record_id, payload)
    balance = float(record.deposit_amount - record.consumed_amount)
    if balance < 500:
        pet = db.query(Pet).filter(Pet.id == record.pet_id).first()
        pet_name = pet.name if pet else f"宠物#{record.pet_id}"
        dispatch_async(
            hub.send_to_roles(
                ["nurse", "manager"],
                title="欠费预警",
                content=f"{pet_name}押金余额不足500元，请联系主人充值",
                level="warning",
            )
        )
    data = InpatientRecordRead.model_validate(record).model_dump()
    return success_response(data=data)


@router.post("/allocate-cage")
def inpatient_allocate_cage(payload: CageAllocationRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """住院场景下执行笼舍三层分配校验。"""
    cage = allocate_cage(
        db,
        pet_id=payload.pet_id,
        clinic_id=payload.clinic_id,
        preferred_zone_type=payload.preferred_zone_type,
        is_emergency=payload.is_emergency,
    )
    data = CageUnitRead.model_validate(cage).model_dump()
    return success_response(data=data)


@router.get("/{record_id}/nursing-logs")
def nursing_logs(record_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询护理日志。"""
    rows = (
        db.query(NursingLog)
        .filter(NursingLog.inpatient_record_id == record_id, NursingLog.is_voided.is_(False))
        .order_by(NursingLog.logged_at.desc())
        .all()
    )
    data = [
        {
            "id": row.id,
            "inpatient_record_id": row.inpatient_record_id,
            "nurse_id": row.nurse_id,
            "temperature": row.temperature,
            "heart_rate": row.heart_rate,
            "notes": row.notes,
            "logged_at": row.logged_at.isoformat(),
            "undo_deadline": (row.logged_at + timedelta(minutes=NURSING_LOG_UNDO_WINDOW_MINUTES)).isoformat(),
        }
        for row in rows
    ]
    return success_response(data=data)


@router.post("/{record_id}/nursing-logs", status_code=status.HTTP_201_CREATED)
def nursing_log_create(
    record_id: int,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """新增护理日志与体征录入。"""
    inpatient = db.query(InpatientRecord).filter(InpatientRecord.id == record_id).first()
    if inpatient is None:
        return success_response(code=404, message="住院记录不存在")
    nurse_id = int(current_user.id or 0)
    if nurse_id <= 0:
        return success_response(code=401, message="未识别当前登录用户")
    temperature = float(payload.get("temperature", 0) or 0)
    heart_rate = int(payload.get("heart_rate", 0) or 0)

    pet = db.query(Pet).filter(Pet.id == inpatient.pet_id).first()
    species = str(pet.species if pet else "")
    if "犬" in species:
        temp_min, temp_max = 38.0, 39.5
        hr_min, hr_max = 60, 140
    elif "猫" in species:
        temp_min, temp_max = 38.1, 39.2
        hr_min, hr_max = 120, 240
    else:
        temp_min, temp_max = 38.0, 40.0
        hr_min, hr_max = 40, 260
    if temperature < 30 or temperature > 45:
        return success_response(code=422, message="temperature：体温范围应在30-45℃")
    if heart_rate < 30 or heart_rate > 300:
        return success_response(code=422, message="heart_rate：心率范围应在30-300")
    log = NursingLog(
        inpatient_record_id=record_id,
        nurse_id=nurse_id,
        temperature=temperature,
        heart_rate=heart_rate,
        notes=str(payload.get("notes", "")),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    abnormal = temperature < temp_min or temperature > temp_max or heart_rate < hr_min or heart_rate > hr_max
    if inpatient.doctor_id:
        pet_name = pet.name if pet else f"宠物#{inpatient.pet_id}"
        dispatch_async(
            hub.send_to_user(
                inpatient.doctor_id,
                role="doctor",
                title="体征异常告警" if abnormal else "体征录入更新",
                content=(
                    f"{pet_name}体征异常（体温{temperature:.1f}℃，心率{heart_rate}bpm），请立即查看"
                    if abnormal
                    else f"{pet_name}体征已更新（体温{temperature:.1f}℃，心率{heart_rate}bpm）"
                ),
                level="error" if abnormal else "info",
            )
        )
    return success_response(
        code=201,
        data={
            "id": log.id,
            "inpatient_record_id": log.inpatient_record_id,
            "nurse_id": log.nurse_id,
            "temperature": log.temperature,
            "heart_rate": log.heart_rate,
            "notes": log.notes,
            "logged_at": log.logged_at.isoformat(),
            "undo_deadline": (log.logged_at + timedelta(minutes=NURSING_LOG_UNDO_WINDOW_MINUTES)).isoformat(),
            "species": species,
            "temperature_range": [temp_min, temp_max],
            "heart_rate_range": [hr_min, hr_max],
            "is_abnormal": abnormal,
        },
    )


@router.delete("/{record_id}/nursing-logs/{log_id}")
def nursing_log_void(
    record_id: int,
    log_id: int,
    payload: dict | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """撤回护理日志（限录入后5分钟内）。"""
    log = (
        db.query(NursingLog)
        .filter(
            NursingLog.id == log_id,
            NursingLog.inpatient_record_id == record_id,
            NursingLog.is_voided.is_(False),
        )
        .first()
    )
    if log is None:
        return success_response(code=404, message="护理日志不存在或已撤回")
    if int(log.nurse_id or 0) != int(current_user.id or -1):
        return success_response(code=403, message="仅允许原录入人员撤回该条记录")
    deadline = log.logged_at + timedelta(minutes=NURSING_LOG_UNDO_WINDOW_MINUTES)
    if datetime.utcnow() > deadline:
        return success_response(code=409, message=f"撤回窗口已过（{NURSING_LOG_UNDO_WINDOW_MINUTES}分钟）")

    reason = ""
    if isinstance(payload, dict):
        reason = str(payload.get("reason", "") or "").strip()
    log.is_voided = True
    log.void_reason = reason or "录入后主动撤回"
    log.voided_at = datetime.utcnow()
    log.voided_by_id = current_user.id
    db.add(log)
    db.commit()
    return success_response(
        data={
            "id": log.id,
            "inpatient_record_id": log.inpatient_record_id,
            "voided_at": log.voided_at.isoformat() if log.voided_at else None,
            "void_reason": log.void_reason,
            "voided_by_id": log.voided_by_id,
        },
        message="护理日志已撤回",
    )

