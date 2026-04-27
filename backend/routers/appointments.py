"""Appointment and schedule management routes."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.core import Appointment, Owner, Pet, Role, User
from backend.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate
from backend.schemas.response import success_response
from backend.services.appointment_service import cancel_appointment, create_appointment, list_appointments, update_appointment
from backend.services.realtime_hub import dispatch_async, hub

router = APIRouter(prefix="/appointments", tags=["appointments"])

CLINIC_NAME_MAP = {
    "C001": "沙河口院区",
    "C002": "甘井子院区",
    "C003": "高新区院区",
}

ACTIVE_APPOINTMENT_STATUS = {"待诊", "就诊中", "已完成"}


def _period_of(dt: datetime) -> str:
    return "morning" if dt.hour < 13 else "afternoon"


def _slot_window(dt: datetime) -> tuple[datetime, datetime]:
    start_hour = 8 if dt.hour < 13 else 14
    slot_start = dt.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    return slot_start, slot_start + timedelta(hours=4)


def _doctor_department(_clinic_id: str, doctor_name: str) -> str:
    if "内科" in doctor_name:
        return "内科"
    if "外科" in doctor_name:
        return "外科"
    if "皮肤" in doctor_name:
        return "皮肤科"
    if "眼" in doctor_name:
        return "眼科"
    if "牙" in doctor_name:
        return "牙科"
    return "综合门诊"


def _doctor_avatar(doctor_name: str) -> str:
    plain = doctor_name.replace("(", "").replace(")", "")
    return f"Dr.{plain[:1] or 'V'}"


def _slot_bookings(db: Session, schedule_row: Appointment) -> list[Appointment]:
    slot_start, slot_end = _slot_window(schedule_row.scheduled_time)
    return (
        db.query(Appointment)
        .filter(Appointment.doctor_id == schedule_row.doctor_id, Appointment.clinic_id == schedule_row.clinic_id)
        .filter(Appointment.scheduled_time >= slot_start, Appointment.scheduled_time < slot_end)
        .filter(Appointment.status.in_(list(ACTIVE_APPOINTMENT_STATUS)))
        .order_by(Appointment.priority_score.desc(), Appointment.scheduled_time.asc())
        .all()
    )


def _booked_count(db: Session, doctor_id: int, clinic_id: str, dt: datetime) -> int:
    slot_start, slot_end = _slot_window(dt)
    return (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor_id, Appointment.clinic_id == clinic_id)
        .filter(Appointment.scheduled_time >= slot_start, Appointment.scheduled_time < slot_end)
        .filter(Appointment.status.in_(list(ACTIVE_APPOINTMENT_STATUS)))
        .count()
    )


def _peak_prediction_for_slot(
    db: Session,
    doctor_id: int,
    clinic_id: str,
    date_key: str,
    period: str,
    max_capacity: int,
) -> tuple[bool, float]:
    current = datetime.strptime(f"{date_key} {'08:00:00' if period == 'morning' else '14:00:00'}", "%Y-%m-%d %H:%M:%S")
    begin = current - timedelta(days=30)
    weekday = current.weekday()
    same_period_rows = (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor_id, Appointment.clinic_id == clinic_id)
        .filter(Appointment.scheduled_time >= begin, Appointment.scheduled_time < current)
        .all()
    )
    bucket: defaultdict[str, int] = defaultdict(int)
    for row in same_period_rows:
        if row.status not in ACTIVE_APPOINTMENT_STATUS:
            continue
        if row.scheduled_time.weekday() != weekday:
            continue
        if _period_of(row.scheduled_time) != period:
            continue
        bucket[row.scheduled_time.date().isoformat()] += 1
    if not bucket:
        return False, 0.0
    predicted = sum(bucket.values()) / max(len(bucket), 1)
    capacity = float(max(max_capacity, 1))
    return predicted >= capacity * 0.85, round(predicted, 2)


def _find_transfer_target(db: Session, source_row: Appointment) -> tuple[Appointment | None, int]:
    doctor = db.query(User).filter(User.id == source_row.doctor_id).first()
    if doctor is None:
        return None, 0
    department = _doctor_department(source_row.clinic_id, doctor.full_name)
    slot_start, slot_end = _slot_window(source_row.scheduled_time)
    candidates = (
        db.query(Appointment, User)
        .join(User, User.id == Appointment.doctor_id)
        .filter(Appointment.clinic_id == source_row.clinic_id)
        .filter(Appointment.scheduled_time >= slot_start, Appointment.scheduled_time < slot_end)
        .filter(Appointment.status == "排班", Appointment.is_leave.is_(False))
        .filter(Appointment.doctor_id != source_row.doctor_id)
        .all()
    )
    best_row: Appointment | None = None
    best_available = -1
    for row, target_doctor in candidates:
        if _doctor_department(source_row.clinic_id, target_doctor.full_name) != department:
            continue
        booked = _booked_count(db, row.doctor_id, row.clinic_id, row.scheduled_time)
        available = int(row.max_capacity or 10) - booked
        if available > best_available:
            best_available = available
            best_row = row
    if best_row is None or best_available <= 0:
        return None, 0
    return best_row, best_available


def _broadcast_schedule_changed(title: str, content: str, level: str = "info") -> None:
    dispatch_async(hub.send_to_roles(["doctor", "manager", "receptionist"], title=title, content=content, level=level))
    dispatch_async(hub.send_to_roles(["lab_tech"], title=title, content=content, level=level))


@router.post("", status_code=status.HTTP_201_CREATED)
def appointment_create(payload: AppointmentCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    record = create_appointment(db, payload)
    pet = db.query(Pet).filter(Pet.id == record.pet_id).first()
    pet_name = pet.name if pet else f"宠物#{record.pet_id}"
    content = f"{pet_name} 已加入待诊队列，优先级评分 {record.priority_score:.1f}"
    if record.urgency_level == "急诊":
        content = f"{pet_name} 因高优先级评分 {record.priority_score:.1f} 已插入待诊队列前列，请优先接诊。"
    dispatch_async(
        hub.send_to_user(
            record.doctor_id,
            role="doctor",
            title="新患者加入",
            content=content,
            level="info",
        )
    )
    data = AppointmentRead.model_validate(record).model_dump()
    return success_response(code=201, data=data)


@router.get("")
def appointments(
    clinic_id: str | None = None,
    doctor_id: int | None = None,
    pet_id: int | None = None,
    status: str | None = None,
    limit: int = 120,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    rows = list_appointments(db, clinic_id, doctor_id, pet_id, status)
    total = len(rows)
    safe_limit = max(20, min(int(limit or 120), 300))
    safe_offset = max(0, int(offset or 0))
    sliced = rows[safe_offset : safe_offset + safe_limit]
    data = []
    for item in sliced:
        base = AppointmentRead.model_validate(item).model_dump()
        pet_row = db.query(Pet).filter(Pet.id == item.pet_id).first()
        doctor_row = db.query(User).filter(User.id == item.doctor_id).first()
        base.update(
            {
                "pet_name": f"{pet_row.name}({pet_row.breed or pet_row.species})" if pet_row else f"宠物#{item.pet_id}",
                "doctor_name": doctor_row.full_name if doctor_row else f"医生#{item.doctor_id}",
                "clinic_name": CLINIC_NAME_MAP.get(item.clinic_id, item.clinic_id),
            }
        )
        data.append(base)
    return success_response(data=data, total=total, limit=safe_limit, offset=safe_offset)


@router.post("/{appointment_id}/cancel")
def appointment_cancel(appointment_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    record = cancel_appointment(db, appointment_id)
    data = AppointmentRead.model_validate(record).model_dump()
    return success_response(data=data, message="取消成功")


@router.put("/{appointment_id}")
def appointment_update(appointment_id: int, payload: AppointmentUpdate, db: Session = Depends(get_db)) -> dict[str, object]:
    record = update_appointment(db, appointment_id, payload)
    data = AppointmentRead.model_validate(record).model_dump()
    return success_response(data=data, message="更新成功")


@router.get("/schedule/week")
def schedule_week(clinic_id: str = "C001", week_start: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    if week_start:
        start = datetime.strptime(week_start, "%Y-%m-%d").date()
    else:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    doctor_rows = (
        db.query(User, Role)
        .join(Role, Role.id == User.role_id)
        .filter(Role.name == "doctor", User.is_active.is_(True), User.branch_code == clinic_id)
        .order_by(User.id.asc())
        .all()
    )
    schedules = (
        db.query(Appointment)
        .filter(Appointment.clinic_id == clinic_id)
        .filter(Appointment.scheduled_time >= datetime.combine(start, datetime.min.time()))
        .filter(Appointment.scheduled_time < datetime.combine(end, datetime.min.time()))
        .order_by(Appointment.scheduled_time.asc())
        .all()
    )
    slots: dict[tuple[int, str, str], Appointment] = {}
    demand_counter: dict[tuple[int, str, str], int] = {}
    for item in schedules:
        period = _period_of(item.scheduled_time)
        date_key = item.scheduled_time.date().isoformat()
        slot_key = (item.doctor_id, date_key, period)
        if item.status in ACTIVE_APPOINTMENT_STATUS:
            demand_counter[slot_key] = demand_counter.get(slot_key, 0) + 1
        if slot_key not in slots or item.status == "排班":
            slots[slot_key] = item

    doctors = [
        {
            "id": user.id,
            "full_name": user.full_name,
            "branch_code": user.branch_code,
            "department": _doctor_department(clinic_id, user.full_name),
            "avatar": _doctor_avatar(user.full_name),
        }
        for user, _ in doctor_rows
    ]

    rows = []
    for doctor in doctors:
        for day in range(7):
            current = start + timedelta(days=day)
            date_key = current.isoformat()
            for period in ("morning", "afternoon"):
                row = slots.get((doctor["id"], date_key, period))
                booked = demand_counter.get((doctor["id"], date_key, period), 0)
                max_capacity = int(row.max_capacity if row else 10)
                rate = round((booked / max(max_capacity, 1)) * 100, 1)
                is_peak, predicted = _peak_prediction_for_slot(db, doctor["id"], clinic_id, date_key, period, max_capacity)
                rows.append(
                    {
                        "doctor_id": doctor["id"],
                        "doctor_name": doctor["full_name"],
                        "department": doctor["department"],
                        "avatar": doctor["avatar"],
                        "clinic_id": clinic_id,
                        "date": date_key,
                        "period": period,
                        "appointment_id": row.id if row else None,
                        "scheduled_time": row.scheduled_time.isoformat() if row else None,
                        "max_capacity": max_capacity,
                        "booked_count": int(booked),
                        "utilization_rate": rate,
                        "is_leave": bool(row.is_leave) if row else False,
                        "status": "请假" if row and row.is_leave else ("已排班" if row else "未排班"),
                        "schedule_note": row.schedule_note if row else "",
                        "is_peak": is_peak,
                        "predicted_count": predicted,
                    }
                )
    return success_response(data={"week_start": start.isoformat(), "clinic_id": clinic_id, "doctors": doctors, "slots": rows})


@router.get("/schedule/{appointment_id}/patients")
def schedule_slot_patients(appointment_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    row = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if row is None:
        return success_response(code=404, message="排班记录不存在")
    patients = []
    for booking in _slot_bookings(db, row):
        pet = db.query(Pet).filter(Pet.id == booking.pet_id).first()
        owner = db.query(Owner).filter(Owner.id == pet.owner_id).first() if pet else None
        patients.append(
            {
                "id": booking.id,
                "pet_name": pet.name if pet else f"宠物#{booking.pet_id}",
                "owner_name": owner.name if owner else "",
                "urgency_level": booking.urgency_level,
                "status": booking.status,
            }
        )
    return success_response(data=patients)


@router.post("/schedule/create", status_code=status.HTTP_201_CREATED)
def schedule_create(payload: dict, db: Session = Depends(get_db)) -> dict[str, object]:
    doctor_id = int(payload.get("doctor_id"))
    clinic_id = str(payload.get("clinic_id"))
    date_str = str(payload.get("date"))
    period = str(payload.get("period", "morning"))
    max_capacity = max(1, min(30, int(payload.get("max_capacity", 10))))
    note = str(payload.get("schedule_note", ""))
    hour = 8 if period == "morning" else 14
    scheduled = datetime.strptime(f"{date_str} {hour:02d}:01:00", "%Y-%m-%d %H:%M:%S")
    placeholder_pet = db.query(Pet).order_by(Pet.id.asc()).first()
    doctor = db.query(User).filter(User.id == doctor_id).first()
    if placeholder_pet is None:
        return success_response(code=400, message="缺少宠物基础数据，无法创建排班")
    if doctor is None:
        return success_response(code=404, message="医生不存在")
    exists = (
        db.query(Appointment)
        .filter(Appointment.clinic_id == clinic_id, Appointment.doctor_id == doctor_id, Appointment.scheduled_time == scheduled)
        .first()
    )
    if exists:
        exists.max_capacity = max_capacity
        exists.is_leave = False
        exists.schedule_note = note
        db.commit()
        db.refresh(exists)
        _broadcast_schedule_changed("排班更新", f"{doctor.full_name} {date_str} {'上午' if period == 'morning' else '下午'} 排班已更新。")
        return success_response(data={"id": exists.id}, message="排班已更新")

    record = Appointment(
        record_code=f"SCH{scheduled:%y%m%d}{doctor_id:03d}{'M' if period == 'morning' else 'A'}NEW",
        pet_id=placeholder_pet.id,
        doctor_id=doctor_id,
        clinic_id=clinic_id,
        scheduled_time=scheduled,
        urgency_level="常规",
        status="排班",
        priority_score=0.0,
        max_capacity=max_capacity,
        is_leave=False,
        schedule_note=note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    dispatch_async(
        hub.send_to_user(
            doctor_id,
            role="doctor",
            title="排班更新",
            content=f"您的 {date_str} {'上午' if period == 'morning' else '下午'} 排班已新增，最大接诊数 {max_capacity}。",
            level="info",
        )
    )
    _broadcast_schedule_changed("号源池刷新", f"{doctor.full_name} {date_str} {'上午' if period == 'morning' else '下午'} 已新增排班。")
    return success_response(code=201, data={"id": record.id})


@router.post("/schedule/{appointment_id}/leave")
def schedule_mark_leave(appointment_id: int, payload: dict | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    body = payload or {}
    action = str(body.get("action", "auto_transfer")).strip()
    reason = str(body.get("reason", "")).strip()
    row = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if row is None:
        return success_response(code=404, message="排班记录不存在")
    booked_rows = _slot_bookings(db, row)
    moved = 0
    transfer_target_row: Appointment | None = None
    transfer_target_doctor: User | None = None
    if action == "auto_transfer" and booked_rows:
        target_row, available = _find_transfer_target(db, row)
        if target_row is None or available <= 0:
            return success_response(code=422, message="未找到同院区同科室空闲医生，无法自动转移")
        transfer_target_row = target_row
        transfer_target_doctor = db.query(User).filter(User.id == target_row.doctor_id).first()
        for item in booked_rows[:available]:
            item.doctor_id = target_row.doctor_id
            item.clinic_id = target_row.clinic_id
            moved += 1
    elif action == "sms_cancel":
        if not reason:
            return success_response(code=422, message="短信退号需填写停诊原因")
        for item in booked_rows:
            item.status = "已取消"

    row.is_leave = True
    row.schedule_note = reason or "请假"
    db.commit()
    db.refresh(row)

    dispatch_async(
        hub.send_to_user(
            row.doctor_id,
            role="doctor",
            title="排班更新",
            content=f"您的 {row.scheduled_time.strftime('%Y-%m-%d %H:%M')} 排班已做停诊处理。",
            level="warning",
        )
    )

    target_text = ""
    if action == "auto_transfer" and moved > 0 and transfer_target_row is not None:
        period_text = "上午" if _period_of(transfer_target_row.scheduled_time) == "morning" else "下午"
        target_text = f"{transfer_target_doctor.full_name if transfer_target_doctor else '其他医生'} {period_text}时段"
    return success_response(
        data={"id": row.id, "is_leave": True, "moved_count": moved, "target_slot": target_text},
        message=(f"已将 {moved} 位患者转移至 {target_text}" if action == "auto_transfer" and moved > 0 else "停诊处理完成"),
    )


@router.delete("/schedule/{appointment_id}")
def schedule_delete(appointment_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    row = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if row is None:
        return success_response(code=404, message="排班记录不存在")
    booked_count = len(_slot_bookings(db, row))
    if booked_count > 0:
        return success_response(code=409, message="该时段已有预约，无法直接删除")
    doctor = db.query(User).filter(User.id == row.doctor_id).first()
    time_text = row.scheduled_time.strftime("%Y-%m-%d %H:%M")
    db.delete(row)
    db.commit()
    if doctor:
        _broadcast_schedule_changed("号源池刷新", f"{doctor.full_name} {time_text} 排班已删除。", level="warning")
    return success_response(data={"deleted": True})


@router.post("/schedule/copy-last-week")
def schedule_copy_last_week(clinic_id: str = "C001", week_start: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    if week_start:
        start = datetime.strptime(week_start, "%Y-%m-%d").date()
    else:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
    last_start = start - timedelta(days=7)
    created = 0
    skipped = 0
    last_rows = (
        db.query(Appointment)
        .filter(Appointment.clinic_id == clinic_id, Appointment.status == "排班")
        .filter(Appointment.scheduled_time >= datetime.combine(last_start, datetime.min.time()))
        .filter(Appointment.scheduled_time < datetime.combine(start, datetime.min.time()))
        .all()
    )
    placeholder_pet = db.query(Pet).order_by(Pet.id.asc()).first()
    if placeholder_pet is None:
        return success_response(code=400, message="缺少宠物基础数据，无法复制排班")
    for row in last_rows:
        target_time = row.scheduled_time + timedelta(days=7)
        exists = (
            db.query(Appointment)
            .filter(Appointment.clinic_id == clinic_id, Appointment.doctor_id == row.doctor_id, Appointment.scheduled_time == target_time)
            .first()
        )
        if exists:
            skipped += 1
            continue
        new_item = Appointment(
            record_code=f"CPY{target_time:%y%m%d}{row.doctor_id:03d}{created:02d}",
            pet_id=placeholder_pet.id,
            doctor_id=row.doctor_id,
            clinic_id=clinic_id,
            scheduled_time=target_time,
            urgency_level="常规",
            status="排班",
            priority_score=0.0,
            max_capacity=row.max_capacity,
            is_leave=row.is_leave,
            schedule_note=row.schedule_note,
        )
        db.add(new_item)
        created += 1
    db.commit()
    _broadcast_schedule_changed("号源池刷新", f"排班批量复制完成，新增 {created} 条，跳过 {skipped} 条。")
    return success_response(
        data={"copied": created, "skipped": skipped},
        message=f"已复制 {created} 条排班记录，{skipped} 个时段因已存在排班被跳过",
    )


@router.get("/schedule/peak-prediction")
def schedule_peak_prediction(clinic_id: str = "C001", week_start: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    if week_start:
        start = datetime.strptime(week_start, "%Y-%m-%d").date()
    else:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)
    schedule_rows = (
        db.query(Appointment)
        .filter(Appointment.clinic_id == clinic_id, Appointment.status == "排班", Appointment.is_leave.is_(False))
        .filter(Appointment.scheduled_time >= datetime.combine(start, datetime.min.time()))
        .filter(Appointment.scheduled_time < datetime.combine(end, datetime.min.time()))
        .all()
    )
    peaks = []
    for row in schedule_rows:
        date_key = row.scheduled_time.date().isoformat()
        period = _period_of(row.scheduled_time)
        is_peak, predicted = _peak_prediction_for_slot(db, row.doctor_id, row.clinic_id, date_key, period, int(row.max_capacity or 10))
        if not is_peak:
            continue
        peaks.append(
            {
                "appointment_id": row.id,
                "doctor_id": row.doctor_id,
                "clinic_id": row.clinic_id,
                "date": date_key,
                "period": period,
                "predicted_count": predicted,
                "threshold": round(float(row.max_capacity or 10) * 0.85, 2),
            }
        )
    return success_response(data=peaks)


@router.get("/schedule/recommendations")
def schedule_recommendations(clinic_id: str = "C001", week_start: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    if week_start:
        start = datetime.strptime(week_start, "%Y-%m-%d").date()
    else:
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=7)

    schedule_rows = (
        db.query(Appointment)
        .filter(Appointment.clinic_id == clinic_id, Appointment.status == "排班", Appointment.is_leave.is_(False))
        .filter(Appointment.scheduled_time >= datetime.combine(start, datetime.min.time()))
        .filter(Appointment.scheduled_time < datetime.combine(end, datetime.min.time()))
        .all()
    )
    doctor_map = {user.id: user for user in db.query(User).filter(User.branch_code == clinic_id, User.is_active.is_(True)).all()}

    recommendations: list[dict[str, object]] = []
    for row in schedule_rows:
        date_key = row.scheduled_time.date().isoformat()
        period = _period_of(row.scheduled_time)
        booked = _booked_count(db, row.doctor_id, clinic_id, row.scheduled_time)
        cap = max(1, int(row.max_capacity or 10))
        util = round((booked / cap) * 100, 1)
        is_peak, predicted = _peak_prediction_for_slot(db, row.doctor_id, clinic_id, date_key, period, cap)
        doctor = doctor_map.get(row.doctor_id)
        doctor_name = doctor.full_name if doctor else f"医生#{row.doctor_id}"
        department = _doctor_department(clinic_id, doctor_name)

        if is_peak and util >= 85:
            add_capacity = max(2, int(round((predicted - cap) + 2)))
            recommendations.append(
                {
                    "type": "expand_capacity",
                    "priority": "high" if util >= 100 else "medium",
                    "doctor_id": row.doctor_id,
                    "doctor_name": doctor_name,
                    "department": department,
                    "date": date_key,
                    "period": period,
                    "current_capacity": cap,
                    "booked": booked,
                    "predicted_demand": predicted,
                    "suggested_capacity": cap + add_capacity,
                    "message": f"{date_key} {period} 预计高峰，建议号源从 {cap} 提升至 {cap + add_capacity}。",
                }
            )

        if util >= 95:
            same_day_candidates = [
                item
                for item in schedule_rows
                if item.id != row.id and item.scheduled_time.date().isoformat() == date_key and _period_of(item.scheduled_time) == period
            ]
            best_target = None
            best_target_rate = 999.0
            for candidate in same_day_candidates:
                candidate_doctor = doctor_map.get(candidate.doctor_id)
                if candidate_doctor is None:
                    continue
                if _doctor_department(clinic_id, candidate_doctor.full_name) != department:
                    continue
                candidate_booked = _booked_count(db, candidate.doctor_id, clinic_id, candidate.scheduled_time)
                candidate_capacity = max(1, int(candidate.max_capacity or 10))
                candidate_rate = round((candidate_booked / candidate_capacity) * 100, 1)
                if candidate_rate < best_target_rate:
                    best_target_rate = candidate_rate
                    best_target = (candidate, candidate_doctor, candidate_booked, candidate_capacity)
            if best_target and best_target_rate <= 70:
                candidate, candidate_doctor, candidate_booked, candidate_capacity = best_target
                recommendations.append(
                    {
                        "type": "redistribute",
                        "priority": "high",
                        "doctor_id": row.doctor_id,
                        "doctor_name": doctor_name,
                        "department": department,
                        "date": date_key,
                        "period": period,
                        "target_doctor_id": candidate.doctor_id,
                        "target_doctor_name": candidate_doctor.full_name,
                        "target_rate": best_target_rate,
                        "message": f"{doctor_name} 当前负载 {util}% ，建议向 {candidate_doctor.full_name} 分流（当前 {best_target_rate}%）。",
                        "target_capacity": candidate_capacity,
                        "target_booked": candidate_booked,
                    }
                )

    priority_rank = {"high": 3, "medium": 2, "low": 1}
    recommendations.sort(key=lambda item: priority_rank.get(str(item.get("priority")), 1), reverse=True)
    return success_response(
        data={
            "clinic_id": clinic_id,
            "week_start": start.isoformat(),
            "recommendations": recommendations[:40],
            "count": len(recommendations),
        }
    )
