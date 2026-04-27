"""宠物档案业务服务。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from backend.exceptions import ApiError
from backend.models.core import Owner, Pet
from backend.schemas.pet import PetCreate, PetUpdate

SPECIES_CODE_MAP = {
    "犬": "C",
    "狗": "C",
    "cat": "M",
    "猫": "M",
    "兔": "R",
    "鸟": "B",
    "爬行类": "P",
    "啮齿类": "G",
    "刺猬": "H",
    "水禽": "W",
    "反刍类": "U",
    "两栖类": "A",
    "龟鳖类": "T",
    "蛇类": "S",
    "节肢类": "J",
    "其他": "X",
}


def _resolve_species_code(species: str) -> str:
    """根据物种名称解析编码规则中的物种码。"""
    normalized = species.strip().lower()
    if species in SPECIES_CODE_MAP:
        return SPECIES_CODE_MAP[species]
    if normalized in SPECIES_CODE_MAP:
        return SPECIES_CODE_MAP[normalized]
    raise ApiError(code=400, message="不支持的物种类型")


def generate_pet_code(db: Session, species: str, clinic_id: str, now: datetime | None = None) -> str:
    """生成宠物ID编码：物种码+院区码+建档年月+4位流水。"""
    current = now or datetime.now()
    species_code = _resolve_species_code(species)
    clinic_code = clinic_id.zfill(2)[:2]
    date_code = current.strftime("%y%m")
    prefix = f"{species_code}{clinic_code}{date_code}"

    latest = db.query(Pet).filter(Pet.pet_code.like(f"{prefix}%")).order_by(Pet.pet_code.desc()).first()
    if latest is None:
        seq = 1
    else:
        seq = int(latest.pet_code[-4:]) + 1

    return f"{prefix}{seq:04d}"


def list_pets(db: Session) -> list[Pet]:
    """查询宠物档案列表。"""
    return db.query(Pet).order_by(Pet.id.desc()).all()


def get_pet(db: Session, pet_id: int) -> Pet:
    """根据ID查询宠物档案。"""
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if pet is None:
        raise ApiError(code=404, message="宠物档案不存在")
    return pet


def create_pet(db: Session, payload: PetCreate) -> Pet:
    """创建宠物档案并自动生成宠物编码。"""
    owner = db.query(Owner).filter(Owner.id == payload.owner_id).first()
    if owner is None:
        raise ApiError(code=404, message="关联主人不存在")

    pet_data = payload.model_dump()
    pet_data["pet_code"] = generate_pet_code(db=db, species=payload.species, clinic_id=payload.clinic_id)
    pet = Pet(**pet_data)
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def update_pet(db: Session, pet_id: int, payload: PetUpdate) -> Pet:
    """更新宠物档案。"""
    pet = get_pet(db, pet_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "owner_id" in update_data:
        owner = db.query(Owner).filter(Owner.id == update_data["owner_id"]).first()
        if owner is None:
            raise ApiError(code=404, message="关联主人不存在")

    for key, value in update_data.items():
        setattr(pet, key, value)
    db.commit()
    db.refresh(pet)
    return pet


def delete_pet(db: Session, pet_id: int) -> None:
    """删除宠物档案。"""
    pet = get_pet(db, pet_id)
    db.delete(pet)
    db.commit()

