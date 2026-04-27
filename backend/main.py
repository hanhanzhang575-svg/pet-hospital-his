"""FastAPI应用入口。"""

import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.exceptions import ApiError
from backend.models import init_db
from backend.routers.ai import router as ai_router
from backend.routers.appointments import router as appointments_router
from backend.routers.auth import router as auth_router
from backend.routers.billing import router as billing_router
from backend.routers.cages import router as cages_router
from backend.routers.deposit_monitor import router as deposit_monitor_router
from backend.routers.federated import router as federated_router
from backend.routers.health import router as health_router
from backend.routers.inpatient_records import router as inpatient_records_router
from backend.routers.inventory import router as inventory_router
from backend.routers.lab import router as lab_router
from backend.routers.notifications import router as notifications_router
from backend.routers.nursing import router as nursing_router
from backend.routers.owners import router as owners_router
from backend.routers.pets import router as pets_router
from backend.routers.prescriptions import router as prescriptions_router
from backend.routers.pharmacy import router as pharmacy_router
from backend.routers.rfm import router as rfm_router
from backend.routers.stats import router as stats_router
from backend.routers.tasks import router as tasks_router
from backend.routers.users import router as users_router
from backend.routers.vet_workbench import router as vet_workbench_router
from backend.routers.adoption import router as adoption_router
from backend.routers.news import router as news_router
from backend.routers.data_center import router as data_center_router
from backend.routers.owner_ops import router as owner_ops_router
from backend.routers.vitals import router as vitals_router
from backend.routers.scheduling import router as scheduling_router
from backend.scheduler import start_scheduler, stop_scheduler
from backend.schemas.response import success_response
from backend.services.demo_bootstrap import ensure_demo_foundation
from backend.services.knowledge_graph_service import bootstrap_graph
from backend.services.realtime_hub import get_user_role, hub
from backend.database import SessionLocal, engine
from backend.auth import get_password_hash
from sqlalchemy import text


def _load_env_files() -> None:
    """优先加载 backend/.env，其次加载项目根目录 .env。"""
    backend_dir = Path(__file__).resolve().parent
    project_dir = backend_dir.parent
    env_candidates = [backend_dir / ".env", project_dir / ".env", Path.cwd() / ".env"]
    for env_path in env_candidates:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)


_load_env_files()

