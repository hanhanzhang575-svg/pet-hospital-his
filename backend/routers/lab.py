"""医技科工作台路由。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.auth import RequireRole
from backend.database import get_db
from backend.models.core import Appointment, LabTestOrder, MedicalRecord, Owner, Pet, User
from backend.schemas.response import success_response
from backend.services.realtime_hub import dispatch_async, hub

router = APIRouter(prefix="/lab", tags=["lab"])

EXAM_METRIC_DEFS = {
    "blood_routine": {
        "WBC": {"犬": (6.0, 17.0), "猫": (5.5, 19.5), "其他": (0.0, 9999.0)},
        "RBC": {"犬": (5.5, 8.5), "猫": (5.0, 10.0), "其他": (0.0, 9999.0)},
        "HGB": {"犬": (120.0, 180.0), "猫": (80.0, 150.0), "其他": (0.0, 9999.0)},
        "HCT": {"犬": (37.0, 55.0), "猫": (24.0, 45.0), "其他": (0.0, 9999.0)},
        "PLT": {"犬": (200.0, 500.0), "猫": (300.0, 700.0), "其他": (0.0, 9999.0)},
    },
    "biochemistry": {
        "ALT": {"犬": (10.0, 100.0), "猫": (10.0, 100.0), "其他": (0.0, 9999.0)},
        "AST": {"犬": (10.0, 50.0), "猫": (10.0, 50.0), "其他": (0.0, 9999.0)},
        "BUN": {"犬": (7.0, 27.0), "猫": (14.0, 36.0), "其他": (0.0, 9999.0)},
        "Creatinine": {"犬": (0.5, 1.5), "猫": (0.6, 2.4), "其他": (0.0, 9999.0)},
        "GLU": {"犬": (70.0, 138.0), "猫": (64.0, 170.0), "其他": (0.0, 9999.0)},
        "TP": {"犬": (54.0, 82.0), "猫": (57.0, 89.0), "其他": (0.0, 9999.0)},
    },
}


def _species_key(value: str) -> str:
    text = str(value or "")
    if "犬" in text:
        return "犬"
    if "猫" in text:
        return "猫"
    return "其他"


def _calc_abnormal_counts(exam_type: str, structured_data: dict[str, object], species: str) -> tuple[int, int]:
    metric_defs = EXAM_METRIC_DEFS.get(exam_type, {})
    abnormal = 0
    critical = 0
    sp = _species_key(species)
    for metric, conf in metric_defs.items():
        raw = structured_data.get(metric)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        low, high = conf.get(sp, conf.get("其他", (0.0, 9999.0)))
        if value < low or value > high:
            abnormal += 1
            if value < low / 2 or value > high * 2:
                critical += 1
    return abnormal, critical


@router.get("/pending-tests")
def pending_tests(
    clinic_id: str | None = None,
    current_user: User = Depends(RequireRole(["lab_tech", "admin", "manager"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """查询待检查/检查中队列。"""
    _ = current_user
    query = db.query(LabTestOrder).filter(LabTestOrder.status.in_(["待检查", "检查中"]))
    if clinic_id:
        query = query.filter(LabTestOrder.clinic_id == clinic_id)
    rows = query.order_by(LabTestOrder.created_at.asc()).all()
    data = []
    for row in rows:
        pet = db.query(Pet).filter(Pet.id == row.pet_id).first()
        owner = db.query(Owner).filter(Owner.id == pet.owner_id).first() if pet else None
        doctor = db.query(User).filter(User.id == row.doctor_id).first()
        appointment = db.query(Appointment).filter(Appointment.id == row.appointment_id).first() if row.appointment_id else None
        chief_complaint = ""
        if appointment:
            record = (
                db.query(MedicalRecord)
                .filter(MedicalRecord.appointment_id == appointment.id)
                .order_by(MedicalRecord.id.desc())
                .first()
            )
            chief_complaint = record.chief_complaint if record and record.chief_complaint else ""
        data.append(
            {
                "id": row.id,
                "appointment_id": row.appointment_id,
                "record_code": row.record_code or "",
                "pet_name": pet.name if pet else f"宠物#{row.pet_id}",
                "pet_species": pet.species if pet else "",
                "pet_breed": pet.breed if pet else "",
                "pet_age_years": (
                    max((datetime.now().date() - pet.birth_date).days // 365, 0)
                    if pet and pet.birth_date
                    else 0
                ),
                "pet_weight": pet.weight if pet and pet.weight is not None else 0,
                "owner_name": owner.name if owner else "",
                "exam_items": row.test_items or [],
                "requesting_doctor": doctor.full_name if doctor else f"医生#{row.doctor_id}",
                "requesting_doctor_id": row.doctor_id,
                "urgency_level": row.urgency_level,
                "requested_at": row.created_at.isoformat(),
                "status": row.status,
                "chief_complaint": chief_complaint,
            }
        )
    return success_response(data=data)


@router.post("/start-exam/{appointment_id}")
def start_exam(
    appointment_id: int,
    current_user: User = Depends(RequireRole(["lab_tech", "admin", "manager"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """将检查单状态置为检查中。"""
    _ = current_user
    order = db.query(LabTestOrder).filter(LabTestOrder.appointment_id == appointment_id).order_by(LabTestOrder.id.desc()).first()
    if order is None:
        return success_response(code=404, message="未找到对应检查单")
    if order.status == "已完成":
        return success_response(code=409, message="当前检查单已完成，无法再次开始")
    order.status = "检查中"
    db.commit()
    db.refresh(order)
    return success_response(data={"id": order.id, "appointment_id": appointment_id, "status": order.status})


@router.post("/submit-result", status_code=status.HTTP_201_CREATED)
def submit_result(
    payload: dict,
    current_user: User = Depends(RequireRole(["lab_tech", "admin", "manager"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """提交检验结果并通知医生。"""
    _ = current_user
    appointment_id = int(payload.get("appointment_id", 0) or 0)
    if appointment_id <= 0:
        return success_response(code=422, message="appointment_id：请传入有效预约ID")

    order = db.query(LabTestOrder).filter(LabTestOrder.appointment_id == appointment_id).order_by(LabTestOrder.id.desc()).first()
    if order is None:
        return success_response(code=404, message="检查单不存在")

    exam_type = str(payload.get("exam_type") or "").strip()
    structured_data = payload.get("structured_data") or {}
    if not isinstance(structured_data, dict):
        return success_response(code=422, message="structured_data：必须是JSON对象")
    image_files = payload.get("image_files") or []
    if not isinstance(image_files, list):
        return success_response(code=422, message="image_files：必须是数组")
    notes = str(payload.get("notes") or "")

    pet = db.query(Pet).filter(Pet.id == order.pet_id).first()
    abnormal_count, critical_count = _calc_abnormal_counts(exam_type, structured_data, pet.species if pet else "")
    order.exam_type = exam_type
    order.structured_data = structured_data
    order.panel_values = {k: float(v) for k, v in structured_data.items() if isinstance(v, (int, float))}
    order.image_urls = [str(x) for x in image_files]
    order.notes = notes
    order.status = "已完成"
    order.abnormal_count = abnormal_count
    order.critical_count = critical_count
    order.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(order)

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment:
        appointment.status = "就诊中" if appointment.status == "待诊" else appointment.status
        db.commit()

    pet_name = pet.name if pet else f"宠物#{order.pet_id}"
    summary = f"🔬 {pet_name}的{exam_type or '检验'}报告已出，发现{abnormal_count}个异常指标，请查看"
    dispatch_async(
        hub.send_to_user(
            order.doctor_id,
            role="doctor",
            title="检验报告已出",
            content=summary,
            level="error" if critical_count > 0 else "info",
        )
    )
    return success_response(
        code=201,
        data={
            "id": order.id,
            "appointment_id": appointment_id,
            "status": order.status,
            "abnormal_count": abnormal_count,
            "critical_count": critical_count,
            "completed_at": order.completed_at.isoformat() if order.completed_at else "",
        },
    )


@router.get("/results")
def results(
    clinic_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    pet_name: str | None = None,
    exam_type: str | None = None,
    current_user: User = Depends(RequireRole(["lab_tech", "admin", "manager", "doctor"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """查询已完成检验结果。"""
    _ = current_user
    query = db.query(LabTestOrder).filter(LabTestOrder.status == "已完成")
    if clinic_id:
        query = query.filter(LabTestOrder.clinic_id == clinic_id)
    if exam_type:
        query = query.filter(LabTestOrder.exam_type == exam_type)
    rows = query.order_by(LabTestOrder.completed_at.desc()).all()
    data = []
    for row in rows:
        pet = db.query(Pet).filter(Pet.id == row.pet_id).first()
        doctor = db.query(User).filter(User.id == row.doctor_id).first()
        completed_at = row.completed_at.isoformat() if row.completed_at else ""
        if date_from and completed_at and completed_at[:10] < date_from:
            continue
        if date_to and completed_at and completed_at[:10] > date_to:
            continue
        if pet_name and pet and pet_name not in pet.name:
            continue
        data.append(
            {
                "id": row.id,
                "appointment_id": row.appointment_id,
                "record_code": row.record_code or "",
                "pet_name": pet.name if pet else f"宠物#{row.pet_id}",
                "pet_species": pet.species if pet else "",
                "exam_type": row.exam_type or "",
                "exam_items": row.test_items or [],
                "structured_data": row.structured_data or {},
                "image_files": row.image_urls or [],
                "notes": row.notes or "",
                "requesting_doctor": doctor.full_name if doctor else f"医生#{row.doctor_id}",
                "abnormal_count": row.abnormal_count or 0,
                "critical_count": row.critical_count or 0,
                "completed_at": completed_at,
            }
        )
    return success_response(data=data)


@router.get("/stats")
def stats(
    clinic_id: str | None = None,
    current_user: User = Depends(RequireRole(["lab_tech", "admin", "manager"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """检验今日统计。"""
    _ = current_user
    query = db.query(LabTestOrder)
    if clinic_id:
        query = query.filter(LabTestOrder.clinic_id == clinic_id)
    rows = query.all()
    today = datetime.now().date()
    pending = sum(1 for r in rows if r.status == "待检查")
    running = sum(1 for r in rows if r.status == "检查中")
    completed = sum(
        1
        for r in rows
        if r.status == "已完成" and r.completed_at is not None and r.completed_at.date() == today
    )
    return success_response(
        data={
            "pending": pending,
            "in_progress": running,
            "completed_today": completed,
        }
    )
