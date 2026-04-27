"""采购与回访任务服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.core import FollowupTask, PurchaseTask, Role, User
from backend.schemas.tasks import FollowupTaskCreate, PurchaseTaskCreate


def create_purchase_tasks(db: Session, items: list[PurchaseTaskCreate]) -> list[PurchaseTask]:
    """批量创建采购任务。"""
    created: list[PurchaseTask] = []
    for item in items:
        if item.suggested_qty <= 0:
            continue
        task = PurchaseTask(
            drug_id=item.drug_id,
            branch_code=item.branch_code,
            current_stock=item.current_stock,
            safety_stock=item.safety_stock,
            suggested_qty=item.suggested_qty,
            status="待处理",
        )
        db.add(task)
        created.append(task)
    db.commit()
    for task in created:
        db.refresh(task)
    return created


def list_purchase_tasks(db: Session, status: str | None = None) -> list[PurchaseTask]:
    """查询采购任务。"""
    query = db.query(PurchaseTask)
    if status:
        query = query.filter(PurchaseTask.status == status)
    return query.order_by(PurchaseTask.id.desc()).all()


def create_followup_tasks(db: Session, items: list[FollowupTaskCreate]) -> list[FollowupTask]:
    """批量创建回访任务。"""
    receptionist_role = db.query(Role).filter(Role.name == "receptionist").first()
    frontdesk_query = db.query(User).filter(User.is_active.is_(True))
    if receptionist_role is not None:
        frontdesk_query = frontdesk_query.filter(User.role_id == receptionist_role.id)
    frontdesk = frontdesk_query.order_by(User.id.asc()).all()
    assignee_id = frontdesk[0].id if frontdesk else None
    created: list[FollowupTask] = []
    for item in items:
        existing = (
            db.query(FollowupTask)
            .filter(
                FollowupTask.owner_id == item.owner_id,
                FollowupTask.status.in_(["待处理", "进行中"]),
            )
            .order_by(FollowupTask.id.desc())
            .first()
        )
        if existing is not None:
            continue
        task = FollowupTask(
            owner_id=item.owner_id,
            owner_name=item.owner_name,
            risk_score=item.risk_score,
            risk_level=item.risk_level,
            recency_days=item.recency_days,
            frequency=item.frequency,
            monetary=item.monetary,
            assignee_id=item.assignee_id if item.assignee_id is not None else assignee_id,
            script_text=item.script_text,
            status="待处理",
        )
        db.add(task)
        created.append(task)
    db.commit()
    for task in created:
        db.refresh(task)
    return created


def list_followup_tasks(db: Session, status: str | None = None) -> list[FollowupTask]:
    """查询回访任务。"""
    query = db.query(FollowupTask)
    if status:
        query = query.filter(FollowupTask.status == status)
    return query.order_by(FollowupTask.id.desc()).all()


def update_followup_task(db: Session, task_id: int, status: str | None = None) -> FollowupTask | None:
    """更新回访任务状态。"""
    task = db.query(FollowupTask).filter(FollowupTask.id == task_id).first()
    if task is None:
        return None
    if status is not None:
        task.status = status
    db.commit()
    db.refresh(task)
    return task


def update_followup_task_detail(db: Session, task_id: int, detail: dict | None = None) -> FollowupTask | None:
    """更新回访任务详情。"""
    task = db.query(FollowupTask).filter(FollowupTask.id == task_id).first()
    if task is None:
        return None
    task.followup_detail = detail or {}
    db.commit()
    db.refresh(task)
    return task

