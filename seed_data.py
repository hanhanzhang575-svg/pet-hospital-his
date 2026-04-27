"""
模拟数据生成脚本
一键生成完整的示例数据供演示和测试使用
"""
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.models.core import (
    User, Owner, Pet, Appointment, 
    CageUnit, InpatientRecord, Prescription, 
    DrugInventory, AiDecisionAuditLog, Role
)
from passlib.context import CryptContext

# 密码哈希工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """对密码进行哈希加密"""
    return pwd_context.hash(password)

def seed_database():
    """生成所有模拟数据"""
    db = SessionLocal()
    try:
        # 清空现有数据（可选）
        print("正在清空旧数据...")
        db.query(AiDecisionAuditLog).delete()
        db.query(Prescription).delete()
        db.query(InpatientRecord).delete()
        db.query(CageUnit).delete()
        db.query(Appointment).delete()
        db.query(Pet).delete()
        db.query(Owner).delete()
        db.query(User).delete()
        db.query(Clinic).delete()
        db.query(DrugInventory).delete()
        db.commit()
        print("✓ 旧数据已清空\n")

        # 1. 创建院区信息
        print("1️⃣ 创建院区信息...")
        clinics = [
            Clinic(clinic_code="C001", name="沙河口分院", address="大连市沙河口区"),
            Clinic(clinic_code="C002", name="甘井子分院", address="大连市甘井子区"),
            Clinic(clinic_code="C003", name="高新园区分院", address="大连市高新园区"),
        ]
        db.add_all(clinics)
        db.commit()
        print(f"✓ 已创建 {len(clinics)} 个院区\n")

        # 2. 创建员工（兽医、护士、前台等）
        print("2️⃣ 创建员工账户...")
        users = [
            User(
                username="admin",
                password_hash=hash_password("admin123"),
                real_name="王院长",
                role="admin",
                clinic_id=clinics[0].id,
                is_active=True
            ),
            User(
                username="doctor1",
                password_hash=hash_password("doc123"),
                real_name="张医生",
                role="doctor",
                clinic_id=clinics[0].id,
                is_active=True
            ),
            User(
                username="doctor2",
                password_hash=hash_password("doc123"),
                real_name="李医生",
                role="doctor",
                clinic_id=clinics[1].id,
                is_active=True
            ),
            User(
                username="nurse1",
                password_hash=hash_password("nurse123"),
                real_name="陈护士",
                role="nurse",
                clinic_id=clinics[0].id,
                is_active=True
            ),
            User(
                username="receptionist1",
                password_hash=hash_password("rec123"),
                real_name="前台小王",
                role="receptionist",
                clinic_id=clinics[0].id,
                is_active=True
            ),
            User(
                username="pharmacist1",
                password_hash=hash_password("pharm123"),
                real_name="药房李师傅",
                role="pharmacist",
                clinic_id=clinics[0].id,
                is_active=True
            ),
        ]
        db.add_all(users)
        db.commit()
        print(f"✓ 已创建 {len(users)} 个员工账户\n")

        # 4. 创建宠物主人
        print("4️⃣ 创建宠物主人档案...")
        owners = [
            Owner(
                owner_code="O001",
                name="张三",
                phone="13800138001",
                address="沙河口区数码广场",
                member_level="普通会员"
            ),
            Owner(
                owner_code="O002",
                name="李四",
                phone="13800138002",
                address="甘井子区中华路",
                member_level="钻石会员"
            ),
            Owner(
                owner_code="O003",
                name="王五",
                phone="13800138003",
                address="高新园区火炬路",
                member_level="黄金会员"
            ),
            Owner(
                owner_code="O004",
                name="赵六",
                phone="13800138004",
                address="沙河口区五四广场",
                member_level="普通会员"
            ),
        ]
        db.add_all(owners)
        db.commit()
        print(f"✓ 已创建 {len(owners)} 个主人档案\n")

        # 5. 创建宠物档案
        print("5️⃣ 创建宠物档案...")
        pets = [
            Pet(
                pet_code="C002401001",
                name="旺财",
                species="犬",
                breed="金毛",
                gender="公",
                birth_date=(datetime.now().date() - timedelta(days=1460)).isoformat(),  # 4岁
                weight=28.5,
                allergy_history=["青霉素"],
                owner_id=owners[0].id,
                clinic_id="C001"
            ),
            Pet(
                pet_code="K002401002",
                name="小花",
                species="猫",
                breed="英短",
                gender="母",
                birth_date=(datetime.now().date() - timedelta(days=730)).isoformat(),  # 2岁
                weight=4.2,
                allergy_history=["鱼油"],
                owner_id=owners[1].id,
                clinic_id="C002"
            ),
            Pet(
                pet_code="C002401003",
                name="黄黄",
                species="犬",
                breed="泰迪",
                gender="公",
                birth_date=(datetime.now().date() - timedelta(days=365)).isoformat(),  # 1岁
                weight=6.5,
                allergy_history=[],
                owner_id=owners[2].id,
                clinic_id="C003"
            ),
            Pet(
                pet_code="K002401004",
                name="咪咪",
                species="猫",
                breed="波斯猫",
                gender="母",
                birth_date=(datetime.now().date() - timedelta(days=1095)).isoformat(),  # 3岁
                weight=5.8,
                allergy_history=["鸡蛋"],
                owner_id=owners[3].id,
                clinic_id="C001"
            ),
            Pet(
                pet_code="C002401005",
                name="多多",
                species="犬",
                breed="拉布拉多",
                gender="公",
                birth_date=(datetime.now().date() - timedelta(days=1825)).isoformat(),  # 5岁
                weight=32.0,
                allergy_history=["牛奶"],
                owner_id=owners[0].id,
                clinic_id="C001"
            ),
        ]
        db.add_all(pets)
        db.commit()
        print(f"✓ 已创建 {len(pets)} 个宠物档案\n")

        # 6. 创建笼舍单元
        print("6️⃣ 创建笼舍单元...")
        cages = [
            CageUnit(
                cage_code="DOG-A01",
                clinic_id="C001",
                zone_type="犬区",
                status="空闲"
            ),
            CageUnit(
                cage_code="DOG-A02",
                clinic_id="C001",
                zone_type="犬区",
                status="空闲"
            ),
            CageUnit(
                cage_code="CAT-B01",
                clinic_id="C001",
                zone_type="猫区",
                status="空闲"
            ),
            CageUnit(
                cage_code="VIP-V01",
                clinic_id="C001",
                zone_type="VIP",
                status="空闲"
            ),
            CageUnit(
                cage_code="ICU-I01",
                clinic_id="C001",
                zone_type="ICU",
                status="空闲"
            ),
        ]
        db.add_all(cages)
        db.commit()
        print(f"✓ 已创建 {len(cages)} 个笼舍单元\n")

        # 7. 创建预约挂号
        print("7️⃣ 创建预约挂号...")
        now = datetime.now()
        appointments = [
            Appointment(
                record_code="20260408ZYS001",
                pet_id=pets[0].id,
                doctor_id=users[1].id,
                clinic_id="C001",
                scheduled_time=now + timedelta(hours=1),
                urgency_level="常规",
                status="待诊",
                priority_score=50.0
            ),
            Appointment(
                record_code="20260408ZYS002",
                pet_id=pets[1].id,
                doctor_id=users[2].id,
                clinic_id="C002",
                scheduled_time=now + timedelta(hours=2),
                urgency_level="优先",
                status="待诊",
                priority_score=75.0
            ),
            Appointment(
                record_code="20260408ZYS003",
                pet_id=pets[2].id,
                doctor_id=users[1].id,
                clinic_id="C001",
                scheduled_time=now + timedelta(hours=3),
                urgency_level="急诊",
                status="待诊",
                priority_score=95.0
            ),
        ]
        db.add_all(appointments)
        db.commit()
        print(f"✓ 已创建 {len(appointments)} 个预约挂号\n")

        # 8. 创建住院记录
        print("8️⃣ 创建住院记录...")
        inpatient_records = [
            InpatientRecord(
                pet_id=pets[3].id,
                cage_id=cages[2].id,
                doctor_id=users[1].id,
                clinic_id="C001",
                admission_time=now - timedelta(days=2),
                status="住院观察",
                deposit_amount=1000,
                consumed_amount=350
            ),
        ]
        db.add_all(inpatient_records)
        db.commit()
        print(f"✓ 已创建 {len(inpatient_records)} 条住院记录\n")

        # 9. 创建药品库存
        print("9️⃣ 创建药品库存...")
        drugs = [
            DrugInventory(
                drug_code="INAB10001",
                drug_name="阿莫西林注射液",
                specification="500mg/支",
                stock_qty=150,
                safety_stock=50,
                unit_price=28.5,
                manufacturer="辉瑞制药",
                expiry_date=datetime.now().date() + timedelta(days=180),
                clinic_id="C001"
            ),
            DrugInventory(
                drug_code="INAB10002",
                drug_name="头孢曲松钠",
                specification="1g/支",
                stock_qty=80,
                safety_stock=30,
                unit_price=45.0,
                manufacturer="浙江医药",
                expiry_date=datetime.now().date() + timedelta(days=200),
                clinic_id="C001"
            ),
            DrugInventory(
                drug_code="ORAB10003",
                drug_name="阿司匹林",
                specification="100mg/片",
                stock_qty=200,
                safety_stock=50,
                unit_price=2.5,
                manufacturer="拜耳",
                expiry_date=datetime.now().date() + timedelta(days=365),
                clinic_id="C001"
            ),
        ]
        db.add_all(drugs)
        db.commit()
        print(f"✓ 已创建 {len(drugs)} 种药品库存\n")

        # 10. 创建处方
        print("🔟 创建处方...")
        prescriptions = [
            Prescription(
                prescription_code="RX20260408001",
                medical_record_id=None,  # 待关联
                doctor_id=users[1].id,
                clinic_id="C001",
                status="待缴费",
                locked_inventory={"INAB10001": 3},
                created_at=now - timedelta(hours=1)
            ),
        ]
        db.add_all(prescriptions)
        db.commit()
        print(f"✓ 已创建 {len(prescriptions)} 条处方\n")

        # 11. 创建审计日志
        print("1️⃣1️⃣ 创建审计日志...")
        audit_logs = [
            AiDecisionAuditLog(
                clinic_id="C001",
                pet_id=pets[0].id,
                doctor_id=users[1].id,
                ai_diagnosis="可能患有皮肤炎症",
                doctor_diagnosis="确诊为过敏性皮炎",
                is_consistent=False,
                reasoning="患者过敏史中有青霉素，而AI未考虑药物交叉反应",
                created_at=now - timedelta(hours=5)
            ),
        ]
        db.add_all(audit_logs)
        db.commit()
        print(f"✓ 已创建 {len(audit_logs)} 条审计日志\n")

        print("=" * 60)
        print("✅ 所有模拟数据生成成功！")
        print("=" * 60)
        print("\n📊 生成数据统计：")
        print(f"  • 角色：{len(roles)} 个")
        print(f"  • 员工：{len(users)} 个")
        print(f"  • 主人：{len(owners)} 个")
        print(f"  • 宠物：{len(pets)} 个")
        print(f"  • 笼舍：{len(cages)} 个")
        print(f"  • 预约：{len(appointments)} 个")
        print(f"  • 住院：{len(inpatient_records)} 个")
        print(f"  • 药品：{len(drugs)} 种")
        print(f"  • 处方：{len(prescriptions)} 条")
        print(f"  • 审计日志：{len(audit_logs)} 条")
        print("\n💡 推荐使用账户：")
        print("  • 管理员：admin / admin123")
        print("  • 医生1：doctor1 / doc123")
        print("  • 医生2：doctor2 / doc123")
        print("  • 护士：nurse1 / nurse123")
        print("  • 前台：receptionist1 / rec123")
        print("  • 药师：pharmacist1 / pharm123")
        print("\n🌐 现在访问 http://localhost:5173 开始使用吧！")

    except Exception as e:
        print(f"❌ 错误：{e}")
        db.rollback()
        return False
    finally:
        db.close()

    return True

if __name__ == "__main__":
    seed_database()
