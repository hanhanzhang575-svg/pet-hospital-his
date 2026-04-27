"""护理体征录入路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models.core import InpatientRecord, NursingLog, Pet, User
from backend.schemas.response import success_response
from backend.services.realtime_hub import dispatch_async, hub

router = APIRouter(prefix="/nursing", tags=["nursing"])


def _temperature_range(species: str) -> tuple[float, float]:
    """按物种返回体温正常范围。"""
    if species == "犬":
        return (38.0, 39.5)
    if species == "猫":
        return (38.1, 39.2)
    return (38.0, 40.0)


def _heart_rate_range(species: str) -> tuple[int, int]:
    """按物种返回心率正常范围。"""
    if species == "犬":
        return (60, 140)
    if species == "猫":
        return (120, 240)
    return (60, 220)


@router.post("/vital-signs", status_code=status.HTTP_201_CREATED)
def create_vital_signs(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """新增护理体征并推送通知给主治医生。"""
    record_id = int(payload.get("inpatient_record_id", 0) or 0)
    nurse_id = int(current_user.id or 0)
    temperature = float(payload.get("temperature", 0) or 0)
    heart_rate = int(payload.get("heart_rate", 0) or 0)
    notes = str(payload.get("notes", "") or "")

    inpatient = db.query(InpatientRecord).filter(InpatientRecord.id == record_id).first()
    if inpatient is None:
        return success_response(code=404, message="住院记录不存在")
    if nurse_id <= 0:
        return success_response(code=401, message="未识别当前登录用户")

    pet = db.query(Pet).filter(Pet.id == inpatient.pet_id).first()
    species = pet.species if pet else ""
    pet_name = pet.name if pet else f"宠物#{inpatient.pet_id}"
    temp_min, temp_max = _temperature_range(species)
    hr_min, hr_max = _heart_rate_range(species)

    if temperature < 30 or temperature > 45:
        return success_response(code=422, message="temperature：体温范围应在30-45℃")
    if heart_rate < 30 or heart_rate > 300:
        return success_response(code=422, message="heart_rate：心率范围应在30-300bpm")

    abnormal_temp = temperature < temp_min or temperature > temp_max
    abnormal_hr = heart_rate < hr_min or heart_rate > hr_max
    is_abnormal = abnormal_temp or abnormal_hr

    log = NursingLog(
        inpatient_record_id=record_id,
        nurse_id=nurse_id,
        temperature=temperature,
        heart_rate=heart_rate,
        notes=notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    if inpatient.doctor_id:
        dispatch_async(
            hub.send_to_user(
                inpatient.doctor_id,
                role="doctor",
                title="体征录入更新" if not is_abnormal else "体征异常告警",
                content=(
                    f"[{pet_name}]体征已录入，请关注"
                    if not is_abnormal
                    else f"[{pet_name}]体温/心率异常，请立即查看"
                ),
                level="error" if is_abnormal else "info",
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
            "is_abnormal": is_abnormal,
            "species": species,
            "temperature_range": [temp_min, temp_max],
            "heart_rate_range": [hr_min, hr_max],
        },
    )

