"""兽医工作台业务服务。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.exceptions import ApiError
from backend.models.core import Appointment, MedicalRecord
from backend.schemas.medical_record import MedicalRecordCreate


def list_pending_queue(db: Session, doctor_id: int, clinic_id: str | None = None) -> list[Appointment]:
    """查询指定医生工作队列（按优先级展示）。"""
    query = db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.status.in_(["待诊", "就诊中", "已完成"]),
    )
    if clinic_id:
        query = query.filter(Appointment.clinic_id == clinic_id)
    rows = query.all()
    urgency_rank = {"急诊": 3, "优先": 2, "常规": 1}
    return sorted(
        rows,
        key=lambda item: (
            -(float(item.priority_score or 0)),
            -(urgency_rank.get(str(item.urgency_level or "常规"), 0)),
            item.scheduled_time,
        ),
    )


def start_consultation(db: Session, appointment_id: int, doctor_id: int) -> Appointment:
    """将预约状态从待诊流转为就诊中。"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment is None:
        raise ApiError(code=404, message="预约记录不存在")
    if appointment.doctor_id != doctor_id:
        raise ApiError(code=403, message="无权操作该预约")
    if appointment.status != "待诊":
        raise ApiError(code=409, message="当前预约状态不可开始接诊")

    appointment.status = "就诊中"
    db.commit()
    db.refresh(appointment)
    return appointment


def _generate_medical_record_no(db: Session, now: datetime | None = None) -> str:
    """生成病历编号。"""
    current = now or datetime.now()
    prefix = f"MR{current.strftime('%Y%m%d')}"
    latest = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.record_no.like(f"{prefix}%"))
        .order_by(MedicalRecord.record_no.desc())
        .first()
    )
    if latest is None:
        seq = 1
    else:
        seq = int(latest.record_no[-4:]) + 1
    return f"{prefix}{seq:04d}"


def create_medical_record(db: Session, payload: MedicalRecordCreate) -> MedicalRecord:
    """录入病历并将关联预约置为已完成。"""
    appointment = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
    if appointment is None:
        raise ApiError(code=404, message="预约记录不存在")
    if appointment.status != "就诊中":
        raise ApiError(code=409, message="当前预约状态不可录入病历")

    record = MedicalRecord(
        record_no=_generate_medical_record_no(db),
        appointment_id=payload.appointment_id,
        pet_id=payload.pet_id,
        vet_id=payload.vet_id,
        chief_complaint=payload.chief_complaint,
        exam_notes=payload.exam_notes,
        diagnosis=payload.diagnosis,
        treatment_plan=payload.treatment_plan,
        kg_evidence_id=payload.kg_evidence_id,
    )
    db.add(record)
    appointment.status = "已完成"
    db.commit()
    db.refresh(record)
    return record


def list_medical_records(db: Session, pet_id: int | None = None) -> list[MedicalRecord]:
    """查询病历列表，可按宠物过滤。"""
    query = db.query(MedicalRecord)
    if pet_id is not None:
        query = query.filter(MedicalRecord.pet_id == pet_id)
    return query.order_by(MedicalRecord.created_at.desc()).all()


def void_medical_record(db: Session, record_id: int, doctor_id: int, reason: str) -> MedicalRecord:
    """作废病历并回滚预约状态。"""
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if record is None:
        raise ApiError(code=404, message="病历不存在")
    if record.vet_id != doctor_id:
        raise ApiError(code=403, message="无权作废该病历")
    if record.is_voided:
        raise ApiError(code=409, message="病历已作废")
    appointment = db.query(Appointment).filter(Appointment.id == record.appointment_id).first()
    record.is_voided = True
    record.void_reason = reason
    record.voided_at = datetime.now()
    if appointment is not None and appointment.status == "已完成":
        appointment.status = "就诊中"
    db.commit()
    db.refresh(record)
    return record

