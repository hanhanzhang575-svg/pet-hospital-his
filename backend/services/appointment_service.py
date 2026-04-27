"""门诊挂号业务服务。"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.exceptions import ApiError
from backend.models.core import Appointment, Pet, User
from backend.schemas.appointment import AppointmentCreate, AppointmentUpdate
from backend.services.queue_priority import calculate_priority_score


def _calculate_pet_age_years(birth_date: date | str | None) -> float:
    """将宠物生日转换为年龄（年）。"""
    if not birth_date:
        return 0.0
    if isinstance(birth_date, date):
        birth = datetime.combine(birth_date, datetime.min.time())
    else:
        try:
            birth = datetime.strptime(birth_date, "%Y-%m-%d")
        except ValueError:
            return 0.0
    delta_days = max((datetime.now() - birth).days, 0)
    return round(delta_days / 365.0, 2)


def _generate_record_code(db: Session, scheduled_time: datetime) -> str:
    """按日期+固定科室码+类型码+流水生成诊单编号。"""
    date_part = scheduled_time.strftime("%Y%m%d")
    prefix = f"{date_part}SUA"
    latest = db.query(Appointment).filter(Appointment.record_code.like(f"{prefix}%")).order_by(Appointment.record_code.desc()).first()
    if latest is None:
        seq = 1
    else:
        seq = int(latest.record_code[-3:]) + 1
    return f"{prefix}{seq:03d}"


def create_appointment(db: Session, payload: AppointmentCreate) -> Appointment:
    """创建预约挂号并执行并发时间槽锁校验。"""
    pet = db.query(Pet).filter(Pet.id == payload.pet_id).first()
    if pet is None:
        raise ApiError(code=404, message="宠物档案不存在")

    doctor = db.query(User).filter(User.id == payload.doctor_id, User.is_active.is_(True)).first()
    if doctor is None:
        raise ApiError(code=404, message="医生不存在")

    now = datetime.now()
    waiting_minutes = max((payload.scheduled_time - now).total_seconds() / 60.0, 0.0)
    age_years = _calculate_pet_age_years(pet.birth_date)
    priority_score = calculate_priority_score(payload.urgency_level, waiting_minutes, age_years)

    appointment = Appointment(
        record_code=_generate_record_code(db=db, scheduled_time=payload.scheduled_time),
        pet_id=payload.pet_id,
        doctor_id=payload.doctor_id,
        clinic_id=payload.clinic_id,
        scheduled_time=payload.scheduled_time,
        urgency_level=payload.urgency_level,
        status="待诊",
        priority_score=priority_score,
        max_capacity=10,
        is_leave=False,
    )

    try:
        db.add(appointment)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(code=409, message="该医生当前时段号源已被占用") from exc

    db.refresh(appointment)
    return appointment


def list_appointments(
    db: Session,
    clinic_id: str | None = None,
    doctor_id: int | None = None,
    pet_id: int | None = None,
    status: str | None = None,
) -> list[Appointment]:
    """查询预约挂号列表，可按院区、医生和状态过滤。"""
    query = db.query(Appointment)
    if clinic_id:
        query = query.filter(Appointment.clinic_id == clinic_id)
    if doctor_id is not None:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if pet_id is not None:
        query = query.filter(Appointment.pet_id == pet_id)
    if status:
        query = query.filter(Appointment.status == status)
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


def cancel_appointment(db: Session, appointment_id: int) -> Appointment:
    """取消预约挂号。"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment is None:
        raise ApiError(code=404, message="预约记录不存在")
    if appointment.status == "已取消":
        raise ApiError(code=409, message="该预约已取消")
    appointment.status = "已取消"
    db.commit()
    db.refresh(appointment)
    return appointment


def update_appointment(db: Session, appointment_id: int, payload: AppointmentUpdate) -> Appointment:
    """更新预约挂号（用于排班调整）。"""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if appointment is None:
        raise ApiError(code=404, message="预约记录不存在")
    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        setattr(appointment, key, value)
    if appointment.scheduled_time:
        pet = db.query(Pet).filter(Pet.id == appointment.pet_id).first()
        waiting_minutes = max((appointment.scheduled_time - datetime.now()).total_seconds() / 60.0, 0.0)
        age_years = _calculate_pet_age_years(pet.birth_date if pet else None)
        appointment.priority_score = calculate_priority_score(appointment.urgency_level, waiting_minutes, age_years)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(code=409, message="该医生当前时段号源已被占用") from exc
    db.refresh(appointment)
    return appointment

