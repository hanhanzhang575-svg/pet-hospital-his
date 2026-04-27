"""
模拟数据生成脚本 - 一键生成完整的示例数据供演示和测试使用
"""
from datetime import datetime, timedelta
from backend.database import Base, SessionLocal
from backend.models.core import (
    User, Owner, Pet, Appointment,
    CageUnit, InpatientRecord, Prescription,
    DrugInventory, AiDecisionAuditLog, Role, Drug,
    MedicalRecord, FollowupTask, Invoice, PrescriptionItem, LabTestOrder
)
from backend.services.queue_priority import calculate_priority_score
from passlib.context import CryptContext

# 密码哈希工具
# 说明：为避免部分 Windows 环境中 bcrypt 后端兼容性问题，优先使用 pbkdf2_sha256。
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    """对密码进行哈希加密"""
    return pwd_context.hash(password)


def _zone_columns(zone_type: str) -> int:
    """返回不同病区在可视化布局中的列数。"""
    if zone_type in {"犬区", "猫区"}:
        return 5
    if zone_type in {"VIP", "ICU"}:
        return 4
    if zone_type in {"隔离", "临时笼"}:
        return 2
    return 4


def _build_zone_cages(clinic_id: str, zone_type: str, prefix: str, count: int) -> list[CageUnit]:
    """批量构建某院区某病区笼位。"""
    return [
        CageUnit(
            cage_code=f"{clinic_id}-{prefix}-{idx:02d}",
            clinic_id=clinic_id,
            zone_type=zone_type,
            status="空闲",
            adjacent_cage_ids=[],
        )
        for idx in range(1, count + 1)
    ]


def _apply_adjacent_ids(units: list[CageUnit], columns: int) -> None:
    """按网格规则为同一病区笼位设置相邻笼位ID。"""
    for index, unit in enumerate(units):
        row = index // columns
        col = index % columns
        adjacent_ids: list[int] = []
        # 左右
        if col > 0:
            adjacent_ids.append(units[index - 1].id)
        if col < columns - 1 and index + 1 < len(units):
            adjacent_ids.append(units[index + 1].id)
        # 上下
        up_index = index - columns
        down_index = index + columns
        if up_index >= 0:
            adjacent_ids.append(units[up_index].id)
        if down_index < len(units):
            adjacent_ids.append(units[down_index].id)
        unit.adjacent_cage_ids = adjacent_ids

