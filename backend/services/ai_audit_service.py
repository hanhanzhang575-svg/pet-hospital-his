"""人机决策偏差审计日志服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.models.core import AiDecisionAuditLog
from backend.schemas.ai import AuditLogCreate


def create_audit_log(db: Session, payload: AuditLogCreate) -> AiDecisionAuditLog:
    """创建人机决策偏差审计日志。"""
    log = AiDecisionAuditLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_audit_logs(db: Session, medical_record_id: int | None = None) -> list[AiDecisionAuditLog]:
    """查询审计日志列表。"""
    query = db.query(AiDecisionAuditLog)
    if medical_record_id:
        query = query.filter(AiDecisionAuditLog.medical_record_id == medical_record_id)
    return query.order_by(AiDecisionAuditLog.id.desc()).all()

