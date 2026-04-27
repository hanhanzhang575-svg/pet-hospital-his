from __future__ import annotations

from datetime import datetime, time, timedelta

from sqlalchemy.orm import Session

from backend.models.core import Appointment, Invoice, MedicalRecord, NewsPost, Owner, Pet, Role, User


ROLE_BLUEPRINTS = [
    ("admin", "系统管理员"),
    ("manager", "院区主任"),
    ("doctor", "执业兽医师"),
    ("nurse", "护理人员"),
    ("receptionist", "前台接诊员"),
    ("pharmacist", "药房人员"),
    ("lab_tech", "检验技师"),
]

USER_BLUEPRINTS = [
    {
        "employee_code": "A0001",
        "username": "admin",
        "password": "admin123",
        "full_name": "王院长",
        "role": "admin",
        "branch_code": "C001",
        "is_licensed_vet": False,
    },
    {
        "employee_code": "M020201007",
        "username": "manager1",
        "password": "mgr123",
        "full_name": "周主任",
        "role": "manager",
        "branch_code": "C002",
        "is_licensed_vet": False,
    },
    {
        "employee_code": "D010101002",
        "username": "doctor1",
        "password": "doc123",
        "full_name": "张医生(内科)",
        "role": "doctor",
        "branch_code": "C001",
        "is_licensed_vet": True,
    },
    {
        "employee_code": "D010101009",
        "username": "doctor7",
        "password": "doc123",
        "full_name": "孙医生(外科)",
        "role": "doctor",
        "branch_code": "C001",
        "is_licensed_vet": True,
    },
    {
        "employee_code": "D010201003",
        "username": "doctor2",
        "password": "doc123",
        "full_name": "李医生(外科)",
        "role": "doctor",
        "branch_code": "C002",
        "is_licensed_vet": True,
    },
    {
        "employee_code": "D020201010",
        "username": "doctor3",
        "password": "doc123",
        "full_name": "王医生(皮肤科)",
        "role": "doctor",
        "branch_code": "C002",
        "is_licensed_vet": True,
    },
    {
        "employee_code": "D030301011",
        "username": "doctor5",
        "password": "doc123",
        "full_name": "陈医生(内科)",
        "role": "doctor",
        "branch_code": "C003",
        "is_licensed_vet": True,
    },
    {
        "employee_code": "D030301012",
        "username": "doctor6",
        "password": "doc123",
        "full_name": "刘医生(牙科)",
        "role": "doctor",
        "branch_code": "C003",
        "is_licensed_vet": True,
    },
    {
        "employee_code": "H010101004",
        "username": "nurse1",
        "password": "nurse123",
        "full_name": "陈护士",
        "role": "nurse",
        "branch_code": "C001",
        "is_licensed_vet": False,
    },
    {
        "employee_code": "Q010101005",
        "username": "receptionist1",
        "password": "rec123",
        "full_name": "前台小王",
        "role": "receptionist",
        "branch_code": "C001",
        "is_licensed_vet": False,
    },
    {
        "employee_code": "Y010101006",
        "username": "pharmacist1",
        "password": "pharm123",
        "full_name": "药房李师傅",
        "role": "pharmacist",
        "branch_code": "C001",
        "is_licensed_vet": False,
    },
    {
        "employee_code": "L010101008",
        "username": "labtech1",
        "password": "lab123",
        "full_name": "检验员小刘",
        "role": "lab_tech",
        "branch_code": "C001",
        "is_licensed_vet": False,
    },
]

DOCTOR_SCHEDULES = {
    "doctor1": {"clinic_id": "C001", "department": "内科", "capacity": 12},
    "doctor7": {"clinic_id": "C001", "department": "外科", "capacity": 9},
    "doctor2": {"clinic_id": "C002", "department": "外科", "capacity": 10},
    "doctor3": {"clinic_id": "C002", "department": "皮肤科", "capacity": 8},
    "doctor5": {"clinic_id": "C003", "department": "内科", "capacity": 11},
    "doctor6": {"clinic_id": "C003", "department": "牙科", "capacity": 8},
}

