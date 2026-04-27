"""Adoption matching APIs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.core import AdoptionPet, Adopter, MatchResult, Pet
from backend.schemas.response import success_response
from backend.services.paci_service import (
    FAST_DEFAULT_TOP_N,
    build_matching_dashboard,
    enqueue_full_matching,
    get_algorithm_profile,
    get_match_status,
    run_paci_matching,
)

router = APIRouter(prefix="/adoption", tags=["adoption"])


def _serialize_match(row: MatchResult, adopter_name: str) -> dict[str, object]:
    return {
        "id": row.id,
        "adoption_pet_id": row.adoption_pet_id,
        "adopter_id": row.adopter_id,
        "adopter_name": adopter_name,
        "s_dist": float(row.s_dist or 0.0),
        "s_env": float(row.s_env or 0.0),
        "s_med": float(row.s_med or 0.0),
        "s_pref": float(row.s_pref or 0.0),
        "s_behavior": float(row.s_behavior or 0.0),
        "s_health_cost": float(row.s_health_cost or 0.0),
        "s_collab": float(row.s_collab or 0.0),
        "total_score": float(row.total_score or 0.0),
        "hard_blocked": bool(row.hard_blocked),
        "predicted_speed_days": int(row.predicted_speed_days or 240),
        "speed_level": str(row.speed_level or "very_slow"),
        "recommendation_confidence": float(row.recommendation_confidence or 0.0),
        "model_version": str(row.model_version or ""),
        "adopted": bool(row.adopted),
        "feedback_score": float(row.feedback_score or 0.0),
        "rationale": row.rationale,
        "details": row.details or {},
    }


@router.get("/algorithm")
def get_algorithm_card() -> dict[str, object]:
    return success_response(data=get_algorithm_profile())


@router.get("/pets")
def list_adoption_pets(db: Session = Depends(get_db)) -> dict[str, object]:
    rows = (
        db.query(AdoptionPet)
        .filter(AdoptionPet.status.in_(["待领养", "可领养"]))
        .order_by(AdoptionPet.adoption_priority.desc(), AdoptionPet.created_at.desc())
        .all()
    )
    data: list[dict[str, object]] = []
    for row in rows:
        pet = db.query(Pet).filter(Pet.id == row.pet_id).first()
        data.append(
            {
                "id": row.id,
                "pet_id": row.pet_id,
                "pet_name": pet.name if pet else f"Pet#{row.pet_id}",
                "species": row.species,
                "breed": row.breed,
                "status": row.status,
                "energy_level": float(row.energy_level or 0.0),
                "sociability": float(row.sociability or 0.0),
                "care_need": float(row.care_need or 0.0),
                "medical_need": float(row.medical_need or 0.0),
                "aggression_level": float(row.aggression_level or 0.0),
                "required_companion_hours": float(row.required_companion_hours or 0.0),
                "age_months": int(row.age_months or 0),
                "vaccinated": bool(row.vaccinated),
                "neutered": bool(row.neutered),
                "adoption_priority": float(row.adoption_priority or 0.0),
            }
        )
    return success_response(data=data)


@router.post("/match/{adoption_pet_id}")
def calculate_match(
    adoption_pet_id: int,
    mode: str = Query(default="fast", pattern="^(fast|full)$"),
    top_n: int = Query(default=FAST_DEFAULT_TOP_N, ge=20, le=2000),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    mode = str(mode).lower()
    adopter_map = {int(a.id): a.name for a in db.query(Adopter.id, Adopter.name).all()}

    if mode == "full":
        status = enqueue_full_matching(adoption_pet_id)
        return success_response(data={"rows": [], "mode": "full", "status": status})

    rows = run_paci_matching(db, adoption_pet_id, mode="fast", top_n=top_n)
    data = [_serialize_match(row, adopter_map.get(int(row.adopter_id), f"Adopter#{row.adopter_id}")) for row in rows]
    status = enqueue_full_matching(adoption_pet_id)
    return success_response(
        data={
            "rows": data,
            "mode": "fast",
            "status": status,
        }
    )


@router.get("/match-status/{adoption_pet_id}")
def match_status(adoption_pet_id: int) -> dict[str, object]:
    return success_response(data=get_match_status(adoption_pet_id))


@router.get("/match/{adoption_pet_id}")
def list_match_results(adoption_pet_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    rows = (
        db.query(MatchResult)
        .filter(MatchResult.adoption_pet_id == adoption_pet_id)
        .order_by(MatchResult.total_score.desc(), MatchResult.predicted_speed_days.asc())
        .all()
    )
    adopter_map = {int(a.id): a.name for a in db.query(Adopter.id, Adopter.name).all()}
    data = [_serialize_match(row, adopter_map.get(int(row.adopter_id), f"Adopter#{row.adopter_id}")) for row in rows]
    return success_response(data=data)


@router.get("/dashboard/{adoption_pet_id}")
def match_dashboard(
    adoption_pet_id: int,
    top_n: int = Query(default=20, ge=5, le=100),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    data = build_matching_dashboard(db=db, adoption_pet_id=adoption_pet_id, top_n=top_n)
    return success_response(data=data)


@router.get("/persona/{adoption_pet_id}")
def adopter_persona(adoption_pet_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    rows = (
        db.query(MatchResult, Adopter)
        .join(Adopter, Adopter.id == MatchResult.adopter_id)
        .filter(MatchResult.adoption_pet_id == adoption_pet_id, MatchResult.hard_blocked.is_(False))
        .order_by(MatchResult.total_score.desc())
        .limit(80)
        .all()
    )
    if not rows:
        return success_response(
            data={
                "histograms": {"experience": [], "housing_type": []},
                "averages": {"budget": 0, "housing_area": 0, "available_hours": 0, "activity_level": 0},
                "geo_points": [],
                "top_personas": [],
            }
        )
    exp_count: dict[str, int] = {}
    house_count: dict[str, int] = {}
    budget_sum = 0.0
    area_sum = 0.0
    hours_sum = 0.0
    activity_sum = 0.0
    geo_points: list[dict[str, object]] = []
    top_personas: list[dict[str, object]] = []
    for idx, (match, adopter) in enumerate(rows):
        exp = str(adopter.experience_level or "unknown")
        house = str(adopter.housing_type or "unknown")
        exp_count[exp] = exp_count.get(exp, 0) + 1
        house_count[house] = house_count.get(house, 0) + 1
        budget_sum += float(adopter.budget or 0)
        area_sum += float(adopter.housing_area or 0)
        hours_sum += float(adopter.available_hours or 0)
        activity_sum += float(adopter.activity_level or 0)
        geo_points.append(
            {
                "name": adopter.name,
                "lng": float(adopter.longitude or 0),
                "lat": float(adopter.latitude or 0),
                "score": float(match.total_score or 0),
            }
        )
        if idx < 6:
            top_personas.append(
                {
                    "adopter_name": adopter.name,
                    "experience_level": exp,
                    "housing_type": house,
                    "budget": float(adopter.budget or 0),
                    "housing_area": float(adopter.housing_area or 0),
                    "available_hours": float(adopter.available_hours or 0),
                    "total_score": float(match.total_score or 0),
                }
            )
    n = max(1, len(rows))
    return success_response(
        data={
            "histograms": {
                "experience": [{"name": k, "value": v} for k, v in exp_count.items()],
                "housing_type": [{"name": k, "value": v} for k, v in house_count.items()],
            },
            "averages": {
                "budget": round(budget_sum / n, 1),
                "housing_area": round(area_sum / n, 1),
                "available_hours": round(hours_sum / n, 1),
                "activity_level": round(activity_sum / n, 2),
            },
            "geo_points": geo_points,
            "top_personas": top_personas,
        }
    )
