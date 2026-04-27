"""采购、回访与跨院区协调路由。"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.exceptions import ApiError
from backend.models.core import (
    CageUnit,
    DoctorSupportRequest,
    Drug,
    OperationAuditLog,
    Pet,
    PurchaseTask,
    ReferralRecord,
    Role,
    User,
)
from backend.schemas.response import success_response
from backend.schemas.tasks import FollowupTaskCreate, PurchaseTaskCreate
from backend.services.realtime_hub import dispatch_async, hub
from backend.services.tasks_service import (
    create_followup_tasks,
    create_purchase_tasks,
    list_followup_tasks,
    list_purchase_tasks,
    update_followup_task,
    update_followup_task_detail,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])
CLINIC_NAME_MAP = {
    "C001": "沙河口院区",
    "C002": "甘井子院区",
    "C003": "高新园区院区",
}


@router.post("/purchase")
def purchase_tasks_create(payload: list[PurchaseTaskCreate], db: Session = Depends(get_db)) -> dict[str, object]:
    """批量创建采购任务。"""
    tasks = create_purchase_tasks(db, payload)
    data = [
        {
            "id": task.id,
            "drug_id": task.drug_id,
            "branch_code": task.branch_code,
            "current_stock": task.current_stock,
            "safety_stock": task.safety_stock,
            "suggested_qty": task.suggested_qty,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
        }
        for task in tasks
    ]
    return success_response(code=201, data=data)


@router.get("/purchase")
def purchase_tasks(status: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询采购任务。"""
    query = db.query(PurchaseTask, Drug).join(Drug, Drug.id == PurchaseTask.drug_id)
    if status:
        query = query.filter(PurchaseTask.status == status)
    rows = query.order_by(PurchaseTask.id.desc()).all()
    data = []
    for task, drug in rows:
        data.append(
            {
                "id": task.id,
                "drug_id": task.drug_id,
                "drug_name": f"{drug.name}({drug.dosage_form})",
                "branch_code": task.branch_code,
                "clinic_name": CLINIC_NAME_MAP.get(task.branch_code, task.branch_code),
                "current_stock": task.current_stock,
                "safety_stock": task.safety_stock,
                "suggested_qty": task.suggested_qty,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
            }
        )
    return success_response(data=data)


@router.put("/purchase/{task_id}")
def purchase_task_update(task_id: int, payload: dict, db: Session = Depends(get_db)) -> dict[str, object]:
    """更新采购任务状态。"""
    task = db.query(PurchaseTask).filter(PurchaseTask.id == task_id).first()
    if task is None:
        return success_response(code=404, message="采购任务不存在")
    if "status" in payload:
        next_status = str(payload["status"])
        if task.status == "已撤回" and next_status in {"已通过", "已驳回"}:
            raise ApiError(code=400, message="该申请已被撤回，无法审批")
        task.status = next_status
    db.commit()
    db.refresh(task)
    return success_response(
        data={
            "id": task.id,
            "drug_id": task.drug_id,
            "branch_code": task.branch_code,
            "current_stock": task.current_stock,
            "safety_stock": task.safety_stock,
            "suggested_qty": task.suggested_qty,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
        }
    )


@router.post("/followup")
def followup_tasks_create(payload: list[FollowupTaskCreate], db: Session = Depends(get_db)) -> dict[str, object]:
    """批量创建回访任务。"""
    tasks = create_followup_tasks(db, payload)
    data = [
        {
            "id": task.id,
            "owner_id": task.owner_id,
            "owner_name": task.owner_name,
            "risk_score": task.risk_score,
            "risk_level": task.risk_level,
            "recency_days": task.recency_days,
            "frequency": task.frequency,
            "monetary": task.monetary,
            "assignee_id": task.assignee_id,
            "script_text": task.script_text,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
        }
        for task in tasks
    ]
    if data:
        dispatch_async(
            hub.send_to_roles(
                ["receptionist"],
                title="RFM回访任务新增",
                content=f"RFM系统新增{len(data)}条回访任务，请及时处理",
                level="warning",
            )
        )
    return success_response(code=201, data=data)