NEWS_BLUEPRINTS = [
    {
        "title": "Quest 猫粮维生素 B1 过低风险提醒",
        "summary": "FDA 于 2026 年 3 月 13 日发布公告，提示部分 Quest Cat Food 产品存在硫胺素含量极低的问题，持续喂食可能引发猫咪神经和消化系统症状。",
        "category": "安全预警",
        "source_name": "FDA",
        "source_url": "https://www.fda.gov/animal-veterinary/outbreaks-and-advisories/fda-advisory-certain-lots-quest-cat-food-pose-serious-health-risks-due-extremely-low-levels-thiamine",
        "published_at": datetime(2026, 3, 13, 9, 0, 0),
        "markdown_content": (
            "## 事件概览\n"
            "美国 FDA 指出，部分 Quest Cat Food 产品检测到维生素 B1（硫胺素）极低或未检出。"
            "猫长期摄入该类产品，可能出现食欲下降、呕吐、步态不稳、抽搐等症状。\n\n"
            "## 对临床和主人有什么意义\n"
            "- 对以单一生骨肉或冻干口粮为主食的猫，需要关注营养完整性。\n"
            "- 出现神经症状时，病史询问中应加入近期主粮品牌与批次。\n"
            "- 登录页保留该资讯，可帮助前台和医生在接诊早期快速联想到营养缺乏风险。\n\n"
            "[查看 FDA 原文](https://www.fda.gov/animal-veterinary/outbreaks-and-advisories/fda-advisory-certain-lots-quest-cat-food-pose-serious-health-risks-due-extremely-low-levels-thiamine)"
        ),
    },
    {
        "title": "Raaw Energy 生食犬粮细菌污染警示",
        "summary": "FDA 在 2026 年 1 月 23 日发布公告，并于 2 月 6 日更新信息，提醒不要喂食受影响批次的 Raaw Energy 犬粮，原因涉及李斯特菌、沙门氏菌和弯曲杆菌风险。",
        "category": "安全预警",
        "source_name": "FDA",
        "source_url": "https://www.fda.gov/animal-veterinary/outbreaks-and-advisories/fda-advisory-do-not-feed-eight-lots-raaw-energy-dog-food-due-contamination-harmful-bacteria",
        "published_at": datetime(2026, 1, 23, 9, 0, 0),
        "markdown_content": (
            "## 事件概览\n"
            "FDA 对 8 个批次的 Raaw Energy 犬粮发布不要喂食的建议，原因是产品被检出李斯特菌、沙门氏菌或弯曲杆菌。\n\n"
            "## 实际价值\n"
            "- 对腹泻、呕吐、精神沉郁类病例，原始饮食史仍是高价值线索。\n"
            "- 医院接诊环节可借此强化“是否喂食生食”的标准问诊项。\n"
            "- 若家中有人免疫力较低，需同时提醒主人注意交叉污染与家居清洁。\n\n"
            "[查看 FDA 原文](https://www.fda.gov/animal-veterinary/outbreaks-and-advisories/fda-advisory-do-not-feed-eight-lots-raaw-energy-dog-food-due-contamination-harmful-bacteria)"
        ),
    },
    {
        "title": "ASPCA 回顾绝育推广对收容与领养的长期影响",
        "summary": "ASPCA 在 2026 年 2 月 18 日发布文章，回顾绝育推广如何缓解猫犬数量失衡，降低收容压力并提升领养机会。",
        "category": "公益领养",
        "source_name": "ASPCA",
        "source_url": "https://www.aspca.org/news/championing-spay-neuter-helped-define-aspca-20th-century-and-beyond",
        "published_at": datetime(2026, 2, 18, 10, 0, 0),
        "markdown_content": (
            "## 为什么这条资讯值得放在系统首页\n"
            "它不是单纯宣传，而是直接关联医院的公益领养、主人教育与绝育门诊。\n\n"
            "## 对业务的启发\n"
            "- 领养匹配模块应把是否绝育、是否需继续跟踪纳入解释维度。\n"
            "- 主人运营可以围绕“绝育后行为管理”“恢复期照护”形成回访脚本。\n"
            "- 医院新闻不必只放院内活动，也可以放行业内真正有参考价值的信息。\n\n"
            "[查看 ASPCA 原文](https://www.aspca.org/news/championing-spay-neuter-helped-define-aspca-20th-century-and-beyond)"
        ),
    },
    {
        "title": "Best Friends 大型领养活动单场完成 200+ 只宠物安置",
        "summary": "Best Friends 于 2025 年 10 月 15 日报道，一场线下联合领养活动成功帮助 200 多只猫犬进入新家庭，说明高质量场景化领养活动对提升转化非常有效。",
        "category": "公益领养",
        "source_name": "Best Friends Animal Society",
        "source_url": "https://bestfriends.org/stories/features/more-200-pets-adopted-new-picture-perfect-venue",
        "published_at": datetime(2025, 10, 15, 10, 0, 0),
        "markdown_content": (
            "## 为什么与本系统相关\n"
            "这类案例说明，领养不是单靠算法排序，还需要活动策划、场景布置和主人教育共同作用。\n\n"
            "## 可以用于系统设计的思路\n"
            "- 领养大厅可同时展示“匹配结果”和“推荐活动/到场引导”。\n"
            "- 运营看板可追踪活动前后匹配转化率、到场率和领养完成率。\n"
            "- 这也是把领养模块保留给前台与院区运营，而不是开放给所有角色的理由。\n\n"
            "[查看 Best Friends 原文](https://bestfriends.org/stories/features/more-200-pets-adopted-new-picture-perfect-venue)"
        ),
    },
]


