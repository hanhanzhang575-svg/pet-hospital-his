"""管理员数据中心（数据库探测器）路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.auth import RequireRole
from backend.database import get_db
from backend.models.core import Pet, User
from backend.schemas.response import success_response

router = APIRouter(prefix="/data-center", tags=["data-center"])


WHITELIST_TABLES = {
    "owners",
    "pets",
    "visits",
    "drugs",
    "cage_units",
    "inpatient_records",
    "medical_records",
    "prescriptions",
    "news_posts",
    "adoption_pets",
    "adopters",
    "match_results",
}


@router.get("/tables")
def list_tables(
    _current_user: User = Depends(RequireRole(["admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    rows = db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name ASC")
    ).fetchall()
    names = [str(r[0]) for r in rows if str(r[0]) in WHITELIST_TABLES]
    return success_response(data=names)


@router.get("/table/{table_name}")
def table_rows(
    table_name: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    _current_user: User = Depends(RequireRole(["admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if table_name not in WHITELIST_TABLES:
        return success_response(code=400, message="不支持的表")
    columns = db.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    pk_cols = {str(c[1]) for c in columns if int(c[5] or 0) == 1}
    fk_rows = db.execute(text(f"PRAGMA foreign_key_list({table_name})")).fetchall()
    fk_cols = {str(r[3]) for r in fk_rows}

    total = int(db.execute(text(f"SELECT COUNT(1) FROM {table_name}")).scalar() or 0)
    offset = (page - 1) * size
    data_rows = db.execute(text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"), {"limit": size, "offset": offset}).fetchall()
    col_names = [str(c[1]) for c in columns]
    data: list[dict[str, object]] = []
    for row in data_rows:
        payload = {}
        for idx, col in enumerate(col_names):
            payload[col] = row[idx]
        data.append(payload)
    return success_response(
        data={
            "columns": col_names,
            "pk_columns": list(pk_cols),
            "fk_columns": list(fk_cols),
            "rows": data,
            "total": total,
        }
    )


@router.get("/trace/medical-record/{record_id}")
def trace_medical_record_fk(
    record_id: int,
    _current_user: User = Depends(RequireRole(["admin"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    row = db.execute(
        text("SELECT id, pet_id, appointment_id, vet_id FROM medical_records WHERE id=:id"),
        {"id": record_id},
    ).fetchone()
    if row is None:
        return success_response(code=404, message="病历不存在")
    pet = db.query(Pet).filter(Pet.id == int(row[1])).first()
    if pet is None:
        return success_response(code=404, message="关联宠物不存在")
    return success_response(
        data={
            "record_id": int(row[0]),
            "pet_id": pet.id,
            "pet_name": pet.name,
            "pet_species": pet.species,
            "owner_id": pet.owner_id,
            "highlight_field": "id",
        }
    )

