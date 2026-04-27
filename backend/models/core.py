"""核心业务ORM模型定义。"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class Role(Base):
    """系统角色表。"""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class User(Base):
    """系统用户表。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_licensed_vet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Owner(Base):
    """宠物主人档案表。"""

    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    id_card: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    member_level: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Pet(Base):
    """宠物档案表。"""

    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    species: Mapped[str] = mapped_column(String(20), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    color: Mapped[str | None] = mapped_column(String(100), nullable=True)
    type_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    allergy_history: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id", ondelete="CASCADE"), nullable=False)
    clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Appointment(Base):
    """门诊预约挂号表。"""

    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("doctor_id", "scheduled_time", name="uq_appointments_doctor_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    scheduled_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    urgency_level: Mapped[str] = mapped_column(String(20), default="常规", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="待诊", nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_leave: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schedule_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class SchedulingAssignment(Base):
    """医生/护士排班结果表。"""

    __tablename__ = "scheduling_assignments"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_schedule_employee_date"),
        UniqueConstraint("role_name", "work_date", "shift_id", name="uq_schedule_role_shift_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_name: Mapped[str] = mapped_column(String(20), nullable=False)
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    shift_id: Mapped[str] = mapped_column(String(20), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="algorithm", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Visit(Base):
    """就诊记录表（兼容 PetClinic 语义）。"""

    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"), nullable=False)
    visit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kg_evidence_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 图谱关联ID：连接知识图谱推理路径
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MedicalRecord(Base):
    """病历主表。"""

    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False)
    vet_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    exam_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    diagnosis: Mapped[str | None] = mapped_column(String(100), nullable=True)
    treatment_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    kg_evidence_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 图谱关联ID：连接知识图谱推理路径
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Diagnosis(Base):
    """诊断结果表。"""

    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medical_record_id: Mapped[int] = mapped_column(ForeignKey("medical_records.id"), nullable=False)
    diagnosis_code: Mapped[str] = mapped_column(String(20), nullable=False)
    diagnosis_name: Mapped[str] = mapped_column(String(100), nullable=False)
    severity_level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class CageUnit(Base):
    """住院笼舍单元表。"""

    __tablename__ = "cage_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cage_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    zone_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="空闲", nullable=False)
    current_pet_id: Mapped[int | None] = mapped_column(ForeignKey("pets.id", ondelete="SET NULL"), nullable=True)
    adjacent_cage_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class InpatientRecord(Base):
    """住院记录表。"""

    __tablename__ = "inpatient_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"), nullable=False)
    cage_id: Mapped[int] = mapped_column(ForeignKey("cage_units.id", ondelete="RESTRICT"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    admission_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    discharge_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deposit_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    consumed_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="待入院", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class NursingLog(Base):
    """护理日志表。"""

    __tablename__ = "nursing_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inpatient_record_id: Mapped[int] = mapped_column(ForeignKey("inpatient_records.id"), nullable=False)
    nurse_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    is_voided: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    voided_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Drug(Base):
    """药品主数据表。"""

    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dosage_form: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DrugInventory(Base):
    """药品库存表。"""

    __tablename__ = "drug_inventory"
    __table_args__ = (
        UniqueConstraint("drug_id", "branch_code", name="uq_drug_inventory_branch"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(10), nullable=False)
    stock_qty: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    safety_stock: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    frozen_for_prescription: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Prescription(Base):
    """处方主表。"""

    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prescription_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    medical_record_id: Mapped[int] = mapped_column(ForeignKey("medical_records.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="待缴费", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expire_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(hours=2),
        nullable=False,
    )
    locked_inventory: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)


class PrescriptionItem(Base):
    """处方明细表。"""

    __tablename__ = "prescription_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"), nullable=False)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), nullable=False)
    dosage: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)


class Invoice(Base):
    """收费主单表。"""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), nullable=True)
    total_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="unpaid", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class InvoiceItem(Base):
    """收费明细表。"""

    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)