def ensure_demo_foundation(db: Session) -> None:
    role_ids = _ensure_roles(db)
    user_map = _ensure_users(db, role_ids)
    _ensure_news_posts(db, user_map.get("admin"))
    _ensure_invoice_history(db)
    _ensure_schedule_history(db, user_map)
    _ensure_medical_record_history(db, user_map)


def _ensure_roles(db: Session) -> dict[str, int]:
    role_ids: dict[str, int] = {}
    for name, description in ROLE_BLUEPRINTS:
        row = db.query(Role).filter(Role.name == name).first()
        if row is None:
            row = Role(name=name, description=description)
            db.add(row)
            db.flush()
        else:
            row.description = description
        role_ids[name] = row.id
    db.commit()
    return role_ids


def _ensure_users(db: Session, role_ids: dict[str, int]) -> dict[str, User]:
    result: dict[str, User] = {}
    existing_users = {user.username: user for user in db.query(User).all()}
    fallback_hash = next((user.password_hash for user in existing_users.values() if user.password_hash), "demo_password_hash")
    for blueprint in USER_BLUEPRINTS:
        row = existing_users.get(str(blueprint["username"]))
        if row is None:
            row = User(
                employee_code=str(blueprint["employee_code"]),
                username=str(blueprint["username"]),
                password_hash=fallback_hash,
                full_name=str(blueprint["full_name"]),
                role_id=role_ids[str(blueprint["role"])],
                branch_code=str(blueprint["branch_code"]),
                is_active=True,
                is_licensed_vet=bool(blueprint["is_licensed_vet"]),
            )
            db.add(row)
            db.flush()
        else:
            row.employee_code = str(blueprint["employee_code"])
            row.full_name = str(blueprint["full_name"])
            row.role_id = role_ids[str(blueprint["role"])]
            row.branch_code = str(blueprint["branch_code"])
            row.is_active = True
            row.is_licensed_vet = bool(blueprint["is_licensed_vet"])
        result[str(blueprint["username"])] = row
    db.commit()
    return result


def _ensure_news_posts(db: Session, admin_user: User | None) -> None:
    existing = db.query(NewsPost).count()
    if existing >= len(NEWS_BLUEPRINTS):
        return
    for item in NEWS_BLUEPRINTS:
        row = db.query(NewsPost).filter(NewsPost.title == item["title"]).first()
        if row is None:
            row = NewsPost(
                title=str(item["title"]),
                summary=str(item["summary"]),
                category=str(item["category"]),
                source_name=str(item["source_name"]),
                source_url=str(item["source_url"]),
                cover_image=None,
                markdown_content=str(item["markdown_content"]),
                is_published=True,
                created_by=admin_user.id if admin_user else None,
                published_at=item["published_at"],
            )
            db.add(row)
        else:
            row.summary = str(item["summary"])
            row.category = str(item["category"])
            row.source_name = str(item["source_name"])
            row.source_url = str(item["source_url"])
            row.cover_image = None
            row.markdown_content = str(item["markdown_content"])
            row.is_published = True
            row.published_at = item["published_at"]
    db.commit()


