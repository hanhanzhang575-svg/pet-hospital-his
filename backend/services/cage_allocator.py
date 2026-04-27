"""笼舍三层约束分配算法模块。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.exceptions import ApiError
from backend.models.core import CageUnit, Pet

CAGE_STATUS_IDLE = "空闲"
CAGE_STATUS_PENDING_ADMISSION = "待入院"
CAGE_STATUS_IN_USE = "住院中"
CAGE_STATUS_PENDING_CLEAN = "待清洁"
CAGE_STATUS_REPAIR = "维修"
CAGE_STATUS_TEMP = "临时启用"

STATE_TRANSITIONS = {
    CAGE_STATUS_IDLE: {CAGE_STATUS_PENDING_ADMISSION, CAGE_STATUS_REPAIR, CAGE_STATUS_TEMP},
    CAGE_STATUS_PENDING_ADMISSION: {CAGE_STATUS_IN_USE, CAGE_STATUS_IDLE},
    CAGE_STATUS_IN_USE: {CAGE_STATUS_PENDING_CLEAN},
    CAGE_STATUS_PENDING_CLEAN: {CAGE_STATUS_IDLE, CAGE_STATUS_REPAIR},
    CAGE_STATUS_REPAIR: {CAGE_STATUS_IDLE},
    CAGE_STATUS_TEMP: {CAGE_STATUS_PENDING_ADMISSION, CAGE_STATUS_IDLE},
}


def _get_zone_candidates(preferred_zone_type: str, is_emergency: bool) -> list[str]:
    """根据急诊策略获取目标病区候选顺序：目标病区→急诊VIP降级→临时笼。"""
    if is_emergency:
        ordered = [preferred_zone_type]
        if preferred_zone_type != "VIP":
            ordered.append("VIP")
        ordered.append("临时笼")
        return ordered
    return [preferred_zone_type]


def allocate_cage(
    db: Session,
    *,
    pet_id: int,
    clinic_id: str,
    preferred_zone_type: str,
    is_emergency: bool,
) -> CageUnit:
    """执行分配：目标病区空余→急诊降级VIP→临时笼→跨院转诊提示。"""
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if pet is None:
        raise ApiError(code=404, message="宠物档案不存在")
    if pet.clinic_id != clinic_id:
        raise ApiError(code=409, message="禁止跨院区分配笼舍")

    zone_candidates = _get_zone_candidates(preferred_zone_type, is_emergency)
    for zone in zone_candidates:
        available_units = (
            db.query(CageUnit)
            .filter(
                CageUnit.clinic_id == clinic_id,
                CageUnit.zone_type == zone,
                CageUnit.status == CAGE_STATUS_IDLE,
                CageUnit.current_pet_id.is_(None),
            )
            .order_by(CageUnit.id.asc())
            .all()
        )

        if not available_units:
            continue

        for cage in available_units:
            cage.status = CAGE_STATUS_PENDING_ADMISSION
            cage.current_pet_id = pet.id
            db.commit()
            db.refresh(cage)
            return cage

    other_clinics = ["C001", "C002", "C003"]
    cross_hints: list[str] = []
    for cid in other_clinics:
        if cid == clinic_id:
            continue
        count = (
            db.query(CageUnit)
            .filter(
                CageUnit.clinic_id == cid,
                CageUnit.zone_type == preferred_zone_type,
                CageUnit.status == CAGE_STATUS_IDLE,
                CageUnit.current_pet_id.is_(None),
            )
            .count()
        )
        if count > 0:
            cross_hints.append(f"{cid}:{count}")
    if cross_hints:
        raise ApiError(code=409, message=f"本院区满载，建议跨院转诊（{', '.join(cross_hints)}）")
    raise ApiError(code=409, message="目标病区无可用笼舍")


def update_cage_status(db: Session, cage_id: int, target_status: str) -> CageUnit:
    """按照笼舍状态机规则更新笼舍状态。"""
    cage = db.query(CageUnit).filter(CageUnit.id == cage_id).first()
    if cage is None:
        raise ApiError(code=404, message="笼舍不存在")

    allowed = STATE_TRANSITIONS.get(cage.status, set())
    if target_status not in allowed:
        raise ApiError(code=409, message=f"笼舍状态不允许从{cage.status}变更为{target_status}")

    cage.status = target_status
    if target_status in {CAGE_STATUS_IDLE, CAGE_STATUS_REPAIR}:
        cage.current_pet_id = None
    db.commit()
    db.refresh(cage)
    return cage


def list_cages(db: Session, clinic_id: str, zone_type: str | None = None) -> list[CageUnit]:
    """查询院区笼舍列表。"""
    query = db.query(CageUnit).filter(CageUnit.clinic_id == clinic_id)
    if zone_type:
        query = query.filter(CageUnit.zone_type == zone_type)
    return query.order_by(CageUnit.id.asc()).all()