def seed_database():
    """生成所有模拟数据"""
    db = SessionLocal()
    try:
        now = datetime.now()
        # 清空现有数据
        print("正在清空旧数据...")
        # 按外键依赖逆序清理，避免 SQLite FOREIGN KEY 约束报错
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        print("✓ 旧数据已清空\n")

        # 1. 创建角色
        print("1️⃣ 创建系统角色...")
        roles = [
            Role(name="admin", description="系统管理员"),
            Role(name="manager", description="院区主任"),
            Role(name="doctor", description="执业兽医师"),
            Role(name="nurse", description="护理人员"),
            Role(name="receptionist", description="前台接诊员"),
            Role(name="pharmacist", description="药房人员"),
            Role(name="lab_tech", description="医技人员"),
        ]
        db.add_all(roles)
        db.commit()
        print(f"✓ 已创建 {len(roles)} 个角色\n")

        # 2. 创建员工
        print("2️⃣ 创建员工账户...")
        users = [
            User(
                employee_code="D010101001",
                username="admin",
                password_hash=hash_password("admin123"),
                full_name="王院长",
                role_id=roles[0].id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=True
            ),
            User(
                employee_code="D010101002",
                username="doctor1",
                password_hash=hash_password("doc123"),
                full_name="张医生",
                role_id=roles[2].id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=True
            ),
            User(
                employee_code="D010201003",
                username="doctor2",
                password_hash=hash_password("doc123"),
                full_name="李医生",
                role_id=roles[2].id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=True
            ),
            User(
                employee_code="D010301009",
                username="doctor3",
                password_hash=hash_password("doc123"),
                full_name="王医生",
                role_id=roles[2].id,
                branch_code="C002",
                is_active=True,
                is_licensed_vet=True
            ),
            User(
                employee_code="H010101004",
                username="nurse1",
                password_hash=hash_password("nurse123"),
                full_name="陈护士",
                role_id=roles[3].id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=False
            ),
            User(
                employee_code="Q010101005",
                username="receptionist1",
                password_hash=hash_password("rec123"),
                full_name="前台小王",
                role_id=roles[4].id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=False
            ),
            User(
                employee_code="Y010101006",
                username="pharmacist1",
                password_hash=hash_password("pharm123"),
                full_name="药房李师傅",
                role_id=roles[5].id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=False
            ),
            User(
                employee_code="M020201007",
                username="manager1",
                password_hash=hash_password("mgr123"),
                full_name="周主任",
                role_id=roles[1].id,
                branch_code="C002",
                is_active=True,
                is_licensed_vet=True
            ),
            User(
                employee_code="L010101008",
                username="labtech1",
                password_hash=hash_password("lab123"),
                full_name="赵技师",
                role_id=roles[6].id,
                branch_code="C001",
                is_active=True,
                is_licensed_vet=False
            ),
        ]
        db.add_all(users)
        db.commit()
        print(f"✓ 已创建 {len(users)} 个员工账户\n")
        user_by_name = {u.full_name: u for u in users}
        doctor_zhang = user_by_name["张医生"]
        doctor_li = user_by_name["李医生"]
        doctor_wang = user_by_name["王医生"]
        doctor_zhao = User(
            employee_code="D020201010",
            username="doctor4",
            password_hash=hash_password("doc123"),
            full_name="赵医生",
            role_id=roles[2].id,
            branch_code="C002",
            is_active=True,
            is_licensed_vet=True
        )
        doctor_chen = User(
            employee_code="D030301011",
            username="doctor5",
            password_hash=hash_password("doc123"),
            full_name="陈医生",
            role_id=roles[2].id,
            branch_code="C003",
            is_active=True,
            is_licensed_vet=True
        )
        doctor_liu = User(
            employee_code="D030301012",
            username="doctor6",
            password_hash=hash_password("doc123"),
            full_name="刘医生",
            role_id=roles[2].id,
            branch_code="C003",
            is_active=True,
            is_licensed_vet=True
        )
        db.add_all([doctor_zhao, doctor_chen, doctor_liu])
        db.commit()
        users.extend([doctor_zhao, doctor_chen, doctor_liu])
        doctor_zhao = db.query(User).filter(User.username == "doctor4").first()
        doctor_chen = db.query(User).filter(User.username == "doctor5").first()
        doctor_liu = db.query(User).filter(User.username == "doctor6").first()

        # 3. 创建宠物主人
        print("3️⃣ 创建宠物主人档案...")
        owners = [
            Owner(
                owner_code="O001",
                name="赵雨桐",
                phone="13800138001",
                address="沙河口区数码广场",
                member_level="普通会员"
            ),
            Owner(
                owner_code="O002",
                name="孙明轩",
                phone="13800138002",
                address="甘井子区中华路",
                member_level="钻石会员"
            ),
            Owner(
                owner_code="O003",
                name="钱知远",
                phone="13800138003",
                address="高新园区火炬路",
                member_level="黄金会员"
            ),
            Owner(
                owner_code="O004",
                name="吴诗涵",
                phone="13800138004",
                address="沙河口区五四广场",
                member_level="普通会员"
            ),
            Owner(
                owner_code="O005",
                name="郑浩然",
                phone="13800138005",
                address="甘井子区泉水",
                member_level="白银会员"
            ),
            Owner(
                owner_code="O006",
                name="冯可心",
                phone="13800138006",
                address="高新园区凌水路",
                member_level="普通会员"
            ),
        ]
        db.add_all(owners)
        db.commit()
        print(f"✓ 已创建 {len(owners)} 个主人档案\n")

        # 4. 创建宠物档案
        print("4️⃣ 创建宠物档案...")
        pets = [
            Pet(
                pet_code="C002401001",
                name="旺财",
                species="犬",
                breed="金毛",
                gender="公",
                birth_date=now.date() - timedelta(days=1460),
                color="金色",
                type_id=1,
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
                birth_date=now.date() - timedelta(days=730),
                color="银灰",
                type_id=2,
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
                birth_date=now.date() - timedelta(days=365),
                color="棕色",
                type_id=1,
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
                birth_date=now.date() - timedelta(days=1095),
                color="白色",
                type_id=2,
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
                birth_date=now.date() - timedelta(days=1825),
                color="奶油色",
                type_id=1,
                weight=32.0,
                allergy_history=["牛奶"],
                owner_id=owners[0].id,
                clinic_id="C001"
            ),
        ]
        db.add_all(pets)
        db.commit()
        print(f"✓ 已创建 {len(pets)} 个宠物档案\n")

        # 5. 创建笼舍单元（按业务容量生成可视化网格）
        print("5️⃣ 创建笼舍单元...")
        # 核心院区 C001：犬25、猫25、VIP10、ICU8、隔离4 + 临时笼2（急诊降级）
        # 其他院区按缩编容量创建，保证演示中每个院区都具备完整病区结构
        zone_plan = {
            "C001": [("犬区", "DOG", 25), ("猫区", "CAT", 25), ("VIP", "VIP", 10), ("ICU", "ICU", 8), ("隔离", "ISO", 4), ("临时笼", "TMP", 2)],
            "C002": [("犬区", "DOG", 12), ("猫区", "CAT", 12), ("VIP", "VIP", 6), ("ICU", "ICU", 4), ("隔离", "ISO", 2), ("临时笼", "TMP", 1)],
            "C003": [("犬区", "DOG", 12), ("猫区", "CAT", 12), ("VIP", "VIP", 6), ("ICU", "ICU", 4), ("隔离", "ISO", 2), ("临时笼", "TMP", 1)],
        }
        cages: list[CageUnit] = []
        for clinic_code, zones in zone_plan.items():
            for zone_type, prefix, count in zones:
                cages.extend(_build_zone_cages(clinic_code, zone_type, prefix, count))
        db.add_all(cages)
        db.flush()

        # 为每个院区-病区设置网格邻接关系（犬猫不跨区，自然避免邻接混养）
        for clinic_code, zones in zone_plan.items():
            for zone_type, _prefix, _count in zones:
                zone_units = [x for x in cages if x.clinic_id == clinic_code and x.zone_type == zone_type]
                _apply_adjacent_ids(zone_units, _zone_columns(zone_type))

        db.commit()
        print(f"✓ 已创建 {len(cages)} 个笼舍单元（含邻接关系）\n")

        # 6. 创建预约挂号（今天上午：急诊/优先/常规）
        print("6️⃣ 创建预约挂号...")
        today_morning_base = now.replace(hour=9, minute=0, second=0, microsecond=0)
        appt_regular_time = today_morning_base + timedelta(minutes=30)
        appt_priority_time = today_morning_base + timedelta(hours=1)
        appt_emergency_time = today_morning_base + timedelta(hours=1, minutes=30)
        # 为答辩演示把“咪咪”替换为“小白(英短猫)”用于住院与挂号联动展示
        pets[3].name = "小白"
        pets[3].breed = "英短"
        db.commit()
        score_regular = calculate_priority_score("常规", 0, 2.0)
        score_priority = calculate_priority_score("优先", 0, 2.0)
        score_emergency = max(calculate_priority_score("急诊", 0, 2.0), score_regular, score_priority) + 1
        appointments = [
            Appointment(
                record_code=f"{now.strftime('%Y%m%d')}SUA001",
                pet_id=pets[0].id,
                doctor_id=doctor_zhang.id,
                clinic_id="C001",
                scheduled_time=appt_regular_time,
                urgency_level="常规",
                status="待诊",
                priority_score=score_regular,
            ),
            Appointment(
                record_code=f"{now.strftime('%Y%m%d')}SUA002",
                pet_id=pets[1].id,
                doctor_id=doctor_wang.id,
                clinic_id="C002",
                scheduled_time=appt_priority_time,
                urgency_level="优先",
                status="待诊",
                priority_score=score_priority,
            ),
            Appointment(
                record_code=f"{now.strftime('%Y%m%d')}SUA003",
                pet_id=pets[3].id,
                doctor_id=doctor_li.id,
                clinic_id="C001",
                scheduled_time=appt_emergency_time,
                urgency_level="急诊",
                status="待诊",
                priority_score=score_emergency,
            ),
        ]
        db.add_all(appointments)
        db.commit()
        print(f"✓ 已创建 {len(appointments)} 个预约挂号\n")

        # 6.1 创建病历（供处方关联）
        medical_records = [
            MedicalRecord(
                record_no=f"MR{now.strftime('%Y%m%d')}001",
                appointment_id=appointments[0].id,
                pet_id=appointments[0].pet_id,
                vet_id=appointments[0].doctor_id,
                chief_complaint="食欲下降",
                exam_notes="一般检查",
                diagnosis="胃肠道应激",
                kg_evidence_id=f"kg-path-{now.strftime('%Y%m%d')}-001",
            ),
            MedicalRecord(
                record_no=f"MR{now.strftime('%Y%m%d')}002",
                appointment_id=appointments[2].id,
                pet_id=appointments[2].pet_id,
                vet_id=appointments[2].doctor_id,
                chief_complaint="急性呕吐",
                exam_notes="需观察补液",
                diagnosis="急性胃炎",
                kg_evidence_id=f"kg-path-{now.strftime('%Y%m%d')}-002",
            ),
        ]
        db.add_all(medical_records)
        db.commit()

        # 6.2 创建医技检查单（今日2条待检查 + 昨日3条已完成，其中1条危急值）
        print("6️⃣+ 创建医技检查单...")
        lab_orders = [
            LabTestOrder(
                appointment_id=appointments[2].id,
                record_code=appointments[2].record_code,
                pet_id=appointments[2].pet_id,
                doctor_id=appointments[2].doctor_id,
                clinic_id=appointments[2].clinic_id,
                test_items=["血常规", "生化全套"],
                exam_type="biochemistry",
                urgency_level="急诊",
                status="待检查",
                structured_data={},
                panel_values={},
                image_urls=[],
                created_at=now - timedelta(hours=2),
            ),
            LabTestOrder(
                appointment_id=appointments[0].id,
                record_code=appointments[0].record_code,
                pet_id=appointments[0].pet_id,
                doctor_id=appointments[0].doctor_id,
                clinic_id=appointments[0].clinic_id,
                test_items=["尿常规"],
                exam_type="urinalysis",
                urgency_level="常规",
                status="待检查",
                structured_data={},
                panel_values={},
                image_urls=[],
                created_at=now - timedelta(hours=1, minutes=20),
            ),
            LabTestOrder(
                appointment_id=None,
                record_code=f"{(now - timedelta(days=1)).strftime('%Y%m%d')}LAB001",
                pet_id=pets[1].id,
                doctor_id=doctor_wang.id,
                clinic_id="C002",
                test_items=["生化全套"],
                exam_type="biochemistry",
                urgency_level="优先",
                status="已完成",
                structured_data={"ALT": 45.0, "AST": 30.0, "BUN": 22.0, "Creatinine": 1.2, "GLU": 110.0, "TP": 70.0},
                panel_values={"ALT": 45.0, "AST": 30.0, "BUN": 22.0, "Creatinine": 1.2, "GLU": 110.0, "TP": 70.0},
                notes="一般生化复查",
                abnormal_count=0,
                critical_count=0,
                image_urls=[],
                created_at=now - timedelta(days=1, hours=5),
                completed_at=now - timedelta(days=1, hours=4, minutes=20),
            ),
            LabTestOrder(
                appointment_id=None,
                record_code=f"{(now - timedelta(days=1)).strftime('%Y%m%d')}LAB002",
                pet_id=pets[0].id,
                doctor_id=doctor_zhang.id,
                clinic_id="C001",
                test_items=["血常规"],
                exam_type="blood_routine",
                urgency_level="常规",
                status="已完成",
                structured_data={"WBC": 8.5, "RBC": 6.1, "HGB": 140.0, "HCT": 42.0, "PLT": 260.0},
                panel_values={"WBC": 8.5, "RBC": 6.1, "HGB": 140.0, "HCT": 42.0, "PLT": 260.0},
                notes="血常规稳定",
                abnormal_count=0,
                critical_count=0,
                image_urls=[],
                created_at=now - timedelta(days=1, hours=3),
                completed_at=now - timedelta(days=1, hours=2, minutes=30),
            ),
            LabTestOrder(
                appointment_id=None,
                record_code=f"{(now - timedelta(days=1)).strftime('%Y%m%d')}LAB003",
                pet_id=pets[3].id,
                doctor_id=doctor_li.id,
                clinic_id="C001",
                test_items=["生化全套", "X光"],
                exam_type="biochemistry",
                urgency_level="急诊",
                status="已完成",
                structured_data={"ALT": 330.0, "AST": 62.0, "BUN": 19.0, "Creatinine": 1.1, "GLU": 98.0, "TP": 68.0},
                panel_values={"ALT": 330.0, "AST": 62.0, "BUN": 19.0, "Creatinine": 1.1, "GLU": 98.0, "TP": 68.0},
                notes="ALT 超上限约3倍，需肝功能持续监测",
                abnormal_count=2,
                critical_count=1,
                image_urls=["demo-xray-cat-001.png"],
                created_at=now - timedelta(days=1, hours=6),
                completed_at=now - timedelta(days=1, hours=5, minutes=10),
            ),
        ]
        db.add_all(lab_orders)
        db.commit()
        print(f"✓ 已创建 {len(lab_orders)} 条医技检查单\n")

        # 7. 创建住院记录（昨天，小白/张医生）
        print("7️⃣ 创建住院记录...")
        # 选定 C001 猫区首个笼位用于住院展示
        c001_cat_cage = next((x for x in cages if x.clinic_id == "C001" and x.zone_type == "猫区"), None)
        if c001_cat_cage is None:
            raise ValueError("未找到 C001 猫区笼位，无法创建住院记录")

        inpatient_records = [
            InpatientRecord(
                pet_id=pets[3].id,
                cage_id=c001_cat_cage.id,
                doctor_id=doctor_zhang.id,
                clinic_id="C001",
                admission_time=now - timedelta(days=1),
                status="住院观察",
                deposit_amount=650,
                consumed_amount=120
            ),
        ]
        db.add_all(inpatient_records)
        c001_cat_cage.status = "住院中"
        c001_cat_cage.current_pet_id = pets[3].id
        db.commit()
        print(f"✓ 已创建 {len(inpatient_records)} 条住院记录\n")

        # 8. 创建药品库存（10种，3种低库存，2种近效期）
        print("8️⃣ 创建药品库存...")
        drugs_data = [
            Drug(drug_code="ORAM10001", name="阿莫西林胶囊", dosage_form="100mg", category="抗生素", unit="粒"),
            Drug(drug_code="ORAM10002", name="头孢氨苄", dosage_form="250mg", category="抗生素", unit="粒"),
            Drug(drug_code="INJP10003", name="复方电解质", dosage_form="500ml", category="补液", unit="袋"),
            Drug(drug_code="ORAL10004", name="益生菌粉", dosage_form="2g", category="肠胃调理", unit="袋"),
            Drug(drug_code="INJP10005", name="布托啡诺", dosage_form="2ml", category="镇痛", unit="支"),
            Drug(drug_code="ORAL10006", name="奥美拉唑", dosage_form="20mg", category="胃黏膜保护", unit="粒"),
            Drug(drug_code="INJP10007", name="昂丹司琼", dosage_form="2ml", category="止吐", unit="支"),
            Drug(drug_code="ORAL10008", name="甲硝唑片", dosage_form="200mg", category="抗感染", unit="片"),
            Drug(drug_code="INJP10009", name="甲泼尼龙", dosage_form="1ml", category="抗炎", unit="支"),
            Drug(drug_code="ORAL10010", name="卡洛芬", dosage_form="50mg", category="镇痛抗炎", unit="片"),
        ]
        db.add_all(drugs_data)
        db.commit()
        price_map = {
            "阿莫西林胶囊": 1.8,
            "头孢氨苄": 2.2,
            "复方电解质": 9.5,
            "益生菌粉": 4.0,
            "布托啡诺": 18.0,
            "奥美拉唑": 1.5,
            "昂丹司琼": 7.5,
            "甲硝唑片": 0.8,
            "甲泼尼龙": 12.0,
            "卡洛芬": 2.8,
        }
        for drug in drugs_data:
            drug.unit_price = float(price_map.get(drug.name, 10.0))
        db.commit()
        inventory_blueprint = [
            # 低于安全阈值（3种，建议采购量应明显不同）
            (drugs_data[0], 12, 20, 120),
            (drugs_data[1], 8, 18, 140),
            (drugs_data[2], 15, 25, 200),
            # 近效期30天内（2种）
            (drugs_data[3], 50, 20, 18),
            (drugs_data[4], 45, 20, 25),
            # 其余正常
            (drugs_data[5], 60, 20, 150),
            (drugs_data[6], 55, 20, 180),
            (drugs_data[7], 80, 30, 210),
            (drugs_data[8], 70, 30, 160),
            (drugs_data[9], 90, 35, 240),
        ]
        drugs = [
            DrugInventory(
                drug_id=drug.id,
                branch_code="C001",
                stock_qty=stock_qty,
                safety_stock=safety_stock,
                frozen_for_prescription=False,
                expiry_date=now + timedelta(days=expire_days),
            )
            for drug, stock_qty, safety_stock, expire_days in inventory_blueprint
        ]
        db.add_all(drugs)
        db.commit()
        print(f"✓ 已创建 {len(drugs_data)} 种药品 + {len(drugs)} 条库存记录\n")

        # 9. 创建处方（待发药/待缴费）
        print("9️⃣ 创建处方...")
        prescriptions = [
            Prescription(
                prescription_code=f"RX{now.strftime('%Y%m%d')}001",
                medical_record_id=medical_records[0].id,
                doctor_id=doctor_zhang.id,
                status="待发药",
                created_at=now - timedelta(minutes=40),
                expire_at=now + timedelta(hours=2),
                locked_inventory={str(drugs_data[0].id): 2.0, str(drugs_data[5].id): 1.0},
            ),
            Prescription(
                prescription_code=f"RX{now.strftime('%Y%m%d')}002",
                medical_record_id=medical_records[1].id,
                doctor_id=doctor_li.id,
                status="待缴费",
                created_at=now - timedelta(minutes=15),
                expire_at=now + timedelta(hours=1),
                locked_inventory={str(drugs_data[2].id): 1.0, str(drugs_data[3].id): 1.0},
            ),
        ]
        db.add_all(prescriptions)
        db.commit()
        print(f"✓ 已创建 {len(prescriptions)} 条处方\n")

        # 9.1 处方明细（用于EOQ近30天动态需求计算）
        print("9️⃣+ 创建处方明细...")
        items = [
            PrescriptionItem(prescription_id=prescriptions[0].id, drug_id=drugs_data[0].id, dosage="bid", frequency="bid", duration_days=5, quantity=4),
            PrescriptionItem(prescription_id=prescriptions[0].id, drug_id=drugs_data[5].id, dosage="qd", frequency="qd", duration_days=7, quantity=2),
            PrescriptionItem(prescription_id=prescriptions[1].id, drug_id=drugs_data[2].id, dosage="iv", frequency="qd", duration_days=2, quantity=1),
            PrescriptionItem(prescription_id=prescriptions[1].id, drug_id=drugs_data[3].id, dosage="po", frequency="bid", duration_days=5, quantity=3),
        ]
        db.add_all(items)
        db.commit()
        print(f"✓ 已创建 {len(items)} 条处方明细\n")

        # 9.2 生成本周和下周排班数据（每位医生每天仅上午或下午）
        print("9️⃣+ 创建两周排班...")
        doctor_users = [doctor_zhang, doctor_li, doctor_wang, doctor_zhao, doctor_chen, doctor_liu]
        week_start = now.date() - timedelta(days=now.weekday())
        created_schedule = 0
        schedule_assignment = {
            doctor_zhang.id: ("C001", "内科"),
            doctor_li.id: ("C001", "外科"),
            doctor_wang.id: ("C002", "皮肤科"),
            doctor_zhao.id: ("C002", "眼科"),
            doctor_chen.id: ("C003", "内科"),
            doctor_liu.id: ("C003", "齿科"),
        }
        for week_offset in (0, 7):
            base = week_start + timedelta(days=week_offset)
            for doctor in doctor_users:
                for day in range(7):
                    date = base + timedelta(days=day)
                    is_morning = ((doctor.id + day + week_offset) % 2 == 0)
                    hour = 8 if is_morning else 14
                    scheduled = datetime.combine(date, datetime.min.time()).replace(hour=hour, minute=1)
                    exists = (
                        db.query(Appointment)
                        .filter(Appointment.doctor_id == doctor.id, Appointment.scheduled_time == scheduled)
                        .first()
                    )
                    if exists:
                        exists.max_capacity = 10
                        exists.is_leave = False
                        exists.schedule_note = f"{schedule_assignment.get(doctor.id, ('', '综合门诊'))[1]}门诊"
                        continue
                    db.add(
                        Appointment(
                            record_code=f"{date.strftime('%Y%m%d')}SCH{doctor.id:03d}",
                            pet_id=pets[0].id,
                            doctor_id=doctor.id,
                            clinic_id=schedule_assignment.get(doctor.id, (doctor.branch_code, "综合门诊"))[0],
                            scheduled_time=scheduled,
                            urgency_level="常规",
                            status="排班",
                            priority_score=0.0,
                            max_capacity=10,
                            is_leave=False,
                            schedule_note=f"{schedule_assignment.get(doctor.id, ('', '综合门诊'))[1]}门诊",
                        )
                    )
                    created_schedule += 1
        db.commit()
        print(f"✓ 已创建 {created_schedule} 条排班数据\n")
        print("9️⃣+ 创建排班预约占位数据...")
        schedule_rows = (
            db.query(Appointment)
            .filter(Appointment.status == "排班")
            .filter(Appointment.scheduled_time >= datetime.combine(week_start, datetime.min.time()))
            .filter(Appointment.scheduled_time < datetime.combine(week_start + timedelta(days=14), datetime.min.time()))
            .order_by(Appointment.scheduled_time.asc())
            .all()
        )
        slot_bookings = [
            (schedule_rows[0], [pets[0], pets[3], pets[4], pets[2], pets[1], pets[0], pets[3], pets[4], pets[2], pets[1]]),
            (schedule_rows[2], [pets[0], pets[2], pets[3], pets[4], pets[1], pets[0], pets[2], pets[3], pets[4]]),
            (schedule_rows[4], [pets[1], pets[3], pets[0], pets[2], pets[4], pets[1]]),
            (schedule_rows[10], [pets[2], pets[3], pets[4], pets[0]]),
            (schedule_rows[16], [pets[4], pets[1], pets[0], pets[2], pets[3], pets[4], pets[1]]),
        ]
        added_booking = 0
        for index, (slot, pet_list) in enumerate(slot_bookings):
            for inner, pet_item in enumerate(pet_list):
                booking_time = slot.scheduled_time + timedelta(minutes=min(200, inner * 25))
                code = f"{slot.scheduled_time.strftime('%Y%m%d')}Q{slot.doctor_id:03d}{index}{inner}"
                exists = db.query(Appointment).filter(Appointment.record_code == code).first()
                if exists:
                    continue
                db.add(
                    Appointment(
                        record_code=code,
                        pet_id=pet_item.id,
                        doctor_id=slot.doctor_id,
                        clinic_id=slot.clinic_id,
                        scheduled_time=booking_time,
                        urgency_level="优先" if inner % 3 == 0 else "常规",
                        status="待诊" if inner % 2 == 0 else "就诊中",
                        priority_score=calculate_priority_score("优先" if inner % 3 == 0 else "常规", 0, 3.0),
                        max_capacity=slot.max_capacity,
                        is_leave=False,
                        schedule_note=f"由{slot.record_code}排班生成",
                    )
                )
                added_booking += 1
        db.commit()
        print(f"✓ 已创建 {added_booking} 条排班预约占位数据\n")

        # 9.1 回访任务（12条待处理）
        print("9️⃣+ 创建回访任务...")
        followup_tasks = []
        for idx in range(12):
            owner = owners[idx % len(owners)]
            followup_tasks.append(
                FollowupTask(
                    owner_id=owner.id,
                    owner_name=owner.name,
                    risk_score=72.0 - idx,
                    risk_level="high" if idx < 4 else ("medium" if idx < 8 else "low"),
                    recency_days=45 + idx * 2,
                    frequency=max(1, 6 - idx // 3),
                    monetary=1200.0 + idx * 180,
                    assignee_id=next((u.id for u in users if u.username == "receptionist1"), 0),
                    script_text="您好，这里是白之助宠物医院，建议为宠物安排近期复诊评估。",
                    status="待处理",
                )
            )
        db.add_all(followup_tasks)
        db.commit()
        print(f"✓ 已创建 {len(followup_tasks)} 条回访任务\n")

        # 9.2 RFM消费历史（3位客户，含1位高流失）
        print("9️⃣+ 创建RFM消费历史...")
        invoices = [
            # 高流失：久未消费、频次低、金额低
            Invoice(
                invoice_no=f"INV{now.strftime('%Y%m%d')}001",
                owner_id=owners[0].id,
                appointment_id=appointments[0].id,
                total_amount=180.0,
                paid_amount=180.0,
                status="paid",
                created_at=now - timedelta(days=320),
            ),
            # 低流失：近期高频高金额
            Invoice(
                invoice_no=f"INV{now.strftime('%Y%m%d')}002",
                owner_id=owners[1].id,
                appointment_id=appointments[1].id,
                total_amount=1680.0,
                paid_amount=1680.0,
                status="paid",
                created_at=now - timedelta(days=8),
            ),
            Invoice(
                invoice_no=f"INV{now.strftime('%Y%m%d')}003",
                owner_id=owners[1].id,
                appointment_id=appointments[1].id,
                total_amount=1320.0,
                paid_amount=1320.0,
                status="paid",
                created_at=now - timedelta(days=26),
            ),
            # 中风险
            Invoice(
                invoice_no=f"INV{now.strftime('%Y%m%d')}004",
                owner_id=owners[2].id,
                appointment_id=appointments[2].id,
                total_amount=560.0,
                paid_amount=560.0,
                status="paid",
                created_at=now - timedelta(days=90),
            ),
            # 其余客户补充近期消费，避免全部被判定为高流失
            Invoice(
                invoice_no=f"INV{now.strftime('%Y%m%d')}005",
                owner_id=owners[3].id,
                appointment_id=appointments[0].id,
                total_amount=460.0,
                paid_amount=460.0,
                status="paid",
                created_at=now - timedelta(days=21),
            ),
            Invoice(
                invoice_no=f"INV{now.strftime('%Y%m%d')}006",
                owner_id=owners[4].id,
                appointment_id=appointments[1].id,
                total_amount=620.0,
                paid_amount=620.0,
                status="paid",
                created_at=now - timedelta(days=14),
            ),
            Invoice(
                invoice_no=f"INV{now.strftime('%Y%m%d')}007",
                owner_id=owners[5].id,
                appointment_id=appointments[2].id,
                total_amount=780.0,
                paid_amount=780.0,
                status="paid",
                created_at=now - timedelta(days=11),
            ),
        ]
        db.add_all(invoices)
        db.commit()
        print(f"✓ 已创建 {len(invoices)} 条RFM消费记录\n")

        # 10. 创建审计日志
        print("🔟 创建审计日志...")
        # 注：审计日志模型要求 medical_record_id，这里跳过
        # audit_logs = [
        #     AiDecisionAuditLog(
        #         medical_record_id=None,
        #         doctor_id=users[1].id,
        #         ai_suggestion="可能患有皮肤炎症",
        #         doctor_decision="确诊为过敏性皮炎",
        #         deviation_reason="患者过敏史中有青霉素，而AI未考虑药物交叉反应",
        #     ),
        # ]
        # db.add_all(audit_logs)
        # db.commit()
        print(f"✓ 已跳过审计日志创建（通过诊疗流程生成）\n")

        # 输出统计信息
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
        print(f"  • 药品：{len(drugs_data)} 种")
        print(f"  • 库存：{len(drugs)} 条")
        print(f"  • 处方：{len(prescriptions)} 条")
        print(f"  • 回访任务：{len(followup_tasks)} 条")
        print(f"  • RFM消费：{len(invoices)} 条")
        print(f"  • 审计日志：跳过（通过诊疗流程生成）")
        print("\n💡 推荐使用账户：")
        print("  • 管理员：admin / admin123")
        print("  • 医生1：doctor1 / doc123")
        print("  • 医生2：doctor2 / doc123")
        print("  • 护士：nurse1 / nurse123")
        print("  • 前台：receptionist1 / rec123")
        print("  • 药师：pharmacist1 / pharm123")
        print("  • 主任演示：manager1 / mgr123（登录后在前端选择院区主任角色）")
        print("  • 医技人员：labtech1 / lab123")
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
