"""RFM客户流失预警模块。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.core import Invoice, Owner
from backend.schemas.ai import RfmWarningRead

MAX_RFM_WARNING_ROWS = 80

def calculate_rfm_score(recency: int, frequency: int, monetary: float) -> float:
    """计算RFM综合评分。"""
    return round(recency * 0.3 + frequency * 0.3 + monetary * 0.4, 2)


def analyze_owner_rfm(db: Session) -> list[RfmWarningRead]:
    """计算客户RFM并返回流失预警列表。"""
    now = datetime.utcnow()
    warnings: list[RfmWarningRead] = []
    owners = db.query(Owner).all()
    for owner in owners:
        invoices = db.query(Invoice).filter(Invoice.owner_id == owner.id).order_by(Invoice.created_at.desc()).all()
        if invoices:
            latest_days = max((now - invoices[0].created_at).days, 0)
            frequency = len(invoices)
            monetary = float(sum(item.total_amount for item in invoices))
        else:
            latest_days = 365
            frequency = 0
            monetary = 0.0

        recency_score = min(latest_days, 365) / 365 * 100
        frequency_score = min(frequency, 12) / 12 * 100
        monetary_score = min(monetary, 20000) / 20000 * 100
        rfm_score = round(recency_score * 0.4 + (100 - frequency_score) * 0.3 + (100 - monetary_score) * 0.3, 2)
        if rfm_score >= 60:
            risk_level = "high"
        elif rfm_score >= 35:
            risk_level = "medium"
        else:
            risk_level = "low"
        warnings.append(
            RfmWarningRead(
                owner_id=owner.id,
                owner_name=owner.name,
                recency_days=latest_days,
                frequency=frequency,
                monetary=round(monetary, 2),
                rfm_score=rfm_score,
                risk_level=risk_level,
            )
        )
    return sorted(warnings, key=lambda item: item.rfm_score, reverse=True)[:MAX_RFM_WARNING_ROWS]