class AiDecisionAuditLog(Base):
    """人机决策偏差审计日志表。"""

    __tablename__ = "ai_decision_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medical_record_id: Mapped[int] = mapped_column(ForeignKey("medical_records.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    ai_suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    doctor_decision: Mapped[str] = mapped_column(Text, nullable=False)
    deviation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    correlation_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    warning_triggered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PurchaseTask(Base):
    """采购任务表。"""

    __tablename__ = "purchase_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    drug_id: Mapped[int] = mapped_column(ForeignKey("drugs.id"), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(10), nullable=False)
    current_stock: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    safety_stock: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    suggested_qty: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="待处理", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class FollowupTask(Base):
    """客户回访任务表。"""

    __tablename__ = "followup_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("owners.id"), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    recency_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monetary: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    script_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="待处理", nullable=False)
    followup_detail: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Vet(Base):
    """执业兽医扩展表（3NF：从 users 拆分专业属性）。"""

    __tablename__ = "vets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    license_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    specialty: Mapped[str | None] = mapped_column(String(60), nullable=True)
    years_of_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class AdoptionPet(Base):
    """待领养宠物特征表（PACI 8维评估）。"""

    __tablename__ = "adoption_pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id", ondelete="CASCADE"), unique=True, nullable=False)
    species: Mapped[str] = mapped_column(String(20), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(60), nullable=True)
    is_dangerous_dog: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    energy_level: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    sociability: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    trainability: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    care_need: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    noise_level: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    space_need: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    medical_need: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    aggression_level: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)  # 1-10
    required_companion_hours: Mapped[float] = mapped_column(Float, default=4.0, nullable=False)
    age_months: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    vaccinated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    neutered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    body_condition_score: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-9
    friendliness_human: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    friendliness_pet: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    shelter_stress: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    adoption_priority: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="待领养", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Adopter(Base):
    """领养人画像表。"""

    __tablename__ = "adopters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("owners.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    experience_level: Mapped[str] = mapped_column(String(20), default="novice", nullable=False)  # novice/intermediate/expert
    housing_area: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    budget: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    available_hours: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    resident_species: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    incompatible_species: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_species: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    preferred_age_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    preferred_age_max: Mapped[int] = mapped_column(Integer, default=180, nullable=False)
    has_children: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_elderly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_allergy_family: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    work_from_home_days: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    activity_level: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    patience_level: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)  # 1-10
    housing_type: Mapped[str] = mapped_column(String(20), default="apartment", nullable=False)
    has_yard: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    credit_score: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)  # 0-100
    historical_adoption_success: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MatchResult(Base):
    """PACI 匹配结果表（存储MCDA三维分值与解释）。"""

    __tablename__ = "match_results"
    __table_args__ = (
        UniqueConstraint("adoption_pet_id", "adopter_id", name="uq_match_result_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    adoption_pet_id: Mapped[int] = mapped_column(ForeignKey("adoption_pets.id", ondelete="CASCADE"), nullable=False)
    adopter_id: Mapped[int] = mapped_column(ForeignKey("adopters.id", ondelete="CASCADE"), nullable=False)
    s_dist: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    s_env: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    s_med: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    s_pref: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    s_behavior: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    s_health_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    s_collab: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hard_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    predicted_speed_days: Mapped[int] = mapped_column(Integer, default=120, nullable=False)
    speed_level: Mapped[str] = mapped_column(String(20), default="slow", nullable=False)
    recommendation_confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), default="hybrid_v2", nullable=False)
    adopted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    feedback_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class NewsPost(Base):
    """医院新闻动态表。"""

    __tablename__ = "news_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    markdown_content: Mapped[str] = mapped_column(Text, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ReferralRecord(Base):
    """跨院区转诊协调记录。"""

    __tablename__ = "referral_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False)
    from_clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    to_clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    target_cage_id: Mapped[int | None] = mapped_column(ForeignKey("cage_units.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    eta_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="待接收", nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class DoctorSupportRequest(Base):
    """跨院区医生支援申请。"""

    __tablename__ = "doctor_support_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    from_clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    to_clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    target_doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    support_period: Mapped[str] = mapped_column(String(100), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="待确认", nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class OperationAuditLog(Base):
    """通用操作审计日志。"""

    __tablename__ = "operation_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    clinic_id: Mapped[str | None] = mapped_column(String(10), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class LabTestOrder(Base):
    """医技检查单与结果表。"""

    __tablename__ = "lab_test_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    appointment_id: Mapped[int | None] = mapped_column(ForeignKey("appointments.id"), nullable=True)
    record_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pet_id: Mapped[int] = mapped_column(ForeignKey("pets.id"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    clinic_id: Mapped[str] = mapped_column(String(10), nullable=False)
    test_items: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    exam_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    structured_data: Mapped[dict[str, object]] = mapped_column(JSON, default=dict, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    abnormal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    critical_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    urgency_level: Mapped[str] = mapped_column(String(20), default="常规", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="待检查", nullable=False)
    panel_values: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class KnowledgeNode(Base):
    """知识图谱节点持久化表。"""

    __tablename__ = "knowledge_nodes"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Symptom/Disease/Drug/Treatment
    data: Mapped[dict | str] = mapped_column(JSON, nullable=False)  # 节点数据（JSON/String）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class KnowledgeEdge(Base):
    """知识图谱边持久化表。"""

    __tablename__ = "knowledge_edges"

    id: Mapped[str] = mapped_column(String(100), primary_key=True, nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[str] = mapped_column(String(100), nullable=False)
    relation: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    data: Mapped[dict | str] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