def _ensure_invoice_history(db: Session) -> None:
    if db.query(Invoice).count() >= 90:
        return

    owners = db.query(Owner).order_by(Owner.id.asc()).limit(120).all()
    if not owners:
        return

    now = datetime.now()
    member_weight = {
        "diamond": 1.8,
        "钻石会员": 1.8,
        "gold": 1.45,
        "黄金会员": 1.45,
        "silver": 1.2,
        "白银会员": 1.2,
    }
    created = False

    for owner in owners:
        owned_count = (
            db.query(Pet)
            .filter(Pet.owner_id == owner.id)
            .count()
        )
        target_count = 1 + (owner.id % 4)
        if owned_count >= 2:
            target_count += 1
        existing_count = db.query(Invoice).filter(Invoice.owner_id == owner.id).count()
        if existing_count >= target_count:
            continue

        level = str(owner.member_level or "")
        multiplier = member_weight.get(level, 1.0)
        for idx in range(existing_count, target_count):
            days_ago = 10 + ((owner.id * 37 + idx * 19) % 320)
            created_at = now - timedelta(days=days_ago, hours=(owner.id + idx) % 9)
            visit_type = (owner.id + idx) % 5
            base_amount = [188, 268, 420, 680, 1280][visit_type]
            amount = round((base_amount + owned_count * 46 + (owner.id % 7) * 32) * multiplier, 2)
            invoice_no = f"SIM{owner.id:04d}{days_ago:03d}{idx:02d}"
            exists = db.query(Invoice).filter(Invoice.invoice_no == invoice_no).first()
            if exists is not None:
                continue
            db.add(
                Invoice(
                    invoice_no=invoice_no,
                    owner_id=owner.id,
                    appointment_id=None,
                    total_amount=amount,
                    paid_amount=amount,
                    status="paid",
                    created_at=created_at,
                )
            )
            created = True
    if created:
        db.commit()


def _ensure_schedule_history(db: Session, user_map: dict[str, User]) -> None:
    if db.query(Appointment).filter(Appointment.status == "排班").count() >= 60:
        return

    pets = db.query(Pet).order_by(Pet.id.asc()).limit(240).all()
    placeholder_pet = pets[0] if pets else None
    if placeholder_pet is None:
        return

    existing_codes = {code for (code,) in db.query(Appointment.record_code).all()}
    now = datetime.now()
    current_monday = now.date() - timedelta(days=now.weekday())

    for username, plan in DOCTOR_SCHEDULES.items():
        doctor = user_map.get(username)
        if doctor is None:
            continue

        for day_offset in range(-28, 14):
            current_day = current_monday + timedelta(days=day_offset)
            weekday = current_day.weekday()
            if weekday == 6:
                continue

            period = _preferred_period(doctor.username, weekday)
            if weekday == 5 and doctor.username in {"doctor3", "doctor6"}:
                continue

            slot_time = datetime.combine(current_day, time(8 if period == "morning" else 14, 1))
            if day_offset >= 0:
                schedule_code = f"SCH{current_day:%y%m%d}{doctor.id:03d}{'M' if period == 'morning' else 'A'}"
                if schedule_code not in existing_codes:
                    db.add(
                        Appointment(
                            record_code=schedule_code,
                            pet_id=placeholder_pet.id,
                            doctor_id=doctor.id,
                            clinic_id=str(plan["clinic_id"]),
                            scheduled_time=slot_time,
                            urgency_level="常规",
                            status="排班",
                            priority_score=0.0,
                            max_capacity=int(plan["capacity"]),
                            is_leave=False,
                            schedule_note=f"{plan['department']}门诊",
                        )
                    )
                    existing_codes.add(schedule_code)

            booking_count = _target_booking_count(doctor.id, current_day, period, int(plan["capacity"]), day_offset < 0)
            booking_status = "已完成" if day_offset < 0 else "待诊"
            for idx in range(booking_count):
                pet = pets[(doctor.id * 31 + current_day.toordinal() + idx * 7) % len(pets)]
                booking_time = slot_time.replace(minute=20) + timedelta(minutes=18 * idx)
                booking_code = f"BKG{current_day:%y%m%d}{doctor.id:03d}{idx:02d}{'H' if day_offset < 0 else 'F'}"
                if booking_code in existing_codes:
                    continue
                db.add(
                    Appointment(
                        record_code=booking_code,
                        pet_id=pet.id,
                        doctor_id=doctor.id,
                        clinic_id=str(plan["clinic_id"]),
                        scheduled_time=booking_time,
                        urgency_level="优先" if idx % 4 == 0 else "常规",
                        status=booking_status,
                        priority_score=8.0 if idx % 4 == 0 else 4.0,
                        max_capacity=int(plan["capacity"]),
                        is_leave=False,
                        schedule_note=f"{plan['department']}门诊号源",
                    )
                )
                existing_codes.add(booking_code)
    db.commit()

    # 控制演示数据规模，避免挂号页首次加载过慢
    generated_rows = (
        db.query(Appointment)
        .filter((Appointment.record_code.like("SCH%")) | (Appointment.record_code.like("BKG%")))
        .order_by(Appointment.scheduled_time.desc(), Appointment.id.desc())
        .all()
    )
    keep = 220
    if len(generated_rows) > keep:
        for row in generated_rows[keep:]:
            db.delete(row)
        db.commit()


