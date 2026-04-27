"""RFM闭环路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.core import Role, User
from backend.schemas.response import success_response
from backend.schemas.tasks import FollowupTaskCreate
from backend.services.realtime_hub import dispatch_async, hub
from backend.services.rfm_analyzer import analyze_owner_rfm
from backend.services.tasks_service import create_followup_tasks

router = APIRouter(prefix="/rfm", tags=["rfm"])


@router.post("/create-followup-tasks")
def create_rfm_followups(payload: dict | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """为高危客户生成回访工单并推送前台。"""
    payload = payload or {}
    selected_owner_ids = set(payload.get("owner_ids") or [])
    warnings = analyze_owner_rfm(db)
    selected = [w for w in warnings if w.risk_level == "high"]
    if selected_owner_ids:
        selected = [w for w in selected if w.owner_id in selected_owner_ids]
    receptionist_role = db.query(Role).filter(Role.name == "receptionist").first()
    receptionist = None
    if receptionist_role is not None:
        receptionist = (
            db.query(User)
            .filter(User.role_id == receptionist_role.id, User.is_active.is_(True))
            .order_by(User.id.asc())
            .first()
        )
    tasks_payload = [
        FollowupTaskCreate(
            owner_id=item.owner_id,
            owner_name=item.owner_name,
            risk_score=item.rfm_score,
            risk_level=item.risk_level,
            recency_days=item.recency_days,
            frequency=item.frequency,
            monetary=item.monetary,
            assignee_id=receptionist.id if receptionist else None,
            script_text="您好，这里是白之助宠物医院。近期建议您尽快带宠物复诊，我们已为您保留绿色通道。",
        )
        for item in selected
    ]
    created = create_followup_tasks(db, tasks_payload) if tasks_payload else []
    if created:
        dispatch_async(
            hub.send_to_roles(
                ["receptionist"],
                title="RFM回访任务新增",
                content=f"RFM系统新增{len(created)}条回访任务，请及时处理",
                level="warning",
            )
        )
    return success_response(data={"count": len(created), "assignee": "前台小王"})

