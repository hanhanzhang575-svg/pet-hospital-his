"""宠物生命体征监护与记录管理。"""

from datetime import datetime
from sqlalchemy import and_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status

from backend.auth import get_current_user
from backend.models.core import InpatientRecord, NursingLog, User
from backend.schemas.response import success_response

router = APIRouter(prefix="/api/v1/vitals", tags=["vitals"])


@router.get("/inpatient-list")
def get_inpatient_list(
    clinic_id: str | None = None,
    db: Session = Depends(lambda: __import__('backend.db', fromlist=['get_db']).get_db()),
    current_user: User = Depends(get_current_user),
) -> dict:
    """获取住院宠物列表（仅护理人员可访问）。"""
    query = db.query(InpatientRecord).filter(InpatientRecord.status.in_(["待入院", "住院中", "观察中"]))
    if clinic_id:
        query = query.filter(InpatientRecord.clinic_id == clinic_id)
    records = query.order_by(InpatientRecord.admission_time.desc()).all()
    data = [
        {
            "record_id": r.id,
            "pet_id": r.pet_id,
            "cage_id": r.cage_id,
            "clinic_id": r.clinic_id,
            "admission_time": r.admission_time.isoformat() if r.admission_time else None,
            "status": r.status,
        }
        for r in records
    ]
    return success_response(data=data)


@router.get("/history/{record_id}")
def get_vitals_history(
    record_id: int,
    db: Session = Depends(lambda: __import__('backend.db', fromlist=['get_db']).get_db()),
    current_user: User = Depends(get_current_user),
) -> dict:
    """获取住院记录的体征历史数据。"""
    logs = (
        db.query(NursingLog)
        .filter(NursingLog.inpatient_record_id == record_id)
        .order_by(NursingLog.recorded_at.desc())
        .limit(100)
        .all()
    )
    data = [
        {
            "id": log.id,
            "timestamp": log.recorded_at.isoformat() if log.recorded_at else None,
            "temperature": log.get("temperature"),
            "heart_rate": log.get("heart_rate"),
            "respiratory_rate": log.get("respiratory_rate"),
            "blood_pressure": log.get("blood_pressure"),
            "weight_kg": log.get("weight_kg"),
            "notes": log.notes,
        }
        for log in logs
    ]
    return success_response(data=data)


@router.post("/record", status_code=status.HTTP_201_CREATED)
def record_vitals(
    payload: dict,
    db: Session = Depends(lambda: __import__('backend.db', fromlist=['get_db']).get_db()),
    current_user: User = Depends(get_current_user),
) -> dict:
    """录入宠物生命体征数据。"""
    record_id = payload.get("record_id")
    if not record_id:
        return {"code": 400, "message": "record_id 必填", "data": {}}

    record = db.query(InpatientRecord).filter(InpatientRecord.id == record_id).first()
    if not record:
        return {"code": 404, "message": "住院记录不存在", "data": {}}

    vitals_data = {
        "temperature": payload.get("temperature"),
        "heart_rate": payload.get("heart_rate"),
        "respiratory_rate": payload.get("respiratory_rate"),
        "blood_pressure": payload.get("blood_pressure"),
        "weight_kg": payload.get("weight_kg"),
    }

    log = NursingLog(
        inpatient_record_id=record_id,
        recorded_at=datetime.utcnow(),
        vitals=vitals_data,
        notes=payload.get("notes", ""),
        recorded_by_id=current_user.id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return success_response(
        data={
            "id": log.id,
            "record_id": record_id,
            "timestamp": log.recorded_at.isoformat(),
            "vitals": vitals_data,
        },
        message="体征数据已记录"
    )
