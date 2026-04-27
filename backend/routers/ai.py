"""AI模块路由。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.core import Appointment, LabTestOrder, MedicalRecord
from backend.schemas.ai import (
    ActiveListenerRequest,
    AuditLogCreate,
    GraphReasoningRequest,
    GraphVizRequest,
    KgRagRequest,
    KnowledgeEdgeCreate,
    KnowledgeNodeCreate,
    KnowledgeRetrieveRequest,
    MultimodalDiagnosisRequest,
)
from backend.schemas.response import success_response
from backend.services.ai_audit_service import create_audit_log, list_audit_logs
from backend.services.kg_rag import (
    active_correlation_check,
    analyze_passive_request,
    full_diagnosis_pipeline,
    multimodal_diagnosis,
    retrieve_knowledge,
)
from backend.services.knowledge_graph_service import add_edge, add_node, get_graph_viz, run_reasoning
from backend.services.realtime_hub import dispatch_async, hub
from backend.services.rfm_analyzer import analyze_owner_rfm

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/kg-rag")
def kg_rag_analyze(payload: KgRagRequest) -> dict[str, object]:
    """执行KG-RAG被动请求层分析。"""
    result = analyze_passive_request(payload)
    return success_response(data=result.model_dump())


@router.post("/active-listener")
def active_listener(payload: ActiveListenerRequest, db: Session = Depends(get_db)) -> dict[str, object]:
    """执行AI主动监听相关性校验。"""
    record = None
    appointment = None
    pet_id = payload.pet_id

    if payload.medical_record_id is not None:
        record = db.query(MedicalRecord).filter(MedicalRecord.id == payload.medical_record_id).first()
        if record is not None:
            appointment = db.query(Appointment).filter(Appointment.id == record.appointment_id).first()
            pet_id = pet_id or record.pet_id

    if appointment is None and payload.appointment_id is not None:
        appointment = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
        if appointment is not None and pet_id is None:
            pet_id = appointment.pet_id

    if appointment is None:
        return success_response(data={"correlation_score": 0, "warning_triggered": False, "message": "静默等待：未找到接诊单", "graph_conflict_warning": False, "can_submit": False})

    if appointment is None or appointment.status != "就诊中":
        return success_response(data={"correlation_score": 0, "warning_triggered": False, "message": "静默等待：医生尚未开始接诊", "graph_conflict_warning": False, "can_submit": False})

    diagnosis_value = ""
    if record is not None and record.diagnosis:
        diagnosis_value = (record.diagnosis or "").strip()
    if not diagnosis_value:
        diagnosis_value = (payload.diagnosis_text or "").strip()
    if not diagnosis_value:
        return success_response(data={"correlation_score": 0, "warning_triggered": False, "message": "静默等待：确诊结论为空", "graph_conflict_warning": False, "can_submit": False})

    if pet_id is None:
        return success_response(data={"correlation_score": 0, "warning_triggered": False, "message": "静默等待：缺少宠物信息", "graph_conflict_warning": False, "can_submit": False})

    lab_query = db.query(LabTestOrder).filter(LabTestOrder.status == "已完成")
    if appointment is not None:
        lab_query = lab_query.filter(or_(LabTestOrder.appointment_id == appointment.id, LabTestOrder.pet_id == pet_id))
    else:
        lab_query = lab_query.filter(LabTestOrder.pet_id == pet_id)
    lab_row = lab_query.order_by(LabTestOrder.completed_at.desc()).first()
    if lab_row is None:
        return success_response(data={"correlation_score": 0, "warning_triggered": False, "message": "静默等待：检验结果未上传", "graph_conflict_warning": False, "can_submit": False})

    if payload.lab_summary:
        lab_summary = payload.lab_summary
    elif isinstance(lab_row.panel_values, dict) and lab_row.panel_values:
        lab_summary = "，".join([f"{k}:{v}" for k, v in lab_row.panel_values.items()])
    else:
        lab_summary = "检验结果已上传"

    result = active_correlation_check(diagnosis_value, lab_summary, payload.threshold)
    if result.warning_triggered and payload.doctor_id is not None:
        dispatch_async(
            hub.send_to_user(
                payload.doctor_id,
                role="doctor",
                title="AI预警",
                content="检测到诊断结论与生化指标存在冲突，请确认",
                level="error",
            )
        )
    data = result.model_dump()
    data["can_submit"] = True
    data["medical_record_id"] = record.id if record is not None else None
    return success_response(data=data)


@router.post("/knowledge/retrieve")
def knowledge_retrieve(payload: KnowledgeRetrieveRequest) -> dict[str, object]:
    """症状输入实时知识检索。"""
    data = retrieve_knowledge(payload.symptoms_text, top_k=5)
    return success_response(data=data)


@router.post("/multimodal-diagnosis")
def ai_multimodal(payload: MultimodalDiagnosisRequest) -> dict[str, object]:
    """多模态图文联合诊断。"""
    data = multimodal_diagnosis(payload.symptoms_text, payload.image_files, payload.pet_info)
    if isinstance(data, dict):
        data["lab_panel"] = payload.lab_panel or {}
    return success_response(data=data)


@router.post("/full-diagnosis")
def ai_full_diagnosis(payload: MultimodalDiagnosisRequest) -> dict[str, object]:
    """完整流水线诊断：检索+图谱+DeepSeek。"""
    request = KgRagRequest(
        medical_record_id=0,
        symptoms=[payload.symptoms_text],
        lab_summary="",
        doctor_input=payload.symptoms_text,
        pet_info={
            **(payload.pet_info or {}),
            "exam_results": payload.lab_panel or {},
        },
    )
    result = full_diagnosis_pipeline(request, image_files=payload.image_files)
    return success_response(data=result.model_dump())


@router.post("/deepseek-reasoning")
def deepseek_reasoning(payload: MultimodalDiagnosisRequest) -> dict[str, object]:
    """输出DeepSeek结构化推理结果。"""
    request = KgRagRequest(
        medical_record_id=0,
        symptoms=[payload.symptoms_text],
        lab_summary="",
        doctor_input=payload.symptoms_text,
        pet_info={
            **(payload.pet_info or {}),
            "exam_results": payload.lab_panel or {},
        },
    )
    result = full_diagnosis_pipeline(request, image_files=payload.image_files)
    return success_response(data=result.model_dump())


@router.post("/graph/reasoning")
def graph_reasoning(payload: GraphReasoningRequest) -> dict[str, object]:
    """运行图谱多跳推理并返回完整链路。"""
    data = run_reasoning(payload.symptom_list, payload.species, payload.exam_results)
    return success_response(data=data)


@router.post("/graph/viz")
def graph_viz(payload: GraphVizRequest) -> dict[str, object]:
    """获取图谱可视化节点边。"""
    data = get_graph_viz(species=payload.species, path=payload.highlighted_path)
    return success_response(data=data)


@router.post("/graph/node")
def graph_add_node(payload: KnowledgeNodeCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    """动态新增知识节点。"""
    data = add_node(db, node_type=payload.node_type, data=payload.data, node_id=payload.node_id)
    return success_response(data=data)


@router.post("/graph/edge")
def graph_add_edge(payload: KnowledgeEdgeCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    """动态新增知识边。"""
    data = add_edge(
        db,
        source_id=payload.source_id,
        target_id=payload.target_id,
        relation=payload.relation,
        confidence=payload.confidence,
        data=payload.data,
    )
    return success_response(data=data)


@router.post("/audit-log")
def audit_log_create(payload: AuditLogCreate, db: Session = Depends(get_db)) -> dict[str, object]:
    """创建人机决策偏差审计日志。"""
    result = create_audit_log(db, payload)
    if payload.warning_triggered:
        record = db.query(MedicalRecord).filter(MedicalRecord.id == payload.medical_record_id).first()
        doctor_id = payload.doctor_id if record is None else record.vet_id
        dispatch_async(
            hub.send_to_user(
                doctor_id,
                role="doctor",
                title="AI预警",
                content="检测到诊断结论与生化指标存在冲突，请确认",
                level="error",
            )
        )
    return success_response(data={"id": result.id})


@router.get("/audit-log")
def audit_logs(medical_record_id: int | None = None, db: Session = Depends(get_db)) -> dict[str, object]:
    """查询人机决策偏差审计日志。"""
    result = list_audit_logs(db, medical_record_id)
    data = [
        {
            "id": item.id,
            "medical_record_id": item.medical_record_id,
            "doctor_id": item.doctor_id,
            "ai_suggestion": item.ai_suggestion,
            "doctor_decision": item.doctor_decision,
            "deviation_reason": item.deviation_reason,
            "correlation_score": item.correlation_score,
            "warning_triggered": item.warning_triggered,
            "created_at": item.created_at.isoformat(),
        }
        for item in result
    ]
    return success_response(data=data)


@router.get("/rfm-warning")
def rfm_warning(db: Session = Depends(get_db)) -> dict[str, object]:
    """查询RFM客户流失预警结果。"""
    result = analyze_owner_rfm(db)
    return success_response(data=[item.model_dump() for item in result])

