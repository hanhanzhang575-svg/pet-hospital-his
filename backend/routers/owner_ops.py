"""主人运营中心路由。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth import RequireRole
from backend.database import get_db
from backend.models.core import Adopter, Invoice, MatchResult, Owner, Pet, User
from backend.schemas.response import success_response

router = APIRouter(prefix="/owner-center", tags=["owner-center"])


@router.get("/{owner_id}")
def owner_center(
    owner_id: int,
    _current_user: User = Depends(RequireRole(["receptionist", "admin", "manager"])),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if owner is None:
        return success_response(code=404, message="主人不存在")
    pets = db.query(Pet).filter(Pet.owner_id == owner_id).order_by(Pet.id.desc()).all()
    invoices = db.query(Invoice).filter(Invoice.owner_id == owner_id).order_by(Invoice.created_at.desc()).all()
    adopter = db.query(Adopter).filter(Adopter.owner_id == owner_id).first()
    if adopter:
        adoption_progress = (
            db.query(MatchResult)
            .filter(MatchResult.adopter_id == adopter.id)
            .order_by(MatchResult.created_at.desc())
            .limit(40)
            .all()
        )
    else:
        adoption_progress = []

    now = datetime.utcnow()
    monthly_bucket: dict[str, float] = defaultdict(float)
    paid_bucket: dict[str, float] = defaultdict(float)
    for inv in invoices:
        if not inv.created_at:
            continue
        key = inv.created_at.strftime("%Y-%m")
        monthly_bucket[key] += float(inv.total_amount or 0)
        paid_bucket[key] += float(inv.paid_amount or 0)
    month_labels: list[str] = []
    for i in range(5, -1, -1):
        m = (now - timedelta(days=i * 30)).strftime("%Y-%m")
        month_labels.append(m)
    trend_rows = [
        {
            "month": m,
            "amount": round(monthly_bucket.get(m, 0.0), 2),
            "paid": round(paid_bucket.get(m, 0.0), 2),
        }
        for m in month_labels
    ]

    total_amount = sum(float(x.total_amount or 0) for x in invoices)
    total_paid = sum(float(x.paid_amount or 0) for x in invoices)
    unpaid_amount = max(0.0, total_amount - total_paid)
    recency_days = 365
    if invoices and invoices[0].created_at:
        recency_days = max((now - invoices[0].created_at).days, 0)
    frequency = len(invoices)
    monetary = total_amount
    recency_score = min(recency_days, 365) / 365 * 100
    frequency_score = min(frequency, 12) / 12 * 100
    monetary_score = min(monetary, 20000) / 20000 * 100
    rfm_score = round(recency_score * 0.4 + (100 - frequency_score) * 0.3 + (100 - monetary_score) * 0.3, 2)
    if rfm_score >= 60:
        rfm_level = "high_risk"
    elif rfm_score >= 35:
        rfm_level = "medium_risk"
    else:
        rfm_level = "healthy"

    adoption_rows = [
        {
            "match_id": r.id,
            "total_score": float(r.total_score or 0.0),
            "hard_blocked": bool(r.hard_blocked),
            "speed_level": str(r.speed_level or "unknown"),
            "predicted_speed_days": int(r.predicted_speed_days or 0),
            "rationale": r.rationale,
            "created_at": r.created_at.isoformat(),
        }
        for r in adoption_progress
    ]
    top_adoption = sorted(
        [x for x in adoption_rows if not x["hard_blocked"]],
        key=lambda x: x["total_score"],
        reverse=True,
    )[:10]

    data = {
        "owner": {
            "id": owner.id,
            "owner_code": owner.owner_code,
            "name": owner.name,
            "phone": owner.phone,
            "latitude": owner.latitude,
            "longitude": owner.longitude,
        },
        "my_pets": [
            {
                "id": p.id,
                "pet_code": p.pet_code,
                "name": p.name,
                "species": p.species,
                "breed": p.breed,
                "weight": p.weight,
            }
            for p in pets
        ],
        "medical_bills": [
            {
                "id": inv.id,
                "invoice_no": inv.invoice_no,
                "total_amount": inv.total_amount,
                "paid_amount": inv.paid_amount,
                "status": inv.status,
                "created_at": inv.created_at.isoformat(),
            }
            for inv in invoices
        ],
        "adoption_progress": adoption_rows,
        "adoption_top_recommendations": top_adoption,
        "billing_trend": trend_rows,
        "owner_kpis": {
            "total_amount": round(total_amount, 2),
            "total_paid": round(total_paid, 2),
            "unpaid_amount": round(unpaid_amount, 2),
            "invoice_count": len(invoices),
            "pet_count": len(pets),
            "adoption_match_count": len(adoption_rows),
        },
        "rfm_profile": {
            "recency_days": recency_days,
            "frequency": frequency,
            "monetary": round(monetary, 2),
            "rfm_score": rfm_score,
            "risk_level": rfm_level,
        },
    }
    return success_response(data=data)

