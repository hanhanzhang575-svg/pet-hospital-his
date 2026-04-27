"""兽医工作台测试数据初始化脚本。"""

from __future__ import annotations

from datetime import datetime, timedelta

from backend.auth import get_password_hash
from backend.database import SessionLocal
from backend.models.core import Appointment, Owner, Pet, Role, User


def init_vet_workbench_data() -> None:
    """初始化兽医工作台演示数据，包含3条不同紧急程度的待诊记录。"""
    db = SessionLocal()
    try:
        # 准备角色
        doctor_role = db.query(Role).filter(Role.name == "doctor").first()
        if doctor_role is None:
            doctor_role = Role(name="doctor", description="执业兽医师")
            db.add(doctor_role)
            db.commit()
            db.refresh(doctor_role)

        # 准备医生
        doctor = db.query(User).filter(User.username == "doctor_demo").first()
        if doctor is None:
            doctor = User(
                employee_code="D010101099",
                username="doctor_demo",
                password_hash=get_password_hash("doc123"),
                full_name="演示医生",
                role_id=doctor_role.id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=True,
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)

        # 清理该医生旧待诊记录，避免重复
        db.query(Appointment).filter(Appointment.doctor_id == doctor.id, Appointment.status == "待诊").delete()
        db.commit()

        # 准备主人和宠物
        owner_specs = [
            ("OWD001", "赵主人", "13800139001"),
            ("OWD002", "钱主人", "13800139002"),
            ("OWD003", "孙主人", "13800139003"),
        ]
        today = datetime.now().date()
        pet_specs = [
            ("C0106250001", "旺旺", "犬", "金毛", "公", today - timedelta(days=365 * 7), ["青霉素"]),
            ("K0106250002", "咪咪", "猫", "英短", "母", today - timedelta(days=365 * 3), []),
            ("C0106250003", "豆豆", "犬", "柯基", "公", today - timedelta(days=365 * 5), ["海鲜"]),
        ]

        owners: list[Owner] = []
        for owner_code, name, phone in owner_specs:
            owner = db.query(Owner).filter(Owner.owner_code == owner_code).first()
            if owner is None:
                owner = Owner(owner_code=owner_code, name=name, phone=phone, member_level="normal")
                db.add(owner)
                db.commit()
                db.refresh(owner)
            owners.append(owner)

        pets: list[Pet] = []
        for idx, (pet_code, name, species, breed, gender, birth_date, allergy_history) in enumerate(pet_specs):
            pet = db.query(Pet).filter(Pet.pet_code == pet_code).first()
            if pet is None:
                pet = Pet(
                    pet_code=pet_code,
                    name=name,
                    species=species,
                    breed=breed,
                    gender=gender,
                    birth_date=birth_date,
                    weight=6.0 + idx,
                    allergy_history=allergy_history,
                    owner_id=owners[idx].id,
                    clinic_id="C001",
                )
                db.add(pet)
                db.commit()
                db.refresh(pet)
            else:
                pet.birth_date = birth_date
            pets.append(pet)
        db.commit()

        # 创建3条不同紧急程度的待诊记录
        now = datetime.now()
        queue_specs = [
            ("常规", 45.0, 30),
            ("优先", 75.0, 45),
            ("急诊", 95.0, 15),
        ]
        for idx, (urgency, score, minute_offset) in enumerate(queue_specs):
            appointment = Appointment(
                record_code=f"{now.strftime('%Y%m%d')}SUA9{idx + 1:02d}",
                pet_id=pets[idx].id,
                doctor_id=doctor.id,
                clinic_id="C001",
                scheduled_time=now + timedelta(minutes=minute_offset),
                urgency_level=urgency,
                status="待诊",
                priority_score=score,
            )
            db.add(appointment)

        db.commit()
        print("✅ 兽医工作台测试数据初始化完成")
        print("医生账号：doctor_demo / doc123")
        print("已创建：3条待诊挂号（常规/优先/急诊）+ 对应主人与宠物档案")
    finally:
        db.close()


if __name__ == "__main__":
    init_vet_workbench_data()

