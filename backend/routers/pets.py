"""宠物档案路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.pet import PetCreate, PetRead, PetUpdate
from backend.schemas.response import success_response
from backend.services.pet_service import create_pet, delete_pet, get_pet, list_pets, update_pet

router = APIRouter(prefix="/pets", tags=["pets"])


@router.get("")
def pets(db: Session = Depends(get_db)) -> dict[str, object]:
    """查询宠物档案列表。"""
    data = [PetRead.model_validate(item).model_dump() for item in list_pets(db)]
    return success_response(data=data)


@router.get("/{pet_id}")
def pet_detail(pet_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询宠物档案详情。"""
    data = PetRead.model_validate(get_pet(db, pet_id)).model_dump()
    return success_response(data=data)


@router.post("", status_code=status.HTTP_201_CREATED)
def pet_create(payload: PetCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    """创建宠物档案。"""
    data = PetRead.model_validate(create_pet(db, payload)).model_dump()
    return success_response(code=201, data=data)


@router.put("/{pet_id}")
def pet_update(pet_id: int, payload: PetUpdate, db: Session = Depends(get_db)) -> dict[str, object]:
    """更新宠物档案。"""
    data = PetRead.model_validate(update_pet(db, pet_id, payload)).model_dump()
    return success_response(data=data)


@router.delete("/{pet_id}")
def pet_delete(pet_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    """删除宠物档案。"""
    delete_pet(db, pet_id)
    return success_response(data={"deleted": True})

