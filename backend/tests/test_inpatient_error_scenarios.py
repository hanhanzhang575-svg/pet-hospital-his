"""住院记录更新异常场景验证脚本。"""

from __future__ import annotations

from datetime import datetime, timedelta

from backend.database import SessionLocal
from backend.models.core import CageUnit, InpatientRecord, Owner, Pet, Role, User
from backend.schemas.inpatient import InpatientRecordUpdate
from backend.services.inpatient_service import update_inpatient_record


def ensure_base_data() -> int:
    """确保存在可用于更新的住院记录，并返回记录ID。"""
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "doctor").first()
        if role is None:
            role = Role(name="doctor", description="执业兽医师")
            db.add(role)
            db.commit()
            db.refresh(role)

        doctor = db.query(User).filter(User.username == "inpatient_test_doctor").first()
        if doctor is None:
            doctor = User(
                employee_code="D010101188",
                username="inpatient_test_doctor",
                password_hash="test_hash",
                full_name="住院测试医生",
                role_id=role.id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=True,
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)

        owner = db.query(Owner).filter(Owner.owner_code == "TEST-OWNER-001").first()
        if owner is None:
            owner = Owner(
                owner_code="TEST-OWNER-001",
                name="住院测试主人",
                phone="13800001111",
                member_level="normal",
            )
            db.add(owner)
            db.commit()
            db.refresh(owner)

        pet = db.query(Pet).filter(Pet.pet_code == "C001TEST001").first()
        if pet is None:
            pet = Pet(
                pet_code="C001TEST001",
                name="住院测试宠物",
                species="犬",
                breed="测试犬",
                gender="公",
                birth_date="2021-01-01",
                weight=10.0,
                allergy_history=[],
                owner_id=owner.id,
                clinic_id="C001",
            )
            db.add(pet)
            db.commit()
            db.refresh(pet)

        cage = db.query(CageUnit).filter(CageUnit.cage_code == "TEST-CAGE-01").first()
        if cage is None:
            cage = CageUnit(
                cage_code="TEST-CAGE-01",
                clinic_id="C001",
                zone_type="犬区",
                status="住院中",
                current_pet_id=pet.id,
                adjacent_cage_ids=[],
            )
            db.add(cage)
            db.commit()
            db.refresh(cage)

        record = (
            db.query(InpatientRecord)
            .filter(InpatientRecord.pet_id == pet.id, InpatientRecord.status != "已出院")
            .order_by(InpatientRecord.id.desc())
            .first()
        )
        if record is None:
            record = InpatientRecord(
                pet_id=pet.id,
                cage_id=cage.id,
                doctor_id=doctor.id,
                clinic_id="C001",
                admission_time=datetime.now() - timedelta(days=1),
                deposit_amount=1000.0,
                consumed_amount=200.0,
                status="住院观察",
            )
            db.add(record)
            db.commit()
            db.refresh(record)
        return record.id
    finally:
        db.close()


def run_error_scenario_tests() -> None:
    """执行3个异常场景，确认返回中文错误信息。"""
    record_id = ensure_base_data()
    db = SessionLocal()
    try:
        scenarios = [
            (
                "押金为负数",
                InpatientRecordUpdate(deposit_amount=-1),
                "押金金额不能为负数",
            ),
            (
                "出院时间早于入院时间",
                InpatientRecordUpdate(discharge_time=datetime.now() - timedelta(days=10)),
                "出院时间不能早于入院时间",
            ),
            (
                "已消费大于押金",
                InpatientRecordUpdate(deposit_amount=100, consumed_amount=200),
                "已消费金额不能大于押金金额",
            ),
        ]

        print("开始执行住院更新异常场景测试...")
        for name, payload, expected in scenarios:
            try:
                update_inpatient_record(db, record_id, payload)
                print(f"❌ {name}: 未抛出预期错误")
            except Exception as exc:
                message = str(getattr(exc, "message", str(exc)))
                ok = expected in message
                flag = "✅" if ok else "❌"
                print(f"{flag} {name}: {message}")
    finally:
        db.close()


if __name__ == "__main__":
    run_error_scenario_tests()

