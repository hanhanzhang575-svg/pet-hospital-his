"""排班运筹算法服务（基于 Google OR-Tools CP-SAT）。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from ortools.sat.python import cp_model


@dataclass(slots=True)
class SchedulingEmployee:
    """排班员工输入实体。"""

    employee_id: int
    role_name: str


@dataclass(slots=True)
class SchedulingShift:
    """班次定义输入实体。"""

    shift_id: str
    start_time: str  # HH:MM
    end_time: str  # HH:MM


@dataclass(slots=True)
class SchedulingResultItem:
    """排班结果输出实体。"""

    employee_id: int
    date: str
    shift_id: str
    role_name: str
    start_at: str
    end_at: str


def _parse_time(value: str) -> time:
    """解析 HH:MM 时间字符串。"""
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def _combine_datetime(work_date: date, hhmm: str) -> datetime:
    """将日期和 HH:MM 拼接为 datetime。"""
    return datetime.combine(work_date, _parse_time(hhmm))


def _calc_shift_bounds(work_date: date, shift: SchedulingShift) -> tuple[datetime, datetime]:
    """计算班次起止时间（自动处理跨天班次）。"""
    start_at = _combine_datetime(work_date, shift.start_time)
    end_at = _combine_datetime(work_date, shift.end_time)
    if end_at <= start_at:
        end_at = end_at + timedelta(days=1)
    return start_at, end_at


def solve_role_schedule(
    *,
    role_name: str,
    employees: list[SchedulingEmployee],
    start_date: date,
    days: int,
    shifts: list[SchedulingShift],
    max_consecutive_work_days: int = 5,
) -> list[SchedulingResultItem]:
    """为单一角色求解排班。

    约束说明：
    1. 每天每个班次必须且只能分配1人。
    2. 每名员工每天最多1个班次。
    3. 禁止“晚班->次日早班”。
    4. 连续工作天数最多5天（默认）。
    5. 软约束：尽量均衡晚班次数。
    """
    if days <= 0:
        return []
    if not employees:
        raise ValueError(f"角色 {role_name} 没有可用员工，无法排班")
    if not shifts:
        raise ValueError("班次列表为空，无法排班")

    # 建模索引
    day_index = list(range(days))
    emp_index = list(range(len(employees)))
    shift_index = list(range(len(shifts)))

    model = cp_model.CpModel()

    # 决策变量：x[e,d,s] = 员工 e 是否在第 d 天上第 s 个班
    x: dict[tuple[int, int, int], cp_model.IntVar] = {}
    for e in emp_index:
        for d in day_index:
            for s in shift_index:
                x[(e, d, s)] = model.NewBoolVar(f"x_e{e}_d{d}_s{s}")

    # 约束1：每天每班次恰好1人
    for d in day_index:
        for s in shift_index:
            model.Add(sum(x[(e, d, s)] for e in emp_index) == 1)

    # 约束2：每人每天最多1班
    for e in emp_index:
        for d in day_index:
            model.Add(sum(x[(e, d, s)] for s in shift_index) <= 1)

    # work_day[e,d]：员工 e 在第 d 天是否上班（用于连续工作约束）
    work_day: dict[tuple[int, int], cp_model.IntVar] = {}
    for e in emp_index:
        for d in day_index:
            var = model.NewBoolVar(f"workday_e{e}_d{d}")
            model.Add(var == sum(x[(e, d, s)] for s in shift_index))
            work_day[(e, d)] = var

    # 约束3：晚班后次日不可早班
    early_shift_ids = {"早", "早班", "morning"}
    late_shift_ids = {"晚", "晚班", "night"}
    early_indices = [idx for idx, item in enumerate(shifts) if item.shift_id in early_shift_ids]
    late_indices = [idx for idx, item in enumerate(shifts) if item.shift_id in late_shift_ids]
    if early_indices and late_indices:
        early_idx = early_indices[0]
        late_idx = late_indices[0]
        for e in emp_index:
            for d in range(days - 1):
                model.Add(x[(e, d, late_idx)] + x[(e, d + 1, early_idx)] <= 1)

    # 约束4：连续工作不超过 max_consecutive_work_days
    window = max_consecutive_work_days + 1
    if days >= window:
        for e in emp_index:
            for start in range(0, days - window + 1):
                model.Add(sum(work_day[(e, d)] for d in range(start, start + window)) <= max_consecutive_work_days)

    # 软约束：均衡晚班次数 -> 最小化 max_late_count - min_late_count
    late_counts: list[cp_model.IntVar] = []
    if late_indices:
        late_idx = late_indices[0]
        for e in emp_index:
            c = model.NewIntVar(0, days, f"late_count_e{e}")
            model.Add(c == sum(x[(e, d, late_idx)] for d in day_index))
            late_counts.append(c)
        max_late = model.NewIntVar(0, days, "max_late")
        min_late = model.NewIntVar(0, days, "min_late")
        model.AddMaxEquality(max_late, late_counts)
        model.AddMinEquality(min_late, late_counts)
        fairness_gap = model.NewIntVar(0, days, "fairness_gap")
        model.Add(fairness_gap == max_late - min_late)
        model.Minimize(fairness_gap)
    else:
        model.Minimize(0)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise ValueError(f"{role_name} 排班求解失败，请检查员工数量或约束条件")

    results: list[SchedulingResultItem] = []
    for d in day_index:
        current_date = start_date + timedelta(days=d)
        for s in shift_index:
            selected_emp = None
            for e in emp_index:
                if solver.Value(x[(e, d, s)]) == 1:
                    selected_emp = employees[e]
                    break
            if selected_emp is None:
                continue
            shift = shifts[s]
            start_at, end_at = _calc_shift_bounds(current_date, shift)
            results.append(
                SchedulingResultItem(
                    employee_id=selected_emp.employee_id,
                    date=current_date.isoformat(),
                    shift_id=shift.shift_id,
                    role_name=role_name,
                    start_at=start_at.isoformat(),
                    end_at=end_at.isoformat(),
                )
            )
    return results


def solve_schedule_for_roles(
    *,
    doctors: list[SchedulingEmployee],
    nurses: list[SchedulingEmployee],
    start_date: date,
    days: int,
    shifts: list[SchedulingShift],
) -> list[SchedulingResultItem]:
    """同时求解医生与护士排班。"""
    doctor_rows = solve_role_schedule(
        role_name="doctor",
        employees=doctors,
        start_date=start_date,
        days=days,
        shifts=shifts,
    )
    nurse_rows = solve_role_schedule(
        role_name="nurse",
        employees=nurses,
        start_date=start_date,
        days=days,
        shifts=shifts,
    )
    return doctor_rows + nurse_rows
