"""Hybrid adoption matching service (fast + background full compute)."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.core import AdoptionPet, Adopter, MatchResult


MODEL_VERSION = "hybrid_v2_2"
FAST_DEFAULT_TOP_N = 200
FULL_JOB_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="adoption-full")


@dataclass
class PetProfile:
    id: int
    species: str
    breed: str | None
    is_dangerous_dog: bool
    energy_level: float
    sociability: float
    trainability: float
    care_need: float
    noise_level: float
    space_need: float
    medical_need: float
    aggression_level: float
    required_companion_hours: float
    age_months: int
    vaccinated: bool
    neutered: bool
    friendliness_human: float
    shelter_stress: float
    adoption_priority: float
    latitude: float | None
    longitude: float | None


@dataclass
class AdopterProfile:
    id: int
    name: str
    experience_level: str
    housing_area: float
    budget: float
    available_hours: float
    latitude: float
    longitude: float
    resident_species: list[str]
    incompatible_species: list[str]
    preferred_species: list[str]
    preferred_age_min: int
    preferred_age_max: int
    has_children: bool
    has_elderly: bool
    has_allergy_family: bool
    work_from_home_days: float
    activity_level: float
    patience_level: float
    housing_type: str
    has_yard: bool
    credit_score: float
    historical_adoption_success: int


@dataclass
class HybridScore:
    s_dist: float
    s_env: float
    s_med: float
    s_pref: float
    s_behavior: float
    s_health_cost: float
    s_collab: float
    total_score: float
    hard_blocked: bool
    predicted_speed_days: int
    speed_level: str
    recommendation_confidence: float
    rationale: str
    details: dict[str, Any]


@dataclass
class MatchJobStatus:
    adoption_pet_id: int
    state: str  # idle/running/completed/failed
    mode: str
    started_at: datetime | None
    finished_at: datetime | None
    processed: int
    total: int
    error: str | None = None


_STATUS_LOCK = threading.Lock()
_MATCH_STATUS: dict[int, MatchJobStatus] = {}
_RUNNING_FULL: set[int] = set()


def _now() -> datetime:
    return datetime.utcnow()


def _avg(values: list[float], default: float = 0.0) -> float:
    if not values:
        return default
    return sum(values) / float(len(values))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_km = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    c = 2 * asin(sqrt(a))
    return earth_radius_km * c


def _to_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        text_value = value.strip()
        if not text_value:
            return []
        try:
            parsed = json.loads(text_value)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except json.JSONDecodeError:
            pass
        return [text_value]
    return [str(value).strip()]


def _pet_profile(pet: AdoptionPet) -> PetProfile:
    return PetProfile(
        id=int(pet.id),
        species=str(pet.species or "").lower(),
        breed=pet.breed,
        is_dangerous_dog=bool(pet.is_dangerous_dog),
        energy_level=float(pet.energy_level or 5.0),
        sociability=float(pet.sociability or 5.0),
        trainability=float(pet.trainability or 5.0),
        care_need=float(pet.care_need or 5.0),
        noise_level=float(pet.noise_level or 5.0),
        space_need=float(pet.space_need or 5.0),
        medical_need=float(pet.medical_need or 5.0),
        aggression_level=float(pet.aggression_level or 3.0),
        required_companion_hours=float(pet.required_companion_hours or 4.0),
        age_months=int(pet.age_months or 12),
        vaccinated=bool(pet.vaccinated),
        neutered=bool(pet.neutered),
        friendliness_human=float(pet.friendliness_human or 5.0),
        shelter_stress=float(pet.shelter_stress or 5.0),
        adoption_priority=float(pet.adoption_priority or 5.0),
        latitude=float(pet.latitude) if pet.latitude is not None else None,
        longitude=float(pet.longitude) if pet.longitude is not None else None,
    )


def _adopter_profiles(rows: list[Adopter]) -> list[AdopterProfile]:
    profiles: list[AdopterProfile] = []
    for row in rows:
        profiles.append(
            AdopterProfile(
                id=int(row.id),
                name=str(row.name or f"Adopter#{row.id}"),
                experience_level=str(row.experience_level or "novice").lower(),
                housing_area=float(row.housing_area or 0.0),
                budget=float(row.budget or 0.0),
                available_hours=float(row.available_hours or 0.0),
                latitude=float(row.latitude or 0.0),
                longitude=float(row.longitude or 0.0),
                resident_species=[x.lower() for x in _to_list(row.resident_species)],
                incompatible_species=[x.lower() for x in _to_list(row.incompatible_species)],
                preferred_species=[x.lower() for x in _to_list(row.preferred_species)],
                preferred_age_min=int(row.preferred_age_min or 0),
                preferred_age_max=int(row.preferred_age_max or 180),
                has_children=bool(row.has_children),
                has_elderly=bool(row.has_elderly),
                has_allergy_family=bool(row.has_allergy_family),
                work_from_home_days=float(row.work_from_home_days or 0.0),
                activity_level=float(row.activity_level or 5.0),
                patience_level=float(row.patience_level or 5.0),
                housing_type=str(row.housing_type or "apartment").lower(),
                has_yard=bool(row.has_yard),
                credit_score=float(row.credit_score or 70.0),
                historical_adoption_success=int(row.historical_adoption_success or 0),
            )
        )
    return profiles


def _hard_constraints(pet: PetProfile, adopter: AdopterProfile) -> tuple[bool, str]:
    if adopter.experience_level == "novice" and pet.is_dangerous_dog:
        return True, "新手领养人不能匹配危险犬"
    if adopter.has_children and pet.aggression_level >= 8:
        return True, "家庭有儿童且宠物攻击性过高"
    if pet.species and pet.species in set(adopter.incompatible_species):
        return True, "家庭现有宠物与该物种存在冲突"
    if adopter.available_hours < max(0.5, pet.required_companion_hours) * 0.3:
        return True, "可陪伴时长低于最低照护阈值"
    return False, ""


def _score_distance(pet: PetProfile, adopter: AdopterProfile) -> tuple[float, float]:
    if pet.latitude is None or pet.longitude is None:
        return 0.55, 0.0
    dist_km = _haversine_km(pet.latitude, pet.longitude, adopter.latitude, adopter.longitude)
    score = _clamp01(1.0 / (1.0 + dist_km / 4.0))
    return score, dist_km


def _score_environment(pet: PetProfile, adopter: AdopterProfile) -> float:
    required_hours = max(0.5, pet.required_companion_hours)
    time_score = _clamp01(adopter.available_hours / required_hours)
    area_required = 12.0 * max(1.0, pet.space_need)
    area_score = _clamp01(adopter.housing_area / area_required)
    wfh_score = _clamp01(adopter.work_from_home_days / 7.0)
    yard_bonus = 0.12 if adopter.has_yard and pet.space_need >= 6 else 0.0
    housing_penalty = 0.08 if adopter.housing_type == "apartment" and pet.space_need >= 8 else 0.0
    return _clamp01(0.45 * time_score + 0.35 * area_score + 0.2 * wfh_score + yard_bonus - housing_penalty)


def _estimate_monthly_cost(pet: PetProfile) -> float:
    medical_part = pet.medical_need * 110.0
    care_part = pet.care_need * 55.0
    age_part = max(0.0, float(pet.age_months - 36)) * 3.0
    behavior_part = pet.aggression_level * 20.0
    return round(180.0 + medical_part + care_part + age_part + behavior_part, 2)


def _score_medical_access(pet: PetProfile, adopter: AdopterProfile, clinics: list[tuple[float, float]]) -> tuple[float, int]:
    nearby_5km = 0
    for lat, lng in clinics:
        if _haversine_km(adopter.latitude, adopter.longitude, lat, lng) <= 5.0:
            nearby_5km += 1
    clinic_score = _clamp01(nearby_5km / 6.0)
    monthly_cost = _estimate_monthly_cost(pet)
    budget_score = _clamp01(adopter.budget / max(200.0, monthly_cost))
    vaccination_score = 1.0 if pet.vaccinated else 0.35
    neuter_score = 1.0 if pet.neutered else 0.55
    risk_score = _clamp01(1.0 - pet.medical_need / 11.0)
    score = 0.24 * clinic_score + 0.28 * budget_score + 0.18 * vaccination_score + 0.1 * neuter_score + 0.2 * risk_score
    return _clamp01(score), nearby_5km


def _score_preference(pet: PetProfile, adopter: AdopterProfile) -> float:
    preferred_species = set(adopter.preferred_species)
    species_score = 0.62 if not preferred_species else (1.0 if pet.species in preferred_species else 0.22)
    age_min = adopter.preferred_age_min
    age_max = max(age_min + 1, adopter.preferred_age_max)
    if age_min <= pet.age_months <= age_max:
        age_score = 1.0
    else:
        gap = min(abs(pet.age_months - age_min), abs(pet.age_months - age_max))
        age_score = _clamp01(1.0 - gap / 60.0)
    family_safety = 1.0
    if adopter.has_children:
        family_safety -= _clamp01(pet.aggression_level / 12.0)
    if adopter.has_elderly:
        family_safety -= _clamp01(pet.noise_level / 16.0)
    if adopter.has_allergy_family and pet.species in {"cat", "dog", "猫", "犬"}:
        family_safety -= 0.24
    return _clamp01(0.45 * species_score + 0.25 * age_score + 0.3 * family_safety)


def _score_behavior(pet: PetProfile, adopter: AdopterProfile) -> float:
    activity_fit = _clamp01(1.0 - abs(adopter.activity_level - pet.energy_level) / 10.0)
    required_patience = (pet.aggression_level + pet.shelter_stress) / 2.0
    patience_fit = _clamp01(1.0 - abs(adopter.patience_level - required_patience) / 10.0)
    trainability_fit = _clamp01(pet.trainability / 10.0)
    social_fit = _clamp01((pet.sociability + pet.friendliness_human) / 20.0)
    return _clamp01(0.3 * activity_fit + 0.3 * patience_fit + 0.2 * trainability_fit + 0.2 * social_fit)


def _score_health_cost(pet: PetProfile, adopter: AdopterProfile) -> float:
    monthly_cost = _estimate_monthly_cost(pet)
    budget_ratio = _clamp01(adopter.budget / max(200.0, monthly_cost))
    time_ratio = _clamp01(adopter.available_hours / max(1.0, pet.required_companion_hours))
    credit_ratio = _clamp01(adopter.credit_score / 100.0)
    history_ratio = _clamp01(float(adopter.historical_adoption_success) / 8.0)
    return _clamp01(0.4 * budget_ratio + 0.2 * time_ratio + 0.25 * credit_ratio + 0.15 * history_ratio)

def _adopter_similarity(a: AdopterProfile, b: AdopterProfile) -> float:
    diffs = [
        abs(a.housing_area - b.housing_area) / 160.0,
        abs(a.budget - b.budget) / 8000.0,
        abs(a.available_hours - b.available_hours) / 12.0,
        abs(a.activity_level - b.activity_level) / 10.0,
        abs(a.patience_level - b.patience_level) / 10.0,
    ]
    return _clamp01(1.0 - _avg(diffs))


def _upsert_status(
    adoption_pet_id: int,
    *,
    state: str | None = None,
    mode: str | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
    processed: int | None = None,
    total: int | None = None,
    error: str | None = None,
) -> MatchJobStatus:
    with _STATUS_LOCK:
        row = _MATCH_STATUS.get(adoption_pet_id)
        if row is None:
            row = MatchJobStatus(
                adoption_pet_id=adoption_pet_id,
                state="idle",
                mode="fast",
                started_at=None,
                finished_at=None,
                processed=0,
                total=0,
                error=None,
            )
            _MATCH_STATUS[adoption_pet_id] = row
        if state is not None:
            row.state = state
        if mode is not None:
            row.mode = mode
        if started_at is not None:
            row.started_at = started_at
        if finished_at is not None:
            row.finished_at = finished_at
        if processed is not None:
            row.processed = processed
        if total is not None:
            row.total = total
        if error is not None:
            row.error = error
        return row


def get_match_status(adoption_pet_id: int) -> dict[str, Any]:
    with _STATUS_LOCK:
        row = _MATCH_STATUS.get(adoption_pet_id)
        if row is None:
            return {
                "adoption_pet_id": adoption_pet_id,
                "state": "idle",
                "mode": "fast",
                "started_at": None,
                "finished_at": None,
                "processed": 0,
                "total": 0,
                "error": None,
            }
        return {
            "adoption_pet_id": row.adoption_pet_id,
            "state": row.state,
            "mode": row.mode,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
            "processed": row.processed,
            "total": row.total,
            "error": row.error,
        }


def _build_collab_context(
    db: Session,
    current_pet_id: int,
    adopters: list[AdopterProfile],
) -> dict[str, Any]:
    species_rows = db.execute(text("SELECT id, species FROM adoption_pets")).fetchall()
    pet_species_map = {int(r[0]): str(r[1] or "").lower() for r in species_rows}
    history_rows = db.execute(
        text(
            """
            SELECT adoption_pet_id, adopter_id, total_score, adopted, feedback_score
            FROM match_results
            WHERE adoption_pet_id != :pet_id
            """
        ),
        {"pet_id": current_pet_id},
    ).fetchall()

    adopter_personal_values: dict[int, list[float]] = {}
    adopter_species_values: dict[int, dict[str, list[float]]] = {}
    adopter_overall_values: dict[int, list[float]] = {}
    species_values: dict[str, list[float]] = {}

    for row in history_rows:
        pet_id = int(row[0])
        adopter_id = int(row[1])
        total_norm = _clamp01(float(row[2] or 0.0) / 100.0)
        adopted = 1.0 if bool(row[3]) else 0.0
        feedback = _clamp01(float(row[4] or 0.0) / 5.0)

        personal_score = 0.55 * total_norm + 0.25 * adopted + 0.2 * feedback
        species_score = 0.6 * total_norm + 0.4 * adopted
        species = pet_species_map.get(pet_id, "")

        adopter_personal_values.setdefault(adopter_id, []).append(personal_score)
        adopter_overall_values.setdefault(adopter_id, []).append(total_norm)
        if species:
            adopter_species_values.setdefault(adopter_id, {}).setdefault(species, []).append(species_score)
            species_values.setdefault(species, []).append(species_score)

    adopter_personal = {aid: _avg(vals, 0.5) for aid, vals in adopter_personal_values.items()}
    adopter_overall = {aid: _avg(vals, 0.5) for aid, vals in adopter_overall_values.items()}
    adopter_species = {
        aid: {sp: _avg(vals, 0.52) for sp, vals in by_species.items()}
        for aid, by_species in adopter_species_values.items()
    }
    global_species = {sp: _avg(vals, 0.52) for sp, vals in species_values.items()}

    adopter_map = {a.id: a for a in adopters}
    history_adopter_ids = [aid for aid in adopter_overall.keys() if aid in adopter_map]

    return {
        "adopter_personal": adopter_personal,
        "adopter_overall": adopter_overall,
        "adopter_species": adopter_species,
        "global_species": global_species,
        "adopter_map": adopter_map,
        "history_adopter_ids": history_adopter_ids,
    }


def _score_collaborative(
    pet: PetProfile,
    adopter: AdopterProfile,
    collab_ctx: dict[str, Any],
) -> tuple[float, dict[str, float]]:
    adopter_personal: dict[int, float] = collab_ctx["adopter_personal"]
    adopter_overall: dict[int, float] = collab_ctx["adopter_overall"]
    adopter_species: dict[int, dict[str, float]] = collab_ctx["adopter_species"]
    global_species: dict[str, float] = collab_ctx["global_species"]
    adopter_map: dict[int, AdopterProfile] = collab_ctx["adopter_map"]
    history_adopter_ids: list[int] = collab_ctx["history_adopter_ids"]

    personal = adopter_personal.get(adopter.id, 0.5)
    species_signal = global_species.get(pet.species, 0.52)

    neighbors: list[tuple[float, float]] = []
    for other_id in history_adopter_ids:
        if other_id == adopter.id:
            continue
        other = adopter_map.get(other_id)
        if other is None:
            continue
        sim = _adopter_similarity(adopter, other)
        if sim <= 0:
            continue
        by_species = adopter_species.get(other_id, {})
        base = by_species.get(pet.species, adopter_overall.get(other_id, 0.5))
        neighbors.append((sim, sim * base))

    if neighbors:
        neighbors.sort(key=lambda x: x[0], reverse=True)
        top = neighbors[:12]
        weighted_sum = sum(x[1] for x in top)
        weight_sum = sum(x[0] for x in top)
        neighbor_signal = _clamp01(weighted_sum / max(1e-6, weight_sum))
    else:
        neighbor_signal = 0.5

    score = _clamp01(0.45 * personal + 0.25 * species_signal + 0.3 * neighbor_signal)
    return score, {
        "personal": round(personal, 4),
        "species_signal": round(species_signal, 4),
        "neighbor_signal": round(neighbor_signal, 4),
    }


def _predict_speed_days(
    pet: PetProfile,
    total_score: float,
    s_pref: float,
    s_collab: float,
) -> tuple[int, str, dict[str, float]]:
    score_component = (1.0 - _clamp01(total_score / 100.0)) * 95.0
    age_penalty = max(0.0, float(pet.age_months - 24)) * 0.58
    medical_penalty = pet.medical_need * 4.8 + (0.0 if pet.vaccinated else 9.0)
    behavior_penalty = pet.aggression_level * 3.8 + pet.shelter_stress * 2.1
    care_penalty = pet.care_need * 1.6
    preference_bonus = s_pref * 26.0
    collab_bonus = s_collab * 20.0
    priority_bonus = pet.adoption_priority * 2.1

    days = int(round(16.0 + score_component + age_penalty + medical_penalty + behavior_penalty + care_penalty - preference_bonus - collab_bonus - priority_bonus))
    days = max(3, min(240, days))
    if days <= 20:
        level = "fast"
    elif days <= 55:
        level = "medium"
    elif days <= 100:
        level = "slow"
    else:
        level = "very_slow"
    return days, level, {
        "score_component": round(score_component, 2),
        "age_penalty": round(age_penalty, 2),
        "medical_penalty": round(medical_penalty, 2),
        "behavior_penalty": round(behavior_penalty, 2),
        "care_penalty": round(care_penalty, 2),
        "preference_bonus": round(preference_bonus, 2),
        "collab_bonus": round(collab_bonus, 2),
        "priority_bonus": round(priority_bonus, 2),
    }


def _build_rationale(score_parts: dict[str, float], speed_days: int, speed_level: str, dist_km: float) -> str:
    ranked = sorted(score_parts.items(), key=lambda x: x[1], reverse=True)
    top_two = ", ".join([f"{k}={v:.2f}" for k, v in ranked[:2]])
    low_two = ", ".join([f"{k}={v:.2f}" for k, v in ranked[-2:]])
    return f"强匹配维度: {top_two}; 待关注维度: {low_two}; 估计领养周期 {speed_days} 天({speed_level}), 距离约 {dist_km:.1f}km。"

def calculate_hybrid_score(
    *,
    pet: PetProfile,
    adopter: AdopterProfile,
    clinic_points: list[tuple[float, float]],
    collab_ctx: dict[str, Any],
) -> HybridScore:
    blocked, reason = _hard_constraints(pet, adopter)
    if blocked:
        return HybridScore(
            s_dist=0.0,
            s_env=0.0,
            s_med=0.0,
            s_pref=0.0,
            s_behavior=0.0,
            s_health_cost=0.0,
            s_collab=0.0,
            total_score=0.0,
            hard_blocked=True,
            predicted_speed_days=240,
            speed_level="very_slow",
            recommendation_confidence=0.2,
            rationale=f"硬约束拦截: {reason}",
            details={"hard_blocked_reason": reason},
        )

    s_dist, dist_km = _score_distance(pet, adopter)
    s_env = _score_environment(pet, adopter)
    s_med, nearby_5km = _score_medical_access(pet, adopter, clinic_points)
    s_pref = _score_preference(pet, adopter)
    s_behavior = _score_behavior(pet, adopter)
    s_health_cost = _score_health_cost(pet, adopter)
    s_collab, collab_parts = _score_collaborative(pet, adopter, collab_ctx)

    weight = {
        "s_dist": 0.16,
        "s_env": 0.18,
        "s_med": 0.16,
        "s_pref": 0.18,
        "s_behavior": 0.14,
        "s_health_cost": 0.10,
        "s_collab": 0.08,
    }
    raw_total = (
        weight["s_dist"] * s_dist
        + weight["s_env"] * s_env
        + weight["s_med"] * s_med
        + weight["s_pref"] * s_pref
        + weight["s_behavior"] * s_behavior
        + weight["s_health_cost"] * s_health_cost
        + weight["s_collab"] * s_collab
    )
    total_score = round(100.0 * _clamp01(raw_total), 2)
    predicted_speed_days, speed_level, speed_parts = _predict_speed_days(pet, total_score, s_pref, s_collab)

    completeness = _avg(
        [
            1.0 if pet.latitude is not None and pet.longitude is not None else 0.0,
            1.0 if adopter.latitude is not None and adopter.longitude is not None else 0.0,
            1.0 if adopter.preferred_species else 0.6,
            1.0 if adopter.preferred_age_max > adopter.preferred_age_min else 0.5,
            1.0 if adopter.budget > 0 else 0.4,
        ],
        0.5,
    )
    confidence = _clamp01(0.38 + 0.35 * completeness + 0.27 * s_collab)
    score_parts = {
        "s_dist": s_dist,
        "s_env": s_env,
        "s_med": s_med,
        "s_pref": s_pref,
        "s_behavior": s_behavior,
        "s_health_cost": s_health_cost,
        "s_collab": s_collab,
    }
    details: dict[str, Any] = {
        "distance_km": round(dist_km, 3),
        "nearby_clinic_count_5km": nearby_5km,
        "monthly_cost_estimate": _estimate_monthly_cost(pet),
        "collaborative_parts": collab_parts,
        "speed_parts": speed_parts,
        "weights": weight,
    }
    return HybridScore(
        s_dist=round(s_dist, 4),
        s_env=round(s_env, 4),
        s_med=round(s_med, 4),
        s_pref=round(s_pref, 4),
        s_behavior=round(s_behavior, 4),
        s_health_cost=round(s_health_cost, 4),
        s_collab=round(s_collab, 4),
        total_score=total_score,
        hard_blocked=False,
        predicted_speed_days=predicted_speed_days,
        speed_level=speed_level,
        recommendation_confidence=round(confidence, 4),
        rationale=_build_rationale(score_parts, predicted_speed_days, speed_level, dist_km),
        details=details,
    )


def _quick_prefilter_adopters(pet: PetProfile, adopters: list[AdopterProfile], top_n: int) -> list[AdopterProfile]:
    scored: list[tuple[float, AdopterProfile]] = []
    for adopter in adopters:
        blocked, _ = _hard_constraints(pet, adopter)
        if blocked:
            continue
        dist_score, _ = _score_distance(pet, adopter)
        pref_hit = 0.7 if not adopter.preferred_species else (1.0 if pet.species in adopter.preferred_species else 0.15)
        budget_score = _clamp01(adopter.budget / max(200.0, _estimate_monthly_cost(pet)))
        env_hint = _clamp01(adopter.available_hours / max(0.5, pet.required_companion_hours))
        quick_score = 0.3 * dist_score + 0.25 * pref_hit + 0.25 * budget_score + 0.2 * env_hint
        scored.append((quick_score, adopter))
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [x[1] for x in scored[: max(20, top_n)]]
    if len(selected) < min(top_n, len(adopters)):
        existing_ids = {s.id for s in selected}
        missing = [a for a in adopters if a.id not in existing_ids]
        selected.extend(missing[: max(0, top_n - len(selected))])
    return selected


def run_paci_matching(
    db: Session,
    adoption_pet_id: int,
    *,
    mode: str = "fast",
    top_n: int = FAST_DEFAULT_TOP_N,
    progress_hook: Callable[[int, int], None] | None = None,
) -> list[MatchResult]:
    mode = str(mode or "fast").lower()
    top_n = max(20, min(int(top_n or FAST_DEFAULT_TOP_N), 2000))

    pet_row = db.query(AdoptionPet).filter(AdoptionPet.id == adoption_pet_id).first()
    if pet_row is None:
        return []
    pet = _pet_profile(pet_row)

    adopter_rows = db.query(Adopter).all()
    if not adopter_rows:
        return []
    adopters = _adopter_profiles(adopter_rows)
    total_adopters = len(adopters)

    if mode == "fast":
        target_adopters = _quick_prefilter_adopters(pet, adopters, min(top_n, total_adopters))
    else:
        target_adopters = adopters

    owner_coords = db.execute(
        text("SELECT latitude, longitude FROM owners WHERE latitude IS NOT NULL AND longitude IS NOT NULL LIMIT 500")
    ).fetchall()
    clinic_points = [(float(lat), float(lng)) for lat, lng in owner_coords]
    collab_ctx = _build_collab_context(db, adoption_pet_id, adopters)

    existing_rows = db.query(MatchResult).filter(MatchResult.adoption_pet_id == adoption_pet_id).all()
    row_by_adopter = {int(r.adopter_id): r for r in existing_rows}

    results: list[MatchResult] = []
    now_iso = _now().isoformat()
    processed = 0
    for adopter in target_adopters:
        score = calculate_hybrid_score(
            pet=pet,
            adopter=adopter,
            clinic_points=clinic_points,
            collab_ctx=collab_ctx,
        )
        row = row_by_adopter.get(adopter.id)
        if row is None:
            row = MatchResult(adoption_pet_id=adoption_pet_id, adopter_id=adopter.id)
            db.add(row)
            row_by_adopter[adopter.id] = row

        row.s_dist = score.s_dist
        row.s_env = score.s_env
        row.s_med = score.s_med
        row.s_pref = score.s_pref
        row.s_behavior = score.s_behavior
        row.s_health_cost = score.s_health_cost
        row.s_collab = score.s_collab
        row.total_score = score.total_score
        row.hard_blocked = score.hard_blocked
        row.predicted_speed_days = score.predicted_speed_days
        row.speed_level = score.speed_level
        row.recommendation_confidence = score.recommendation_confidence
        row.model_version = f"{MODEL_VERSION}_{mode}"
        row.rationale = score.rationale
        row.details = {
            **(score.details or {}),
            "computed_at": now_iso,
            "compute_mode": mode,
        }
        results.append(row)

        processed += 1
        if progress_hook and (processed % 25 == 0 or processed == len(target_adopters)):
            progress_hook(processed, len(target_adopters))

    db.commit()
    results.sort(
        key=lambda x: (float(x.total_score or 0), float(x.recommendation_confidence or 0), -float(x.predicted_speed_days or 240)),
        reverse=True,
    )
    return results

def _run_full_job(adoption_pet_id: int) -> None:
    started = _now()
    db = SessionLocal()
    try:
        total = db.query(Adopter.id).count()
        _upsert_status(
            adoption_pet_id,
            state="running",
            mode="full",
            started_at=started,
            finished_at=None,
            processed=0,
            total=total,
            error=None,
        )

        def _progress(processed: int, total_items: int) -> None:
            _upsert_status(adoption_pet_id, processed=processed, total=total_items)

        run_paci_matching(db, adoption_pet_id, mode="full", top_n=total, progress_hook=_progress)
        _upsert_status(
            adoption_pet_id,
            state="completed",
            mode="full",
            finished_at=_now(),
            processed=total,
            total=total,
            error=None,
        )
    except Exception as exc:  # pragma: no cover
        _upsert_status(
            adoption_pet_id,
            state="failed",
            mode="full",
            finished_at=_now(),
            error=str(exc),
        )
    finally:
        db.close()
        with _STATUS_LOCK:
            _RUNNING_FULL.discard(adoption_pet_id)


def enqueue_full_matching(adoption_pet_id: int) -> dict[str, Any]:
    with _STATUS_LOCK:
        if adoption_pet_id in _RUNNING_FULL:
            row = _MATCH_STATUS.get(adoption_pet_id)
            return {
                "scheduled": False,
                "state": row.state if row else "running",
                "message": "full matching already running",
            }
        _RUNNING_FULL.add(adoption_pet_id)
    FULL_JOB_POOL.submit(_run_full_job, adoption_pet_id)
    return {"scheduled": True, "state": "running", "message": "full matching started"}


def _freshness_label(last_computed_at: datetime | None) -> str:
    if last_computed_at is None:
        return "unknown"
    age = _now() - last_computed_at
    if age <= timedelta(minutes=2):
        return "fresh"
    if age <= timedelta(minutes=10):
        return "warming"
    return "stale"


def get_algorithm_profile() -> dict[str, Any]:
    return {
        "model_version": MODEL_VERSION,
        "summary": "Hybrid recommendation = 内容特征匹配 + 协同过滤信号 + 领养速度预测。",
        "steps": [
            "Step1 硬约束过滤：新手危险犬、家庭儿童高攻击性、物种冲突、最低陪伴时长。",
            "Step2 多维内容评分：距离、环境、医疗可达、偏好、行为契合、健康成本。",
            "Step3 协同信号：历史反馈 + 同类领养成功 + 相似领养人近邻偏好。",
            "Step4 速度预测：综合分映射预计领养天数与速度等级。",
            "Step5 可解释输出：维度分解、速度因子、置信度。",
        ],
        "weights": {
            "s_dist": 0.16,
            "s_env": 0.18,
            "s_med": 0.16,
            "s_pref": 0.18,
            "s_behavior": 0.14,
            "s_health_cost": 0.10,
            "s_collab": 0.08,
        },
        "speed_level_rule": {"fast": "<=20", "medium": "21-55", "slow": "56-100", "very_slow": ">100"},
    }


def build_matching_dashboard(db: Session, adoption_pet_id: int, top_n: int = 20) -> dict[str, Any]:
    top_n = max(5, min(int(top_n or 20), 200))
    rows = (
        db.query(MatchResult)
        .filter(MatchResult.adoption_pet_id == adoption_pet_id)
        .order_by(MatchResult.total_score.desc(), MatchResult.predicted_speed_days.asc())
        .all()
    )
    adopter_rows = db.query(Adopter.id, Adopter.name).all()
    adopter_name_map = {int(r[0]): str(r[1]) for r in adopter_rows}
    total_adopters = len(adopter_rows)

    status = get_match_status(adoption_pet_id)
    last_completed_at = None
    if status.get("finished_at"):
        try:
            last_completed_at = datetime.fromisoformat(str(status["finished_at"]))
        except ValueError:
            last_completed_at = None

    if not rows:
        return {
            "overview": {
                "candidate_count": 0,
                "hard_blocked_count": 0,
                "hard_blocked_ratio": 0.0,
                "avg_score": 0.0,
                "avg_speed_days": 0.0,
                "fast_ratio": 0.0,
            },
            "meta": {
                "compute_mode": status.get("mode", "fast"),
                "data_freshness": _freshness_label(last_completed_at),
                "last_computed_at": status.get("finished_at"),
                "is_partial": True,
                "status": status,
            },
            "top_matches": [],
            "speed_distribution": [],
            "score_breakdown_mean": [],
            "scatter": [],
        }

    valid_rows = [r for r in rows if not bool(r.hard_blocked)]
    target_rows = valid_rows if valid_rows else rows
    use_top = target_rows[: max(5, min(top_n, len(target_rows)))]

    hard_blocked_count = len([r for r in rows if bool(r.hard_blocked)])
    overview = {
        "candidate_count": len(rows),
        "hard_blocked_count": hard_blocked_count,
        "hard_blocked_ratio": round(hard_blocked_count / max(1, len(rows)), 4),
        "avg_score": round(_avg([float(r.total_score or 0.0) for r in target_rows]), 2),
        "avg_speed_days": round(_avg([float(r.predicted_speed_days or 0.0) for r in target_rows]), 2),
        "fast_ratio": round(len([r for r in target_rows if str(r.speed_level) == "fast"]) / max(1, len(target_rows)), 4),
    }

    speed_count: dict[str, int] = {"fast": 0, "medium": 0, "slow": 0, "very_slow": 0}
    for row in target_rows:
        key = str(row.speed_level or "very_slow")
        speed_count[key] = speed_count.get(key, 0) + 1
    total_speed = max(1, sum(speed_count.values()))
    speed_distribution = [
        {"name": k, "value": v, "percent": round((v / total_speed) * 100.0, 1)}
        for k, v in speed_count.items()
    ]

    score_breakdown_mean = [
        {"name": "distance", "value": round(_avg([float(r.s_dist or 0.0) for r in target_rows]) * 100.0, 1)},
        {"name": "environment", "value": round(_avg([float(r.s_env or 0.0) for r in target_rows]) * 100.0, 1)},
        {"name": "medical", "value": round(_avg([float(r.s_med or 0.0) for r in target_rows]) * 100.0, 1)},
        {"name": "preference", "value": round(_avg([float(r.s_pref or 0.0) for r in target_rows]) * 100.0, 1)},
        {"name": "behavior", "value": round(_avg([float(r.s_behavior or 0.0) for r in target_rows]) * 100.0, 1)},
        {"name": "health_cost", "value": round(_avg([float(r.s_health_cost or 0.0) for r in target_rows]) * 100.0, 1)},
        {"name": "collaborative", "value": round(_avg([float(r.s_collab or 0.0) for r in target_rows]) * 100.0, 1)},
    ]

    top_matches = []
    scatter = []
    for row in use_top:
        name = adopter_name_map.get(int(row.adopter_id), f"Adopter#{row.adopter_id}")
        top_matches.append(
            {
                "id": row.id,
                "adopter_id": row.adopter_id,
                "adopter_name": name,
                "total_score": float(row.total_score or 0.0),
                "predicted_speed_days": int(row.predicted_speed_days or 240),
                "speed_level": str(row.speed_level or "very_slow"),
                "recommendation_confidence": float(row.recommendation_confidence or 0.0),
                "s_dist": float(row.s_dist or 0.0),
                "s_env": float(row.s_env or 0.0),
                "s_med": float(row.s_med or 0.0),
                "s_pref": float(row.s_pref or 0.0),
                "s_behavior": float(row.s_behavior or 0.0),
                "s_health_cost": float(row.s_health_cost or 0.0),
                "s_collab": float(row.s_collab or 0.0),
                "hard_blocked": bool(row.hard_blocked),
                "rationale": row.rationale,
                "details": row.details or {},
            }
        )
        scatter.append(
            {
                "name": name,
                "score": round(float(row.total_score or 0.0), 1),
                "speed_days": int(row.predicted_speed_days or 240),
                "confidence": round(float(row.recommendation_confidence or 0.0), 4),
            }
        )

    is_partial = len(rows) < total_adopters or bool(status.get("state") == "running" and status.get("mode") == "full")
    meta = {
        "compute_mode": status.get("mode", "fast"),
        "data_freshness": _freshness_label(last_completed_at),
        "last_computed_at": status.get("finished_at"),
        "is_partial": is_partial,
        "status": status,
    }
    return {
        "overview": overview,
        "meta": meta,
        "top_matches": top_matches,
        "speed_distribution": speed_distribution,
        "score_breakdown_mean": score_breakdown_mean,
        "scatter": scatter,
    }
