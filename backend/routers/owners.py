"""宠物主人档案路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.owner import OwnerCreate, OwnerRead, OwnerUpdate
from backend.schemas.response import success_response
from backend.services.owner_service import create_owner, delete_owner, get_owner, list_owners, update_owner

router = APIRouter(prefix="/owners", tags=["owners"])


@router.get("")
def owners(db: Session = Depends(get_db)) -> dict[str, object]:
    """查询宠物主人列表。"""
    data = [OwnerRead.model_validate(item).model_dump() for item in list_owners(db)]
    return success_response(data=data)


@router.get("/{owner_id}")
def owner_detail(owner_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询宠物主人详情。"""
    data = OwnerRead.model_validate(get_owner(db, owner_id)).model_dump()
    return success_response(data=data)


@router.post("", status_code=status.HTTP_201_CREATED)
def owner_create(payload: OwnerCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    """创建宠物主人档案。"""
    data = OwnerRead.model_validate(create_owner(db, payload)).model_dump()
    return success_response(code=201, data=data)


@router.put("/{owner_id}")
def owner_update(owner_id: int, payload: OwnerUpdate, db: Session = Depends(get_db)) -> dict[str, object]:
    """更新宠物主人档案。"""
    data = OwnerRead.model_validate(update_owner(db, owner_id, payload)).model_dump()
    return success_response(data=data)


@router.delete("/{owner_id}")
def owner_delete(owner_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """删除宠物主人档案。"""
    delete_owner(db, owner_id)
    return success_response(data={"deleted": True})

