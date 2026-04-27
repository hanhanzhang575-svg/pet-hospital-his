"""笼舍状态机与分配路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.cage import CageAllocationRequest, CageStatusUpdateRequest, CageUnitRead
from backend.schemas.response import success_response
from backend.services.cage_allocator import allocate_cage, list_cages, update_cage_status

router = APIRouter(prefix="/cages", tags=["cages"])


@router.get("")
def cages(clinic_id: str, zone_type: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询院区笼舍列表。"""
    data = [CageUnitRead.model_validate(item).model_dump() for item in list_cages(db, clinic_id, zone_type)]
    return success_response(data=data)


@router.post("/allocate")
def cage_allocate(payload: CageAllocationRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """执行笼舍三层分配校验。"""
    cage = allocate_cage(
        db,
        pet_id=payload.pet_id,
        clinic_id=payload.clinic_id,
        preferred_zone_type=payload.preferred_zone_type,
        is_emergency=payload.is_emergency,
    )
    data = CageUnitRead.model_validate(cage).model_dump()
    return success_response(data=data)


@router.post("/{cage_id}/status")
def cage_status_update(cage_id: int, payload: CageStatusUpdateRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """按状态机规则更新笼舍状态。"""
    cage = update_cage_status(db, cage_id, payload.target_status)
    data = CageUnitRead.model_validate(cage).model_dump()
    return success_response(data=data)