def _preferred_period(username: str, weekday: int) -> str:
    morning_map = {
        "doctor1": {0, 2, 4, 5},
        "doctor7": {1, 3, 5},
        "doctor2": {0, 3, 5},
        "doctor3": {1, 2, 4},
        "doctor5": {0, 2, 4, 5},
        "doctor6": {1, 3},
    }
    return "morning" if weekday in morning_map.get(username, {0, 2, 4}) else "afternoon"


def _target_booking_count(doctor_id: int, current_day, period: str, capacity: int, historical: bool) -> int:
    weekday = current_day.weekday()
    demand = 3
    if period == "morning":
        demand += 1
    if weekday in (0, 4):
        demand += 2
    if weekday == 5:
        demand = max(2, demand - 1)
    if historical:
        demand += 1
    demand += ((doctor_id + current_day.toordinal()) % 4) - 1
    return max(0, min(capacity, demand))


def _ensure_medical_record_history(db: Session, user_map: dict[str, User]) -> None:
    if db.query(MedicalRecord).count() >= 20:
        return
    doctors = [u for u in user_map.values() if u.role_id and "doctor" in u.username]
    appointments = (
        db.query(Appointment)
        .filter(Appointment.status.in_(["待诊", "就诊中", "已完成"]))
        .order_by(Appointment.scheduled_time.desc())
        .limit(80)
        .all()
    )
    if not appointments:
        return
    existing_codes = {x.record_no for x in db.query(MedicalRecord.record_no).all()}
    existing_appointment_ids = {x.appointment_id for x in db.query(MedicalRecord.appointment_id).all()}
    seed_texts = [
        ("食欲下降，偶有呕吐", "胃肠炎"),
        ("皮肤瘙痒伴脱毛", "过敏性皮炎"),
        ("精神萎靡，发热", "上呼吸道感染"),
        ("间歇咳嗽，夜间明显", "支气管炎"),
        ("步态异常，后肢无力", "关节炎"),
    ]
    created = 0
    for idx, ap in enumerate(appointments):
        if created >= 20:
            break
        if ap.id in existing_appointment_ids:
            continue
        doctor_id = ap.doctor_id or (doctors[idx % len(doctors)].id if doctors else 1)
        chief, diag = seed_texts[idx % len(seed_texts)]
        code = f"MR{datetime.now():%Y%m%d}{idx + 1:04d}"
        while code in existing_codes:
            code = f"MR{datetime.now():%Y%m%d}{idx + 1 + created:04d}"
        row = MedicalRecord(
            record_no=code,
            appointment_id=ap.id,
            pet_id=ap.pet_id,
            vet_id=doctor_id,
            chief_complaint=chief,
            exam_notes="体格检查已完成，生命体征平稳。",
            diagnosis=diag,
            treatment_plan="先行对症支持治疗，72小时复查。",
            is_voided=False,
        )
        db.add(row)
        existing_codes.add(code)
        existing_appointment_ids.add(ap.id)
        created += 1
    if created:
        db.commit()
