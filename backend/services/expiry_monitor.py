"""药品效期预警定时任务模块。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.core import DrugInventory
from backend.schemas.inventory import ExpiryWarningRead


def scan_expiry_warnings(db: Session, warning_days: int = 30, now: datetime | None = None) -> list[ExpiryWarningRead]:
    """扫描药品库存效期并生成预警结果。"""
    current = now or datetime.utcnow()
    warnings: list[ExpiryWarningRead] = []
    inventories = db.query(DrugInventory).filter(DrugInventory.expiry_date.is_not(None)).all()
    for inventory in inventories:
        days_to_expiry = int((inventory.expiry_date - current).total_seconds() // 86400)
        if days_to_expiry > warning_days:
            continue
        if days_to_expiry < 0:
            level = "expired"
            message = "药品已过期，禁止发药并需立即下架"
        elif days_to_expiry <= 7:
            level = "critical"
            message = "药品效期不足7天，请优先处置"
        else:
            level = "warning"
            message = "药品临近效期，请尽快补货或调拨"
        warnings.append(
            ExpiryWarningRead(
                inventory_id=inventory.id,
                drug_id=inventory.drug_id,
                branch_code=inventory.branch_code,
                days_to_expiry=days_to_expiry,
                warning_level=level,
                message=message,
            )
        )
    return warnings


def expiry_monitor_job(db_factory: Callable[[], Session]) -> list[ExpiryWarningRead]:
    """效期预警定时任务入口。"""
    db = db_factory()
    try:
        return scan_expiry_warnings(db)
    finally:
        db.close()

