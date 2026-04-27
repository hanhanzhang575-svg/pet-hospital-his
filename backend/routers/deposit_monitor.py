"""押金水位预警路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.response import success_response
from backend.services.deposit_monitor import evaluate_deposit_warnings

router = APIRouter(prefix="/deposit-monitor", tags=["deposit-monitor"])


@router.get("/warnings")
def deposit_warnings(db: Session = Depends(get_db)) -> dict[str, object]:
    """查询押金水位预警结果。"""
    data = [item.model_dump() for item in evaluate_deposit_warnings(db)]
    return success_response(data=data)