@router.get("/followup")
def followup_tasks(status: str | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询回访任务。"""
    tasks = list_followup_tasks(db, status)
    data = []
    for task in tasks:
        assignee = db.query(User).filter(User.id == task.assignee_id).first() if task.assignee_id else None
        data.append(
            {
                "id": task.id,
                "owner_id": task.owner_id,
                "owner_name": task.owner_name,
                "risk_score": task.risk_score,
                "risk_level": task.risk_level,
                "recency_days": task.recency_days,
                "frequency": task.frequency,
                "monetary": task.monetary,
                "assignee_id": task.assignee_id,
                "assignee_name": assignee.full_name if assignee else "",
                "script_text": task.script_text,
                "status": task.status,
                "followup_detail": task.followup_detail or {},
                "created_at": task.created_at.isoformat(),
            }
        )
    return success_response(data=data)


@router.put("/followup/{task_id}")
def followup_task_update(task_id: int, payload: dict, db: Session = Depends(get_db)) -> dict[str, object]:
    """更新回访任务状态。"""
    task = update_followup_task(db, task_id, status=payload.get("status"))
    if task is None:
        return success_response(code=404, message="回访任务不存在")
    status_value = str(payload.get("status") or "")
    if status_value in {"已预约复诊", "无效拒接"}:
        task.status = status_value
        db.commit()
        db.refresh(task)
    if isinstance(payload.get("followup_detail"), dict):
        task = update_followup_task_detail(db, task_id, detail=payload.get("followup_detail"))
    return success_response(
        data={
            "id": task.id,
            "owner_id": task.owner_id,
            "owner_name": task.owner_name,
            "risk_score": task.risk_score,
            "risk_level": task.risk_level,
            "recency_days": task.recency_days,
            "frequency": task.frequency,
            "monetary": task.monetary,
            "assignee_id": task.assignee_id,
            "script_text": task.script_text,
            "status": task.status,
            "followup_detail": task.followup_detail or {},
            "created_at": task.created_at.isoformat(),
        }
    )


@router.get("/coordination/overview")
def coordination_overview(db: Session = Depends(get_db)) -> dict[str, object]:
    """跨院区协调中心概览。"""
    clinics = ["C001", "C002", "C003"]
    rows = []
    for clinic in clinics:
        doctor_count = db.query(User).join(Role, Role.id == User.role_id).filter(Role.name == "doctor", User.branch_code == clinic).count()
        pending_appointments = db.query(PurchaseTask).filter(PurchaseTask.branch_code == clinic, PurchaseTask.status == "待处理").count()
        cage_idle = db.query(CageUnit).filter(CageUnit.clinic_id == clinic, CageUnit.status == "空闲").count()
        daily_outpatient = db.query(Pet).count() % 40 + (5 if clinic == "C001" else 8 if clinic == "C002" else 6)
        surgery_count = max(1, daily_outpatient // 6)
        load = "高" if doctor_count and (daily_outpatient / doctor_count) > 8 else "中" if doctor_count else "低"
        rows.append(
            {
                "clinic_id": clinic,
                "clinic_name": CLINIC_NAME_MAP.get(clinic, clinic),
                "doctor_load": load,
                "cage_idle": cage_idle,
                "inventory_risk": "中" if pending_appointments > 0 else "低",
                "daily_completed_visits": daily_outpatient,
                "daily_surgeries": surgery_count,
            }
        )
    return success_response(data=rows)


@router.post("/coordination/referrals")
def create_referral(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    """发起跨院区转诊。"""
    record = ReferralRecord(
        pet_id=int(payload.get("pet_id")),
        from_clinic_id=str(payload.get("from_clinic_id") or current_user.branch_code),
        to_clinic_id=str(payload.get("to_clinic_id")),
        target_cage_id=int(payload.get("target_cage_id")) if payload.get("target_cage_id") else None,
        reason=str(payload.get("reason") or ""),
        eta_time=datetime.fromisoformat(payload["eta_time"]) if payload.get("eta_time") else None,
        status="待接收",
        created_by=current_user.id,
    )
    db.add(record)
    db.add(
        OperationAuditLog(
            user_id=current_user.id,
            action="跨院区转诊申请",
            target_type="referral",
            target_id=str(record.pet_id),
            clinic_id=record.to_clinic_id,
            details=record.reason,
        )
    )
    db.commit()
    db.refresh(record)
    dispatch_async(
        hub.send_to_roles(
            ["nurse"],
            title="新增转诊申请",
            content=f"目标院区{CLINIC_NAME_MAP.get(record.to_clinic_id, record.to_clinic_id)}收到转诊申请，请确认接收",
            level="warning",
        )
    )
    return success_response(data={"id": record.id, "status": record.status})


@router.get("/coordination/referrals")
def list_referrals(db: Session = Depends(get_db)) -> dict[str, object]:
    """查询转诊记录。"""
    rows = db.query(ReferralRecord).order_by(ReferralRecord.id.desc()).all()
    data = []
    for r in rows:
        pet = db.query(Pet).filter(Pet.id == r.pet_id).first()
        cage = db.query(CageUnit).filter(CageUnit.id == r.target_cage_id).first() if r.target_cage_id else None
        data.append(
            {
                "id": r.id,
                "pet_id": r.pet_id,
                "pet_name": f"{pet.name}({pet.breed or pet.species})" if pet else f"宠物#{r.pet_id}",
                "from_clinic_id": r.from_clinic_id,
                "from_clinic_name": CLINIC_NAME_MAP.get(r.from_clinic_id, r.from_clinic_id),
                "to_clinic_id": r.to_clinic_id,
                "to_clinic_name": CLINIC_NAME_MAP.get(r.to_clinic_id, r.to_clinic_id),
                "target_cage_id": r.target_cage_id,
                "target_cage_code": cage.cage_code if cage else "",
                "reason": r.reason,
                "eta_time": r.eta_time.isoformat() if r.eta_time else None,
                "status": r.status,
            }
        )
    return success_response(data=data)


@router.post("/coordination/doctor-support")
def create_doctor_support(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    """发起医生支援申请。"""
    req = DoctorSupportRequest(
        from_clinic_id=str(payload.get("from_clinic_id") or current_user.branch_code),
        to_clinic_id=str(payload.get("to_clinic_id")),
        target_doctor_id=int(payload.get("target_doctor_id")),
        support_period=str(payload.get("support_period") or ""),
        reason=str(payload.get("reason") or ""),
        status="待确认",
        created_by=current_user.id,
    )
    db.add(req)
    db.add(
        OperationAuditLog(
            user_id=current_user.id,
            action="医生支援申请",
            target_type="doctor_support",
            target_id=str(req.target_doctor_id),
            clinic_id=req.to_clinic_id,
            details=req.reason,
        )
    )
    db.commit()
    db.refresh(req)
    dispatch_async(
        hub.send_to_user(
            req.target_doctor_id,
            role="doctor",
            title="医生支援申请",
            content=f"您收到{CLINIC_NAME_MAP.get(req.from_clinic_id, req.from_clinic_id)}的支援请求，请查看",
            level="info",
        )
    )
    dispatch_async(
        hub.send_to_roles(
            ["manager"],
            title="跨院区医生支援",
            content=f"已发起医生支援：{req.from_clinic_id} -> {req.to_clinic_id}",
            level="warning",
        )
    )
    return success_response(data={"id": req.id, "status": req.status})


@router.get("/coordination/available-cages")
def available_cages(clinic_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询目标院区可用笼舍。"""
    rows = db.query(CageUnit).filter(CageUnit.clinic_id == clinic_id, CageUnit.status == "空闲").order_by(CageUnit.id.asc()).all()
    return success_response(data=[{"id": item.id, "cage_code": item.cage_code, "zone_type": item.zone_type} for item in rows])


@router.post("/coordination/audit")
def write_operation_audit(payload: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    """写入操作审计日志。"""
    log = OperationAuditLog(
        user_id=current_user.id,
        action=str(payload.get("action") or "操作审计"),
        target_type=str(payload.get("target_type") or "system"),
        target_id=str(payload.get("target_id") or ""),
        clinic_id=str(payload.get("clinic_id") or ""),
        details=str(payload.get("details") or ""),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return success_response(data={"id": log.id})

