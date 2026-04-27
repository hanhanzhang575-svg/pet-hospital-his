"""医生与护士排班路由（OR-Tools CP-SAT）。"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.core import Role, SchedulingAssignment, User
from backend.schemas.response import success_response

router = APIRouter(prefix="/scheduling", tags=["scheduling"])

MIN_DEMO_STAFF_PER_ROLE = 6
DEMO_STAFF_NAMES = {
    "doctor": ["林医生(内科)", "赵医生(外科)", "许医生(皮肤科)", "何医生(眼科)", "顾医生(牙科)", "唐医生(影像科)"],
    "nurse": ["周护士", "吴护士", "郑护士", "沈护士", "韩护士", "魏护士"],
}


class ShiftInput(BaseModel):
    """班次输入模型。"""

    shift_id: str = Field(..., description="班次标识，如 早班/中班/晚班")
    start_time: str = Field(..., description="开始时间 HH:MM")
    end_time: str = Field(..., description="结束时间 HH:MM")


class GenerateScheduleRequest(BaseModel):
    """自动排班请求模型。"""

    start_date: date = Field(..., description="排班起始日期")
    days: int = Field(default=7, ge=1, le=31, description="排班天数")
    clinic_id: str | None = Field(default=None, description="院区编码")
    shifts: list[ShiftInput] = Field(
        default_factory=lambda: [
            ShiftInput(shift_id="早班", start_time="08:00", end_time="12:00"),
            ShiftInput(shift_id="中班", start_time="12:00", end_time="18:00"),
            ShiftInput(shift_id="晚班", start_time="18:00", end_time="23:00"),
        ],
        description="班次定义",
    )
    overwrite_existing: bool = Field(default=True, description="是否覆盖同日期范围内历史排班")


class UpsertScheduleRequest(BaseModel):
    """拖拽调整后的单条排班更新请求模型。"""

    assignment_id: int | None = Field(default=None, description="已有排班ID，新增可为空")
    employee_id: int = Field(..., description="员工ID")
    role_name: str = Field(..., description="角色名：doctor/nurse")
    work_date: date = Field(..., description="排班日期")
    shift_id: str = Field(..., description="班次ID")
    start_at: datetime = Field(..., description="开始时间")
    end_at: datetime = Field(..., description="结束时间")
    source: str = Field(default="manual", description="来源：manual/algorithm")


def _get_or_create_role(db: Session, role_name: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        role = Role(name=role_name, description="排班演示角色")
        db.add(role)
        db.flush()
    return role


def _pick_users_by_role(db: Session, role_name: str, clinic_id: str | None) -> list[dict[str, Any]]:
    """按角色读取可用员工。"""
    role = db.query(Role).filter(Role.name == role_name).first()
    if role is None:
        return []
    query = db.query(User).filter(User.role_id == role.id, User.is_active.is_(True))
    if clinic_id:
        query = query.filter(User.branch_code == clinic_id)
    rows = query.order_by(User.id.asc()).all()
    return [{"employee_id": row.id, "role_name": role_name} for row in rows]


def _ensure_demo_staff(db: Session, role_name: str, clinic_id: str | None, target_count: int = MIN_DEMO_STAFF_PER_ROLE) -> None:
    """补足演示排班人员，避免样例数据太少导致算法无结果。"""
    if not clinic_id:
        return

    role = _get_or_create_role(db, role_name)
    current_count = (
        db.query(User)
        .filter(User.role_id == role.id, User.branch_code == clinic_id, User.is_active.is_(True))
        .count()
    )
    if current_count >= target_count:
        return

    fallback_hash = db.query(User.password_hash).filter(User.password_hash.is_not(None)).limit(1).scalar() or "demo_password_hash"
    prefix = "D" if role_name == "doctor" else "H"
    names = DEMO_STAFF_NAMES.get(role_name, [])

    for index in range(current_count + 1, target_count + 1):
        username = f"scheduler_{clinic_id.lower()}_{role_name}_{index:02d}"
        if db.query(User).filter(User.username == username).first():
            continue

        employee_code = f"{prefix}{clinic_id[-3:]}9{index:03d}"
        while db.query(User).filter(User.employee_code == employee_code).first():
            employee_code = f"{prefix}{clinic_id[-3:]}{index:03d}{datetime.utcnow():%S%f}"[:20]

        db.add(
            User(
                employee_code=employee_code,
                username=username,
                password_hash=fallback_hash,
                full_name=names[(index - 1) % len(names)] if names else f"{role_name}{index:02d}",
                role_id=role.id,
                branch_code=clinic_id,
                is_active=True,
                is_licensed_vet=(role_name == "doctor"),
            )
        )
    db.commit()


def _staff_summary(db: Session, clinic_id: str | None) -> dict[str, Any]:
    """返回医生/护士员工池摘要。"""
    summary: dict[str, Any] = {}
    for role_name in ("doctor", "nurse"):
        role = db.query(Role).filter(Role.name == role_name).first()
        if role is None:
            rows: list[User] = []
        else:
            query = db.query(User).filter(User.role_id == role.id, User.is_active.is_(True))
            if clinic_id:
                query = query.filter(User.branch_code == clinic_id)
            rows = query.order_by(User.id.asc()).all()
        summary[role_name] = {
            "count": len(rows),
            "items": [
                {
                    "employee_id": row.id,
                    "employee_name": row.full_name,
                    "clinic_id": row.branch_code,
                }
                for row in rows
            ],
        }
    return summary


def _combine_datetime(work_date: date, hhmm: str) -> datetime:
    hour, minute = hhmm.split(":")
    return datetime.combine(work_date, datetime.min.time()).replace(hour=int(hour), minute=int(minute))


def _fallback_solve_role_schedule(
    *,
    role_name: str,
    employees: list[dict[str, Any]],
    start_date: date,
    days: int,
    shifts: list[ShiftInput],
) -> list[SimpleNamespace]:
    """无 OR-Tools 环境下的均衡轮转排班，保证演示页面有可解释结果。"""
    if not employees:
        raise ValueError(f"角色 {role_name} 没有可用员工，无法排班")
    if len(employees) < len(shifts):
        raise ValueError(f"角色 {role_name} 至少需要 {len(shifts)} 名员工覆盖每日班次")

    rows: list[SimpleNamespace] = []
    role_offset = 1 if role_name == "nurse" else 0
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        day_start = (day * 2 + role_offset) % len(employees)
        for shift_index, shift in enumerate(shifts):
            employee = employees[(day_start + shift_index) % len(employees)]
            start_at = _combine_datetime(current_date, shift.start_time)
            end_at = _combine_datetime(current_date, shift.end_time)
            if end_at <= start_at:
                end_at += timedelta(days=1)
            rows.append(
                SimpleNamespace(
                    employee_id=int(employee["employee_id"]),
                    date=current_date.isoformat(),
                    shift_id=shift.shift_id,
                    role_name=role_name,
                    start_at=start_at.isoformat(),
                    end_at=end_at.isoformat(),
                )
            )
    return rows


def _fallback_solve_schedule_for_roles(
    *,
    doctors: list[dict[str, Any]],
    nurses: list[dict[str, Any]],
    start_date: date,
    days: int,
    shifts: list[ShiftInput],
) -> list[SimpleNamespace]:
    return _fallback_solve_role_schedule(
        role_name="doctor",
        employees=doctors,
        start_date=start_date,
        days=days,
        shifts=shifts,
    ) + _fallback_solve_role_schedule(
        role_name="nurse",
        employees=nurses,
        start_date=start_date,
        days=days,
        shifts=shifts,
    )


@router.get("/staff")
def list_scheduling_staff(clinic_id: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询当前院区可参与排班的医生与护士。"""
    return success_response(data=_staff_summary(db, clinic_id))


