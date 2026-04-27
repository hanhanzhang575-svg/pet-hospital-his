"""医院新闻动态路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth import RequireRole
from backend.database import get_db
from backend.models.core import NewsPost, User
from backend.schemas.response import success_response

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
def list_news(limit: int = 12, db: Session = Depends(get_db)) -> dict[str, object]:
    safe_limit = max(1, min(int(limit or 12), 30))
    rows = (
        db.query(NewsPost)
        .filter(NewsPost.is_published.is_(True))
        .order_by(NewsPost.created_at.desc())
        .limit(safe_limit)
        .all()
    )
    data = [
        {
            "id": row.id,
            "title": row.title,
            "summary": row.summary,
            "category": row.category,
            "source_name": row.source_name,
            "source_url": row.source_url,
            "cover_image": row.cover_image,
            "markdown_content": row.markdown_content,
            "published_at": row.published_at.isoformat() if row.published_at else None,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]
    return success_response(data=data)


@router.post("")
def create_news(
    payload: dict[str, object],
    current_user: User = Depends(RequireRole(["admin", "manager"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    row = NewsPost(
        title=str(payload.get("title") or "").strip(),
        summary=str(payload.get("summary") or "").strip() or None,
        category=str(payload.get("category") or "").strip() or None,
        source_name=str(payload.get("source_name") or "").strip() or None,
        source_url=str(payload.get("source_url") or "").strip() or None,
        cover_image=str(payload.get("cover_image") or "").strip() or None,
        markdown_content=str(payload.get("markdown_content") or "").strip(),
        is_published=bool(payload.get("is_published", True)),
        created_by=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return success_response(data={"id": row.id})

