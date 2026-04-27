"""宠物主人档案业务服务。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.exceptions import ApiError
from backend.models.core import Owner
from backend.schemas.owner import OwnerCreate, OwnerUpdate


def list_owners(db: Session) -> list[Owner]:
    """查询宠物主人列表。"""
    return db.query(Owner).order_by(Owner.id.desc()).all()


def get_owner(db: Session, owner_id: int) -> Owner:
    """根据ID查询宠物主人。"""
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if owner is None:
        raise ApiError(code=404, message="宠物主人不存在")
    return owner


def create_owner(db: Session, payload: OwnerCreate) -> Owner:
    """创建宠物主人档案。"""
    exists = db.query(Owner).filter(Owner.owner_code == payload.owner_code).first()
    if exists is not None:
        raise ApiError(code=409, message="主人编码已存在")

    owner = Owner(**payload.model_dump())
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner


def update_owner(db: Session, owner_id: int, payload: OwnerUpdate) -> Owner:
    """更新宠物主人档案。"""
    owner = get_owner(db, owner_id)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(owner, key, value)
    db.commit()
    db.refresh(owner)
    return owner


def delete_owner(db: Session, owner_id: int) -> None:
    """删除宠物主人档案。"""
    owner = get_owner(db, owner_id)
    db.delete(owner)
    db.commit()