@router.post("/generate")
def generate_schedule(payload: GenerateScheduleRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """自动生成医生+护士排班，并落库。"""
    use_fallback_solver = False
    try:
        from backend.services.scheduling_algorithm import SchedulingEmployee, SchedulingShift, solve_schedule_for_roles
    except Exception:
        use_fallback_solver = True

    _ensure_demo_staff(db, "doctor", payload.clinic_id)
    _ensure_demo_staff(db, "nurse", payload.clinic_id)

    doctors = _pick_users_by_role(db, "doctor", payload.clinic_id)
    nurses = _pick_users_by_role(db, "nurse", payload.clinic_id)
    if not doctors:
        return success_response(code=422, message="当前条件下无可用医生，无法排班", data={"staff": _staff_summary(db, payload.clinic_id)})
    if not nurses:
        return success_response(code=422, message="当前条件下无可用护士，无法排班", data={"staff": _staff_summary(db, payload.clinic_id)})

    try:
        if use_fallback_solver:
            solved_rows = _fallback_solve_schedule_for_roles(
                doctors=doctors,
                nurses=nurses,
                start_date=payload.start_date,
                days=payload.days,
                shifts=payload.shifts,
            )
        else:
            shifts = [SchedulingShift(shift_id=s.shift_id, start_time=s.start_time, end_time=s.end_time) for s in payload.shifts]
            doctor_inputs = [SchedulingEmployee(employee_id=int(x["employee_id"]), role_name=str(x["role_name"])) for x in doctors]
            nurse_inputs = [SchedulingEmployee(employee_id=int(x["employee_id"]), role_name=str(x["role_name"])) for x in nurses]
            solved_rows = solve_schedule_for_roles(
                doctors=doctor_inputs,
                nurses=nurse_inputs,
                start_date=payload.start_date,
                days=payload.days,
                shifts=shifts,
            )
    except ValueError as exc:
        return success_response(code=422, message=str(exc), data={"staff": _staff_summary(db, payload.clinic_id)})

    end_date = payload.start_date + timedelta(days=payload.days - 1)
    if payload.overwrite_existing:
        query = db.query(SchedulingAssignment).filter(
            SchedulingAssignment.work_date >= payload.start_date,
            SchedulingAssignment.work_date <= end_date,
        )
        if payload.clinic_id:
            employee_ids_subq = select(User.id).where(User.branch_code == payload.clinic_id)
            query = query.filter(SchedulingAssignment.employee_id.in_(employee_ids_subq))
        query.delete(synchronize_session=False)

    records: list[SchedulingAssignment] = []
    for row in solved_rows:
        records.append(
            SchedulingAssignment(
                employee_id=row.employee_id,
                role_name=row.role_name,
                work_date=date.fromisoformat(row.date),
                shift_id=row.shift_id,
                start_at=datetime.fromisoformat(row.start_at),
                end_at=datetime.fromisoformat(row.end_at),
                source="algorithm",
            )
        )
    db.add_all(records)
    db.commit()
    for item in records:
        db.refresh(item)

    data = [
        {
            "assignment_id": item.id,
            "employee_id": item.employee_id,
            "date": item.work_date.isoformat(),
            "shift_id": item.shift_id,
            "role_name": item.role_name,
            "start_at": item.start_at.isoformat(),
            "end_at": item.end_at.isoformat(),
            "source": item.source,
        }
        for item in records
    ]
    staff = _staff_summary(db, payload.clinic_id)
    return success_response(
        data={
            "rows": data,
            "count": len(data),
            "staff": staff,
            "date_range": {"start_date": payload.start_date.isoformat(), "end_date": end_date.isoformat()},
        },
        message=(
            f"排班生成成功：医生 {staff['doctor']['count']} 人，护士 {staff['nurse']['count']} 人，共 {len(data)} 条"
            + ("（当前使用内置轮转算法，安装 ortools 后自动切换 CP-SAT）" if use_fallback_solver else "")
        ),
    )


@router.get("/assignments")
def list_assignments(
    start_date: date | None = None,
    end_date: date | None = None,
    role_name: str | None = None,
    clinic_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """查询排班结果。"""
    query = db.query(SchedulingAssignment, User).join(User, User.id == SchedulingAssignment.employee_id)
    if start_date:
        query = query.filter(SchedulingAssignment.work_date >= start_date)
    if end_date:
        query = query.filter(SchedulingAssignment.work_date <= end_date)
    if role_name:
        query = query.filter(SchedulingAssignment.role_name == role_name)
    if clinic_id:
        query = query.filter(User.branch_code == clinic_id)
    rows = query.order_by(SchedulingAssignment.work_date.asc(), SchedulingAssignment.start_at.asc(), User.id.asc()).all()
    data = [
        {
            "assignment_id": item.id,
            "employee_id": user.id,
            "employee_name": user.full_name,
            "department": user.branch_code,
            "role_name": item.role_name,
            "date": item.work_date.isoformat(),
            "shift_id": item.shift_id,
            "start_at": item.start_at.isoformat(),
            "end_at": item.end_at.isoformat(),
            "source": item.source,
        }
        for item, user in rows
    ]
    return success_response(data=data, meta={"staff": _staff_summary(db, clinic_id)})


@router.put("/assignment")
def upsert_assignment(payload: UpsertScheduleRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """手动拖拽后同步单条排班。"""
    user = db.query(User).filter(User.id == payload.employee_id, User.is_active.is_(True)).first()
    if user is None:
        return success_response(code=404, message="员工不存在")

    row: SchedulingAssignment | None = None
    if payload.assignment_id is not None:
        row = db.query(SchedulingAssignment).filter(SchedulingAssignment.id == payload.assignment_id).first()
        if row is None:
            return success_response(code=404, message="排班记录不存在")
        row.employee_id = payload.employee_id
        row.role_name = payload.role_name
        row.work_date = payload.work_date
        row.shift_id = payload.shift_id
        row.start_at = payload.start_at
        row.end_at = payload.end_at
        row.source = payload.source
    else:
        row = SchedulingAssignment(
            employee_id=payload.employee_id,
            role_name=payload.role_name,
            work_date=payload.work_date,
            shift_id=payload.shift_id,
            start_at=payload.start_at,
            end_at=payload.end_at,
            source=payload.source,
        )
        db.add(row)

    db.commit()
    db.refresh(row)
    return success_response(
        data={
            "assignment_id": row.id,
            "employee_id": row.employee_id,
            "date": row.work_date.isoformat(),
            "shift_id": row.shift_id,
            "role_name": row.role_name,
            "start_at": row.start_at.isoformat(),
            "end_at": row.end_at.isoformat(),
            "source": row.source,
        },
        message="排班已同步",
    )
