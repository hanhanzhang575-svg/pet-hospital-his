"""Generate large synthetic data for adoption matching module."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from statistics import mean

from sqlalchemy import text

from backend.database import SessionLocal, engine
from backend.models.core import AdoptionPet, Adopter, MatchResult, Owner, Pet


SPECIES_CHOICES = ["dog", "cat"]
DOG_BREEDS = ["Labrador", "Corgi", "Shiba", "Golden Retriever", "Border Collie", "Poodle", "Husky"]
CAT_BREEDS = ["British Shorthair", "Ragdoll", "Siamese", "Persian", "Domestic Shorthair", "Maine Coon"]
HOUSING_TYPES = ["apartment", "house", "townhouse", "loft"]
NAME_SURNAMES = list("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨")
NAME_GIVEN = list("晨雨轩宁逸瑶萌浩宇安然雅彤梓涵诗琪思远可欣")


def ensure_adoption_columns() -> None:
    """Ensure required columns exist for upgraded hybrid schema."""
    with engine.begin() as conn:
        adoption_pet_columns = conn.execute(text("PRAGMA table_info(adoption_pets);")).fetchall()
        adoption_pet_names = {str(row[1]) for row in adoption_pet_columns}
        if "age_months" not in adoption_pet_names:
            conn.execute(text("ALTER TABLE adoption_pets ADD COLUMN age_months INTEGER NOT NULL DEFAULT 12"))
        if "vaccinated" not in adoption_pet_names:
            conn.execute(text("ALTER TABLE adoption_pets ADD COLUMN vaccinated BOOLEAN NOT NULL DEFAULT 1"))
        if "neutered" not in adoption_pet_names:
            conn.execute(text("ALTER TABLE adoption_pets ADD COLUMN neutered BOOLEAN NOT NULL DEFAULT 0"))
        if "body_condition_score" not in adoption_pet_names:
            conn.execute(text("ALTER TABLE adoption_pets ADD COLUMN body_condition_score FLOAT NOT NULL DEFAULT 5.0"))
        if "friendliness_human" not in adoption_pet_names:
            conn.execute(text("ALTER TABLE adoption_pets ADD COLUMN friendliness_human FLOAT NOT NULL DEFAULT 5.0"))
        if "friendliness_pet" not in adoption_pet_names:
            conn.execute(text("ALTER TABLE adoption_pets ADD COLUMN friendliness_pet FLOAT NOT NULL DEFAULT 5.0"))
        if "shelter_stress" not in adoption_pet_names:
            conn.execute(text("ALTER TABLE adoption_pets ADD COLUMN shelter_stress FLOAT NOT NULL DEFAULT 5.0"))
        if "adoption_priority" not in adoption_pet_names:
            conn.execute(text("ALTER TABLE adoption_pets ADD COLUMN adoption_priority FLOAT NOT NULL DEFAULT 5.0"))

        adopter_columns = conn.execute(text("PRAGMA table_info(adopters);")).fetchall()
        adopter_names = {str(row[1]) for row in adopter_columns}
        if "preferred_species" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN preferred_species JSON NOT NULL DEFAULT '[]'"))
        if "preferred_age_min" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN preferred_age_min INTEGER NOT NULL DEFAULT 0"))
        if "preferred_age_max" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN preferred_age_max INTEGER NOT NULL DEFAULT 180"))
        if "has_children" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN has_children BOOLEAN NOT NULL DEFAULT 0"))
        if "has_elderly" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN has_elderly BOOLEAN NOT NULL DEFAULT 0"))
        if "has_allergy_family" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN has_allergy_family BOOLEAN NOT NULL DEFAULT 0"))
        if "work_from_home_days" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN work_from_home_days FLOAT NOT NULL DEFAULT 0.0"))
        if "activity_level" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN activity_level FLOAT NOT NULL DEFAULT 5.0"))
        if "patience_level" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN patience_level FLOAT NOT NULL DEFAULT 5.0"))
        if "housing_type" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN housing_type VARCHAR(20) NOT NULL DEFAULT 'apartment'"))
        if "has_yard" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN has_yard BOOLEAN NOT NULL DEFAULT 0"))
        if "credit_score" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN credit_score FLOAT NOT NULL DEFAULT 70.0"))
        if "historical_adoption_success" not in adopter_names:
            conn.execute(text("ALTER TABLE adopters ADD COLUMN historical_adoption_success INTEGER NOT NULL DEFAULT 0"))

        match_columns = conn.execute(text("PRAGMA table_info(match_results);")).fetchall()
        match_names = {str(row[1]) for row in match_columns}
        if "s_pref" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN s_pref FLOAT NOT NULL DEFAULT 0.0"))
        if "s_behavior" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN s_behavior FLOAT NOT NULL DEFAULT 0.0"))
        if "s_health_cost" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN s_health_cost FLOAT NOT NULL DEFAULT 0.0"))
        if "s_collab" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN s_collab FLOAT NOT NULL DEFAULT 0.0"))
        if "predicted_speed_days" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN predicted_speed_days INTEGER NOT NULL DEFAULT 120"))
        if "speed_level" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN speed_level VARCHAR(20) NOT NULL DEFAULT 'slow'"))
        if "recommendation_confidence" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN recommendation_confidence FLOAT NOT NULL DEFAULT 0.5"))
        if "model_version" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN model_version VARCHAR(40) NOT NULL DEFAULT 'hybrid_v2'"))
        if "adopted" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN adopted BOOLEAN NOT NULL DEFAULT 0"))
        if "feedback_score" not in match_names:
            conn.execute(text("ALTER TABLE match_results ADD COLUMN feedback_score FLOAT NOT NULL DEFAULT 0.0"))


def _rand_cn_name(index: int) -> str:
    return f"{random.choice(NAME_SURNAMES)}{random.choice(NAME_GIVEN)}{index % 97}"


def _rand_coord() -> tuple[float, float]:
    # Around Dalian city area.
    return (
        round(38.7 + random.random() * 0.55, 6),
        round(121.2 + random.random() * 0.75, 6),
    )


def _pet_profile(species: str) -> tuple[str, float, float, float]:
    if species == "dog":
        return random.choice(DOG_BREEDS), random.uniform(4.0, 9.5), random.uniform(3.0, 8.0), random.uniform(3.0, 9.0)
    return random.choice(CAT_BREEDS), random.uniform(2.0, 7.0), random.uniform(2.0, 7.0), random.uniform(2.0, 7.0)


def generate_data(
    *,
    new_owners: int,
    new_pets: int,
    new_adopters: int,
    new_adoption_pets: int,
    history_rows: int,
) -> None:
    ensure_adoption_columns()
    db = SessionLocal()
    now = datetime.now()
    try:
        owners_before = db.query(Owner).count()
        pets_before = db.query(Pet).count()
        adopters_before = db.query(Adopter).count()
        adoption_pets_before = db.query(AdoptionPet).count()
        match_before = db.query(MatchResult).count()

        max_owner_id = db.query(Owner.id).order_by(Owner.id.desc()).first()
        max_pet_id = db.query(Pet.id).order_by(Pet.id.desc()).first()
        owner_base = int(max_owner_id[0]) if max_owner_id else 0
        pet_base = int(max_pet_id[0]) if max_pet_id else 0

        owners_batch: list[Owner] = []
        for i in range(1, new_owners + 1):
            lat, lng = _rand_coord()
            code = f"OX{owner_base + i:06d}"
            owners_batch.append(
                Owner(
                    owner_code=code,
                    name=_rand_cn_name(owner_base + i),
                    phone=f"139{random.randint(10000000, 99999999)}",
                    telephone=f"0411-{random.randint(2000000, 8999999)}",
                    address=f"大连市样本街区{random.randint(1, 500)}号",
                    member_level=random.choice(["normal", "silver", "gold", "diamond"]),
                    latitude=lat,
                    longitude=lng,
                )
            )
        db.add_all(owners_batch)
        db.commit()

        owner_ids = [oid for (oid,) in db.query(Owner.id).all()]
        pets_batch: list[Pet] = []
        for i in range(1, new_pets + 1):
            species = random.choice(SPECIES_CHOICES)
            breed, weight, care_need, med_need = _pet_profile(species)
            pet_code = f"PX{pet_base + i:07d}"
            birth_days = random.randint(30, 3650)
            pet_name = f"{random.choice(['团子', '毛毛', '可乐', '奶糖', '栗子', '元宝'])}{pet_base + i}"
            pets_batch.append(
                Pet(
                    pet_code=pet_code,
                    name=pet_name,
                    species=species,
                    breed=breed,
                    gender=random.choice(["male", "female"]),
                    birth_date=(datetime.now() - timedelta(days=birth_days)).date(),
                    color=random.choice(["white", "black", "brown", "orange", "tabby", "mixed"]),
                    type_id=1 if species == "dog" else 2,
                    weight=round(weight, 2),
                    allergy_history=[],
                    owner_id=random.choice(owner_ids),
                    clinic_id=random.choice(["C001", "C002", "C003"]),
                )
            )
        db.add_all(pets_batch)
        db.commit()

        all_owner_rows = db.query(Owner.id, Owner.name, Owner.latitude, Owner.longitude).all()
        owner_map = {int(row[0]): row for row in all_owner_rows}
        pet_ids_no_adoption = [
            int(pid) for (pid,) in db.execute(
                text(
                    """
                    SELECT p.id
                    FROM pets p
                    LEFT JOIN adoption_pets ap ON ap.pet_id = p.id
                    WHERE ap.id IS NULL
                    """
                )
            ).fetchall()
        ]
        random.shuffle(pet_ids_no_adoption)
        selected_adoption_pet_ids = pet_ids_no_adoption[:new_adoption_pets]

        adoption_batch: list[AdoptionPet] = []
        pet_meta_rows = db.query(Pet.id, Pet.species, Pet.breed, Pet.owner_id, Pet.birth_date).filter(Pet.id.in_(selected_adoption_pet_ids)).all()
        for row in pet_meta_rows:
            pid = int(row[0])
            species = str(row[1] or "cat").lower()
            owner_row = owner_map.get(int(row[3])) if row[3] else None
            lat = float(owner_row[2]) if owner_row and owner_row[2] is not None else _rand_coord()[0]
            lng = float(owner_row[3]) if owner_row and owner_row[3] is not None else _rand_coord()[1]
            age_months = 12
            if row[4] is not None:
                age_months = max(2, int((datetime.now().date() - row[4]).days / 30))
            adoption_batch.append(
                AdoptionPet(
                    pet_id=pid,
                    species=species,
                    breed=row[2],
                    is_dangerous_dog=True if species == "dog" and random.random() < 0.1 else False,
                    energy_level=round(random.uniform(2.0, 10.0), 2),
                    sociability=round(random.uniform(2.0, 10.0), 2),
                    trainability=round(random.uniform(2.0, 10.0), 2),
                    care_need=round(random.uniform(2.0, 10.0), 2),
                    noise_level=round(random.uniform(1.0, 10.0), 2),
                    space_need=round(random.uniform(2.0, 10.0), 2),
                    medical_need=round(random.uniform(1.0, 10.0), 2),
                    aggression_level=round(random.uniform(1.0, 10.0), 2),
                    required_companion_hours=round(random.uniform(1.0, 10.0), 2),
                    age_months=age_months,
                    vaccinated=True if random.random() < 0.82 else False,
                    neutered=True if random.random() < 0.56 else False,
                    body_condition_score=round(random.uniform(3.0, 8.5), 2),
                    friendliness_human=round(random.uniform(2.0, 10.0), 2),
                    friendliness_pet=round(random.uniform(2.0, 10.0), 2),
                    shelter_stress=round(random.uniform(1.0, 10.0), 2),
                    adoption_priority=round(random.uniform(1.0, 10.0), 2),
                    latitude=lat,
                    longitude=lng,
                    status=random.choice(["待领养", "待领养", "待领养", "可领养"]),
                )
            )
        db.add_all(adoption_batch)
        db.commit()

        max_adopter_id = db.query(Adopter.id).order_by(Adopter.id.desc()).first()
        adopter_start = int(max_adopter_id[0]) if max_adopter_id else 0
        adopters_batch: list[Adopter] = []
        for i in range(1, new_adopters + 1):
            owner = random.choice(all_owner_rows)
            lat = float(owner[2]) if owner[2] is not None else _rand_coord()[0]
            lng = float(owner[3]) if owner[3] is not None else _rand_coord()[1]
            preferred = random.sample(SPECIES_CHOICES, k=random.choice([1, 1, 2]))
            min_age = random.choice([0, 2, 6, 12, 24])
            max_age = min_age + random.randint(12, 168)
            adopters_batch.append(
                Adopter(
                    owner_id=int(owner[0]) if random.random() < 0.75 else None,
                    name=f"领养人{adopter_start + i}_{_rand_cn_name(adopter_start + i)}",
                    experience_level=random.choice(["novice", "intermediate", "expert"]),
                    housing_area=round(random.uniform(25.0, 220.0), 2),
                    budget=round(random.uniform(500.0, 12000.0), 2),
                    available_hours=round(random.uniform(0.5, 12.0), 2),
                    latitude=lat,
                    longitude=lng,
                    resident_species=random.sample(SPECIES_CHOICES, k=random.choice([0, 1])),
                    incompatible_species=random.sample(SPECIES_CHOICES, k=random.choice([0, 0, 1])),
                    preferred_species=preferred,
                    preferred_age_min=min_age,
                    preferred_age_max=max_age,
                    has_children=True if random.random() < 0.35 else False,
                    has_elderly=True if random.random() < 0.2 else False,
                    has_allergy_family=True if random.random() < 0.12 else False,
                    work_from_home_days=round(random.uniform(0.0, 7.0), 1),
                    activity_level=round(random.uniform(1.0, 10.0), 2),
                    patience_level=round(random.uniform(1.0, 10.0), 2),
                    housing_type=random.choice(HOUSING_TYPES),
                    has_yard=True if random.random() < 0.4 else False,
                    credit_score=round(random.uniform(45.0, 98.0), 2),
                    historical_adoption_success=random.randint(0, 6),
                )
            )
        db.add_all(adopters_batch)
        db.commit()

        adoption_pet_ids = [pid for (pid,) in db.query(AdoptionPet.id).all()]
        adopter_ids = [aid for (aid,) in db.query(Adopter.id).all()]
        existing_pairs = {(int(r[0]), int(r[1])) for r in db.query(MatchResult.adoption_pet_id, MatchResult.adopter_id).all()}

        weights = {
            "s_dist": 0.16,
            "s_env": 0.18,
            "s_med": 0.16,
            "s_pref": 0.18,
            "s_behavior": 0.14,
            "s_health_cost": 0.10,
            "s_collab": 0.08,
        }

        rows_to_add: list[MatchResult] = []
        created = 0
        attempts = 0
        max_attempts = max(history_rows * 12, 5000)
        while created < history_rows and attempts < max_attempts:
            attempts += 1
            pet_id = random.choice(adoption_pet_ids)
            adopter_id = random.choice(adopter_ids)
            pair = (pet_id, adopter_id)
            if pair in existing_pairs:
                continue
            existing_pairs.add(pair)

            scores = {
                "s_dist": random.random(),
                "s_env": random.random(),
                "s_med": random.random(),
                "s_pref": random.random(),
                "s_behavior": random.random(),
                "s_health_cost": random.random(),
                "s_collab": random.random(),
            }
            total = 100 * sum(scores[k] * w for k, w in weights.items())
            total = round(max(0.0, min(100.0, total)), 2)
            speed_days = max(3, min(220, int(round(180 - total * 1.4 + random.uniform(-18, 24)))))
            if speed_days <= 20:
                speed_level = "fast"
            elif speed_days <= 55:
                speed_level = "medium"
            elif speed_days <= 100:
                speed_level = "slow"
            else:
                speed_level = "very_slow"

            adopted = True if random.random() < (total / 125.0) else False
            feedback = round(random.uniform(2.0, 5.0), 2) if adopted else round(random.uniform(0.0, 3.5), 2)
            confidence = round(min(0.99, max(0.35, mean(list(scores.values())) + random.uniform(-0.08, 0.08))), 4)

            rows_to_add.append(
                MatchResult(
                    adoption_pet_id=pet_id,
                    adopter_id=adopter_id,
                    s_dist=round(scores["s_dist"], 4),
                    s_env=round(scores["s_env"], 4),
                    s_med=round(scores["s_med"], 4),
                    s_pref=round(scores["s_pref"], 4),
                    s_behavior=round(scores["s_behavior"], 4),
                    s_health_cost=round(scores["s_health_cost"], 4),
                    s_collab=round(scores["s_collab"], 4),
                    total_score=total,
                    hard_blocked=False if random.random() < 0.95 else True,
                    predicted_speed_days=speed_days,
                    speed_level=speed_level,
                    recommendation_confidence=confidence,
                    model_version="synthetic_v1",
                    adopted=adopted,
                    feedback_score=feedback,
                    rationale="Synthetic historical interaction for collaborative signal bootstrap.",
                    details={"source": "synthetic", "generated_at": now.isoformat()},
                )
            )
            created += 1

            if len(rows_to_add) >= 2000:
                db.add_all(rows_to_add)
                db.commit()
                rows_to_add.clear()
        if rows_to_add:
            db.add_all(rows_to_add)
            db.commit()

        print("=" * 60)
        print("Adoption synthetic data generation completed.")
        print(f"Owners: {owners_before} -> {db.query(Owner).count()} (+{new_owners})")
        print(f"Pets: {pets_before} -> {db.query(Pet).count()} (+{new_pets})")
        print(f"Adopters: {adopters_before} -> {db.query(Adopter).count()} (+{new_adopters})")
        print(f"AdoptionPets: {adoption_pets_before} -> {db.query(AdoptionPet).count()} (+{len(adoption_batch)})")
        print(f"MatchResults: {match_before} -> {db.query(MatchResult).count()} (+{created})")
        print("=" * 60)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate non-duplicate synthetic data for adoption module.")
    parser.add_argument("--seed", type=int, default=20260414, help="Random seed for reproducibility.")
    parser.add_argument("--new-owners", type=int, default=220, help="Number of new owners.")
    parser.add_argument("--new-pets", type=int, default=520, help="Number of new pets.")
    parser.add_argument("--new-adopters", type=int, default=680, help="Number of new adopters.")
    parser.add_argument("--new-adoption-pets", type=int, default=360, help="Number of pets inserted into adoption pool.")
    parser.add_argument("--history-rows", type=int, default=18000, help="Number of historical match rows.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    random.seed(args.seed)
    generate_data(
        new_owners=args.new_owners,
        new_pets=args.new_pets,
        new_adopters=args.new_adopters,
        new_adoption_pets=args.new_adoption_pets,
        history_rows=args.history_rows,
    )
