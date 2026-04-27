"""AI模块Schema定义。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class KgRagRequest(BaseModel):
    """KG-RAG被动分析请求体。"""

    medical_record_id: int
    symptoms: list[str]
    lab_summary: str
    doctor_input: str
    pet_info: dict[str, object] | None = None


class KgRagResponse(BaseModel):
    """KG-RAG分析响应体。"""

    diagnosis_suggestion: str
    evidence_nodes: list[str]
    confidence: float
    structured_result: dict[str, object] | None = None


class FullDiagnosisResponse(BaseModel):
    """完整诊断流水线响应。"""

    chromadb_matches: list[str]
    graph_reasoning_path: list[dict[str, object]]
    llm_diagnosis: dict[str, object]
    graph_constraints: dict[str, object]
    degraded: bool = False


class ActiveListenerRequest(BaseModel):
    """主动监听校验请求体。"""

    medical_record_id: int | None = None
    appointment_id: int | None = None
    pet_id: int | None = None
    diagnosis_text: str
    lab_summary: str = ""
    threshold: float = 0.45
    doctor_id: int | None = None


class ActiveListenerResponse(BaseModel):
    """主动监听校验响应体。"""

    correlation_score: float
    warning_triggered: bool
    message: str
    graph_conflict_warning: bool = False


class KnowledgeRetrieveRequest(BaseModel):
    """症状实时检索请求体。"""

    symptoms_text: str
    species: str = "犬"


class MultimodalDiagnosisRequest(BaseModel):
    """图文联合诊断请求体。"""

    symptoms_text: str
    image_files: list[str] = []
    pet_info: dict[str, object] = {}
    lab_panel: dict[str, float] = {}


class GraphReasoningRequest(BaseModel):
    """图谱多跳推理请求。"""

    symptom_list: list[str]
    species: str
    exam_results: dict[str, float] = {}


class GraphVizRequest(BaseModel):
    """图谱可视化请求。"""

    species: str | None = None
    highlighted_path: list[dict[str, object]] = []


class KnowledgeNodeCreate(BaseModel):
    """动态新增图谱节点。"""

    node_type: str
    node_id: str | None = None
    data: dict[str, object]


class KnowledgeEdgeCreate(BaseModel):
    """动态新增图谱边。"""

    source_id: str
    target_id: str
    relation: str
    confidence: float
    data: dict[str, object] = {}


class AuditLogCreate(BaseModel):
    """审计日志创建请求体。"""

    medical_record_id: int
    doctor_id: int
    ai_suggestion: str
    doctor_decision: str
    deviation_reason: str
    correlation_score: float
    warning_triggered: bool


class AuditLogRead(BaseModel):
    """审计日志响应体。"""

    id: int
    medical_record_id: int
    doctor_id: int
    ai_suggestion: str
    doctor_decision: str
    deviation_reason: str
    correlation_score: float
    warning_triggered: bool
    created_at: datetime


class RfmWarningRead(BaseModel):
    """RFM客户流失预警响应体。"""

    owner_id: int
    owner_name: str
    recency_days: int
    frequency: int
    monetary: float
    rfm_score: float
    risk_level: str