app = FastAPI(title="白之助宠物医院信息管理系统", version="0.1.0")
app.include_router(health_router, prefix="/api/v1")
app.include_router(ai_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(owners_router, prefix="/api/v1")
app.include_router(pets_router, prefix="/api/v1")
app.include_router(appointments_router, prefix="/api/v1")
app.include_router(vet_workbench_router, prefix="/api/v1")
app.include_router(adoption_router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(data_center_router, prefix="/api/v1")
app.include_router(owner_ops_router, prefix="/api/v1")
app.include_router(cages_router, prefix="/api/v1")
app.include_router(inpatient_records_router, prefix="/api/v1")
app.include_router(deposit_monitor_router, prefix="/api/v1")
app.include_router(prescriptions_router, prefix="/api/v1")
app.include_router(pharmacy_router, prefix="/api/v1")
app.include_router(rfm_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(lab_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(nursing_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(federated_router, prefix="/api/v1")
app.include_router(scheduling_router, prefix="/api/v1")


@app.on_event("startup")
def on_startup() -> None:
    """应用启动时初始化数据库结构。"""
    init_db()
    # 兼容旧库：补齐medical_records.diagnosis字段，避免电子病历500
    with engine.begin() as conn:
        columns = conn.execute(text("PRAGMA table_info(medical_records);")).fetchall()
        names = {str(row[1]) for row in columns}
        if "diagnosis" not in names:
            conn.execute(text("ALTER TABLE medical_records ADD COLUMN diagnosis VARCHAR(100)"))
        if "is_voided" not in names:
            conn.execute(text("ALTER TABLE medical_records ADD COLUMN is_voided BOOLEAN DEFAULT 0 NOT NULL"))
        if "void_reason" not in names:
            conn.execute(text("ALTER TABLE medical_records ADD COLUMN void_reason TEXT"))
        if "voided_at" not in names:
            conn.execute(text("ALTER TABLE medical_records ADD COLUMN voided_at DATETIME"))
        if "kg_evidence_id" not in names:
            conn.execute(text("ALTER TABLE medical_records ADD COLUMN kg_evidence_id VARCHAR(100)"))
        if "treatment_plan" not in names:
            conn.execute(text("ALTER TABLE medical_records ADD COLUMN treatment_plan TEXT"))
        pet_columns = conn.execute(text("PRAGMA table_info(pets);")).fetchall()
        pet_names = {str(row[1]) for row in pet_columns}
        if "color" not in pet_names:
            conn.execute(text("ALTER TABLE pets ADD COLUMN color VARCHAR(100)"))
        if "type_id" not in pet_names:
            conn.execute(text("ALTER TABLE pets ADD COLUMN type_id INTEGER"))
        appointment_columns = conn.execute(text("PRAGMA table_info(appointments);")).fetchall()
        appointment_names = {str(row[1]) for row in appointment_columns}
        if "max_capacity" not in appointment_names:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN max_capacity INTEGER DEFAULT 10 NOT NULL"))
        if "is_leave" not in appointment_names:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN is_leave BOOLEAN DEFAULT 0 NOT NULL"))
        if "schedule_note" not in appointment_names:
            conn.execute(text("ALTER TABLE appointments ADD COLUMN schedule_note VARCHAR(255)"))
        schedule_columns = conn.execute(text("PRAGMA table_info(scheduling_assignments);")).fetchall()
        if not schedule_columns:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS scheduling_assignments (
                        id INTEGER PRIMARY KEY,
                        employee_id INTEGER NOT NULL,
                        role_name VARCHAR(20) NOT NULL,
                        work_date DATE NOT NULL,
                        shift_id VARCHAR(20) NOT NULL,
                        start_at DATETIME NOT NULL,
                        end_at DATETIME NOT NULL,
                        source VARCHAR(20) NOT NULL DEFAULT 'algorithm',
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(employee_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                    """
                )
            )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_schedule_employee_date "
                    "ON scheduling_assignments(employee_id, work_date)"
                )
            )
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_schedule_role_shift_date "
                    "ON scheduling_assignments(role_name, work_date, shift_id)"
                )
            )
        drug_columns = conn.execute(text("PRAGMA table_info(drugs);")).fetchall()
        drug_names = {str(row[1]) for row in drug_columns}
        if "unit_price" not in drug_names:
            conn.execute(text("ALTER TABLE drugs ADD COLUMN unit_price FLOAT DEFAULT 10.0 NOT NULL"))
        role_rows = conn.execute(text("SELECT name FROM roles")).fetchall()
        role_names = {str(r[0]) for r in role_rows}
        if "lab_tech" not in role_names:
            conn.execute(text("INSERT INTO roles (name, description, created_at) VALUES ('lab_tech', '医技人员', CURRENT_TIMESTAMP)"))
        lab_tech_role_id = conn.execute(text("SELECT id FROM roles WHERE name = 'lab_tech' LIMIT 1")).scalar()
        if lab_tech_role_id is not None:
            existing_lab_users = conn.execute(
                text("SELECT COUNT(1) FROM users WHERE role_id = :role_id"),
                {"role_id": int(lab_tech_role_id)},
            ).scalar()
            if int(existing_lab_users or 0) == 0:
                conn.execute(
                    text(
                        """
                        INSERT INTO users (
                            employee_code, username, password_hash, full_name,
                            role_id, branch_code, is_active, is_licensed_vet, created_at
                        ) VALUES (
                            :employee_code, :username, :password_hash, :full_name,
                            :role_id, :branch_code, 1, 0, CURRENT_TIMESTAMP
                        )
                        """
                    ),
                    {
                        "employee_code": "L0001",
                        "username": "labtech1",
                        "password_hash": get_password_hash("lab123"),
                        "full_name": "检验员小刘",
                        "role_id": int(lab_tech_role_id),
                        "branch_code": "C001",
                    },
                )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY,
                    pet_id INTEGER NOT NULL,
                    visit_date DATE,
                    description VARCHAR(255),
                    kg_evidence_id VARCHAR(100),
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS vets (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    license_no VARCHAR(40) NOT NULL UNIQUE,
                    specialty VARCHAR(60),
                    years_of_experience INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS adoption_pets (
                    id INTEGER PRIMARY KEY,
                    pet_id INTEGER NOT NULL UNIQUE,
                    species VARCHAR(20) NOT NULL,
                    breed VARCHAR(60),
                    is_dangerous_dog BOOLEAN NOT NULL DEFAULT 0,
                    energy_level FLOAT NOT NULL DEFAULT 5.0,
                    sociability FLOAT NOT NULL DEFAULT 5.0,
                    trainability FLOAT NOT NULL DEFAULT 5.0,
                    care_need FLOAT NOT NULL DEFAULT 5.0,
                    noise_level FLOAT NOT NULL DEFAULT 5.0,
                    space_need FLOAT NOT NULL DEFAULT 5.0,
                    medical_need FLOAT NOT NULL DEFAULT 5.0,
                    aggression_level FLOAT NOT NULL DEFAULT 3.0,
                    required_companion_hours FLOAT NOT NULL DEFAULT 4.0,
                    latitude FLOAT,
                    longitude FLOAT,
                    status VARCHAR(20) NOT NULL DEFAULT '待领养',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(pet_id) REFERENCES pets(id) ON DELETE CASCADE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS adopters (
                    id INTEGER PRIMARY KEY,
                    owner_id INTEGER,
                    name VARCHAR(100) NOT NULL,
                    experience_level VARCHAR(20) NOT NULL DEFAULT 'novice',
                    housing_area FLOAT NOT NULL DEFAULT 50.0,
                    budget FLOAT NOT NULL DEFAULT 0.0,
                    available_hours FLOAT NOT NULL DEFAULT 2.0,
                    latitude FLOAT NOT NULL,
                    longitude FLOAT NOT NULL,
                    resident_species JSON NOT NULL DEFAULT '[]',
                    incompatible_species JSON NOT NULL DEFAULT '[]',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(owner_id) REFERENCES owners(id) ON DELETE SET NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS match_results (
                    id INTEGER PRIMARY KEY,
                    adoption_pet_id INTEGER NOT NULL,
                    adopter_id INTEGER NOT NULL,
                    s_dist FLOAT NOT NULL DEFAULT 0.0,
                    s_env FLOAT NOT NULL DEFAULT 0.0,
                    s_med FLOAT NOT NULL DEFAULT 0.0,
                    total_score FLOAT NOT NULL DEFAULT 0.0,
                    hard_blocked BOOLEAN NOT NULL DEFAULT 0,
                    rationale TEXT,
                    details JSON NOT NULL DEFAULT '{}',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(adoption_pet_id) REFERENCES adoption_pets(id) ON DELETE CASCADE,
                    FOREIGN KEY(adopter_id) REFERENCES adopters(id) ON DELETE CASCADE,
                    UNIQUE(adoption_pet_id, adopter_id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS news_posts (
                    id INTEGER PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    summary VARCHAR(500),
                    category VARCHAR(50),
                    source_name VARCHAR(100),
                    source_url VARCHAR(500),
                    cover_image VARCHAR(500),
                    markdown_content TEXT NOT NULL,
                    is_published BOOLEAN NOT NULL DEFAULT 1,
                    created_by INTEGER,
                    published_at DATETIME,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE SET NULL
                )
                """
            )
        )
        news_columns = conn.execute(text("PRAGMA table_info(news_posts);")).fetchall()
        news_names = {str(row[1]) for row in news_columns}
        if "category" not in news_names:
            conn.execute(text("ALTER TABLE news_posts ADD COLUMN category VARCHAR(50)"))
        if "source_name" not in news_names:
            conn.execute(text("ALTER TABLE news_posts ADD COLUMN source_name VARCHAR(100)"))
        if "source_url" not in news_names:
            conn.execute(text("ALTER TABLE news_posts ADD COLUMN source_url VARCHAR(500)"))
        if "published_at" not in news_names:
            conn.execute(text("ALTER TABLE news_posts ADD COLUMN published_at DATETIME"))
        owner_columns = conn.execute(text("PRAGMA table_info(owners);")).fetchall()
        owner_names = {str(row[1]) for row in owner_columns}
        if "latitude" not in owner_names:
            conn.execute(text("ALTER TABLE owners ADD COLUMN latitude FLOAT"))
        if "longitude" not in owner_names:
            conn.execute(text("ALTER TABLE owners ADD COLUMN longitude FLOAT"))
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
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_pet ON match_results(adoption_pet_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_adopter ON match_results(adopter_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_match_results_total_score ON match_results(total_score DESC)"))
        nursing_columns = conn.execute(text("PRAGMA table_info(nursing_logs);")).fetchall()
        nursing_names = {str(row[1]) for row in nursing_columns}
        if "is_voided" not in nursing_names:
            conn.execute(text("ALTER TABLE nursing_logs ADD COLUMN is_voided BOOLEAN DEFAULT 0 NOT NULL"))
        if "void_reason" not in nursing_names:
            conn.execute(text("ALTER TABLE nursing_logs ADD COLUMN void_reason TEXT"))
        if "voided_at" not in nursing_names:
            conn.execute(text("ALTER TABLE nursing_logs ADD COLUMN voided_at DATETIME"))
        if "voided_by_id" not in nursing_names:
            conn.execute(text("ALTER TABLE nursing_logs ADD COLUMN voided_by_id INTEGER"))
        visit_columns = conn.execute(text("PRAGMA table_info(visits);")).fetchall()
        visit_names = {str(row[1]) for row in visit_columns}
        if "kg_evidence_id" not in visit_names:
            conn.execute(text("ALTER TABLE visits ADD COLUMN kg_evidence_id VARCHAR(100)"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id VARCHAR(100) PRIMARY KEY,
                    node_type VARCHAR(50) NOT NULL,
                    data JSON NOT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id VARCHAR(100) PRIMARY KEY,
                    source_id VARCHAR(100) NOT NULL,
                    target_id VARCHAR(100) NOT NULL,
                    relation VARCHAR(100) NOT NULL,
                    confidence FLOAT NOT NULL DEFAULT 1.0,
                    data JSON NOT NULL DEFAULT '{}',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS lab_test_orders (
                    id INTEGER PRIMARY KEY,
                    appointment_id INTEGER,
                    record_code VARCHAR(30),
                    pet_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    clinic_id VARCHAR(10) NOT NULL,
                    test_items JSON NOT NULL DEFAULT '[]',
                    exam_type VARCHAR(30),
                    structured_data JSON NOT NULL DEFAULT '{}',
                    notes TEXT,
                    abnormal_count INTEGER NOT NULL DEFAULT 0,
                    critical_count INTEGER NOT NULL DEFAULT 0,
                    urgency_level VARCHAR(20) NOT NULL DEFAULT '常规',
                    status VARCHAR(20) NOT NULL DEFAULT '待检查',
                    panel_values JSON NOT NULL DEFAULT '{}',
                    image_urls JSON NOT NULL DEFAULT '[]',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at DATETIME
                )
                """
            )
        )
        lab_columns = conn.execute(text("PRAGMA table_info(lab_test_orders);")).fetchall()
        lab_names = {str(row[1]) for row in lab_columns}
        if "appointment_id" not in lab_names:
            conn.execute(text("ALTER TABLE lab_test_orders ADD COLUMN appointment_id INTEGER"))
        if "record_code" not in lab_names:
            conn.execute(text("ALTER TABLE lab_test_orders ADD COLUMN record_code VARCHAR(30)"))
        if "exam_type" not in lab_names:
            conn.execute(text("ALTER TABLE lab_test_orders ADD COLUMN exam_type VARCHAR(30)"))
        if "structured_data" not in lab_names:
            conn.execute(text("ALTER TABLE lab_test_orders ADD COLUMN structured_data JSON NOT NULL DEFAULT '{}'"))
        if "notes" not in lab_names:
            conn.execute(text("ALTER TABLE lab_test_orders ADD COLUMN notes TEXT"))
        if "abnormal_count" not in lab_names:
            conn.execute(text("ALTER TABLE lab_test_orders ADD COLUMN abnormal_count INTEGER NOT NULL DEFAULT 0"))
        if "critical_count" not in lab_names:
            conn.execute(text("ALTER TABLE lab_test_orders ADD COLUMN critical_count INTEGER NOT NULL DEFAULT 0"))
        owner_columns = conn.execute(text("PRAGMA table_info(owners);")).fetchall()
        owner_names = {str(row[1]) for row in owner_columns}
        if "telephone" not in owner_names:
            conn.execute(text("ALTER TABLE owners ADD COLUMN telephone VARCHAR(20)"))
            conn.execute(text("UPDATE owners SET telephone = phone WHERE telephone IS NULL OR telephone = ''"))
        if "birth_date" not in pet_names:
            conn.execute(text("ALTER TABLE pets ADD COLUMN birth_date DATE"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS referral_records (
                    id INTEGER PRIMARY KEY,
                    pet_id INTEGER NOT NULL,
                    from_clinic_id VARCHAR(10) NOT NULL,
                    to_clinic_id VARCHAR(10) NOT NULL,
                    target_cage_id INTEGER,
                    reason TEXT NOT NULL,
                    eta_time DATETIME,
                    status VARCHAR(20) NOT NULL DEFAULT '待接收',
                    created_by INTEGER,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS doctor_support_requests (
                    id INTEGER PRIMARY KEY,
                    from_clinic_id VARCHAR(10) NOT NULL,
                    to_clinic_id VARCHAR(10) NOT NULL,
                    target_doctor_id INTEGER NOT NULL,
                    support_period VARCHAR(100) NOT NULL,
                    reason TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT '待确认',
                    created_by INTEGER,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS operation_audit_logs (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    action VARCHAR(60) NOT NULL,
                    target_type VARCHAR(40) NOT NULL,
                    target_id VARCHAR(40),
                    clinic_id VARCHAR(10),
                    details TEXT,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        followup_columns = conn.execute(text("PRAGMA table_info(followup_tasks);")).fetchall()
        followup_names = {str(row[1]) for row in followup_columns}
        if "followup_detail" not in followup_names:
            conn.execute(text("ALTER TABLE followup_tasks ADD COLUMN followup_detail JSON NOT NULL DEFAULT '{}'"))
    db = SessionLocal()
    try:
        ensure_demo_foundation(db)
        bootstrap_graph(db)
    finally:
        db.close()
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown() -> None:
    """应用关闭时停止后台调度器。"""
    stop_scheduler()


@app.exception_handler(ApiError)
def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
    """统一业务异常响应。"""
    return JSONResponse(
        status_code=exc.code,
        content={"code": exc.code, "message": exc.message, "data": {}},
    )


@app.exception_handler(RequestValidationError)
def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """统一422校验错误响应格式。"""
    details = exc.errors()
    if details:
        first = details[0]
        field = first.get("loc", ["body", "字段"])[-1]
        message = first.get("msg", "参数校验失败")
        final_message = f"{field}：{message}"
    else:
        final_message = "参数校验失败"
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": final_message, "data": {"detail": details}},
    )


@app.get("/api/v1")
def api_root() -> dict[str, object]:
    """API根路径探活接口。"""
    return success_response(data={"service": "shironosuke-backend"})


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:
    """建立按用户隔离的实时通知 WebSocket。"""
    db = SessionLocal()
    try:
        role = get_user_role(db, user_id)
        if role is None:
            await websocket.close(code=1008)
            return
        await hub.connect(user_id=user_id, role=role, websocket=websocket)
        print(f"WebSocket connected: user_id={user_id}")
        await websocket.send_json(
            {
                "type": "notification",
                "role": role,
                "title": "连接成功",
                "content": "实时通知通道已建立",
                "level": "info",
            }
        )
        while True:
            message = await websocket.receive_text()
            if message.strip().lower() == "ping":
                await websocket.send_text("pong")
                continue
            try:
                payload = json.loads(message)
                if (
                    isinstance(payload, dict)
                    and str(payload.get("type", "")).strip().lower() == "ping"
                ):
                    await websocket.send_json({"type": "pong", "ts": payload.get("ts")})
            except json.JSONDecodeError:
                continue
    except WebSocketDisconnect:
        hub.disconnect(user_id)
        print(f"WebSocket disconnected: user_id={user_id}")
    finally:
        db.close()

