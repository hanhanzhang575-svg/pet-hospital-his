"""KG-RAG诊断引擎模块（三层+多模态）。"""

from __future__ import annotations

import base64
import math

from ai_module.knowledge_graph import validate_with_graph
from ai_module.vector_store import VectorKnowledgeStore, embed_text
from backend.schemas.ai import ActiveListenerResponse, FullDiagnosisResponse, KgRagRequest, KgRagResponse
from backend.services.knowledge_graph_service import get_graph, run_reasoning
from backend.services.llm_client import (
    build_constrained_messages,
    call_deepseek_multimodal,
    call_deepseek_text,
    parse_llm_json,
)


VECTOR_STORE = VectorKnowledgeStore()
GRAPH = get_graph()


def _species_blocked_tokens(species: str) -> set[str]:
    sp = str(species or "").strip()
    if sp == "猫":
        return {"犬", "dog", "canine"}
    if sp == "犬":
        return {"猫", "cat", "feline"}
    return set()


def _filter_species_matches(matches: list[str], species: str) -> list[str]:
    blocked = _species_blocked_tokens(species)
    if not blocked:
        return matches
    filtered: list[str] = []
    for item in matches:
        text = str(item)
        if any(token in text for token in blocked):
            continue
        filtered.append(text)
    return filtered


def _build_degraded_diagnosis(
    warning: str,
    graph_reasoning: dict[str, object],
    llm_error: dict[str, object],
) -> dict[str, object]:
    candidate_diseases = graph_reasoning.get("candidate_diseases", [])
    top_name = ""
    if candidate_diseases and isinstance(candidate_diseases[0], dict):
        top_name = str(candidate_diseases[0].get("name") or "")
    return {
        "mode": "offline_graph_only",
        "warning": warning,
        "error": llm_error,
        "diagnosis": top_name or "建议完善检查后再评估",
        "treatment_plan": "先行对症支持治疗，结合实验室检查结果复评后调整方案。",
        "differential_diagnosis": graph_reasoning.get("candidate_diseases", []),
        "recommended_exams": ["血常规", "生化全套"],
        "medication_plan": [
            {"drug_name": x, "dose": "按体重评估", "caution": "结合临床复核"}
            for x in graph_reasoning.get("recommended_drugs", [])[:5]
        ],
        "forbidden_warnings": [f"禁用：{x}" for x in graph_reasoning.get("forbidden_drugs", [])[:6]],
    }

def _enforce_drug_constraints(structured: dict[str, object], graph_constraints: dict[str, object]) -> dict[str, object]:
    """过滤禁忌药物并补充禁忌提示。"""
    if not isinstance(structured, dict):
        return structured
    forbidden = set(graph_constraints.get("forbidden_drugs", [])) | set(graph_constraints.get("species_forbidden_drugs", []))
    if not forbidden:
        if "diagnosis" not in structured:
            diagnosis_list = structured.get("differential_diagnosis", [])
            if isinstance(diagnosis_list, list) and diagnosis_list and isinstance(diagnosis_list[0], dict):
                structured["diagnosis"] = str(diagnosis_list[0].get("name") or "")
        if "treatment_plan" not in structured:
            med_plan = structured.get("medication_plan", [])
            if isinstance(med_plan, list) and med_plan:
                top = med_plan[0]
                if isinstance(top, dict):
                    structured["treatment_plan"] = str(top.get("caution") or "按医嘱执行并复评")
            else:
                structured["treatment_plan"] = "按医嘱执行并复评"
        return structured
    drug_list = structured.get("medication_plan", []) or structured.get("用药建议", []) or []
    safe_drugs = []
    removed = []
    for item in drug_list:
        drug_name = ""
        if isinstance(item, dict):
            drug_name = str(item.get("drug_name") or item.get("药品名") or "").strip()
        if drug_name and drug_name in forbidden:
            removed.append(drug_name)
        else:
            safe_drugs.append(item)
    if "medication_plan" in structured:
        structured["medication_plan"] = safe_drugs
    else:
        structured["用药建议"] = safe_drugs
    forbidden_list = structured.get("forbidden_warnings", []) or structured.get("禁忌提示", []) or []
    for name in removed:
        forbidden_list.append(f"禁忌药物已过滤：{name}")
    for name in forbidden:
        if all(name not in str(x) for x in forbidden_list):
            forbidden_list.append(f"物种禁忌：{name}")
    if "forbidden_warnings" in structured:
        structured["forbidden_warnings"] = forbidden_list
    else:
        structured["禁忌提示"] = forbidden_list
    # 统一关键字段，便于前端按固定 v-model 一键回填
    if "diagnosis" not in structured:
        diagnosis_list = structured.get("differential_diagnosis", [])
        if isinstance(diagnosis_list, list) and diagnosis_list and isinstance(diagnosis_list[0], dict):
            structured["diagnosis"] = str(diagnosis_list[0].get("name") or "")
    if "treatment_plan" not in structured:
        med_plan = structured.get("medication_plan", [])
        if isinstance(med_plan, list) and med_plan:
            top = med_plan[0]
            if isinstance(top, dict):
                structured["treatment_plan"] = str(top.get("caution") or "按医嘱执行并复评")
        else:
            structured["treatment_plan"] = "按医嘱执行并复评"
    return structured


def retrieve_knowledge(symptoms_text: str, top_k: int = 5) -> list[str]:
    """第一层：向量检索TopK知识。"""
    return [item.text for item in VECTOR_STORE.search(symptoms_text, top_k=top_k)]


def _compose_symptoms_text(payload: KgRagRequest) -> str:
    symptom_text = "，".join(payload.symptoms or [])
    if payload.doctor_input:
        symptom_text = f"{payload.doctor_input}；{symptom_text}".strip("；")
    return symptom_text


def analyze_passive_request(payload: KgRagRequest) -> KgRagResponse:
    """纯文本三层RAG流程。"""
    pet_info = payload.pet_info or {}
    species = str(pet_info.get("species", "犬"))
    symptoms_text = _compose_symptoms_text(payload)
    top_items = _filter_species_matches(retrieve_knowledge(symptoms_text, top_k=6), species)
    legacy_constraints = validate_with_graph(GRAPH, species, top_items)
    reasoning = run_reasoning(payload.symptoms or [symptoms_text], species)
    graph_constraints = {
        "candidate_diseases": reasoning.get("candidate_diseases", []),
        "recommended_drugs": reasoning.get("recommended_drugs", []),
        "forbidden_drugs": reasoning.get("forbidden_drugs", []),
        "graph_reasoning_path": reasoning.get("graph_reasoning_path", []),
        "recommended_treatments": reasoning.get("recommended_treatments", []),
        "species_forbidden_drugs": legacy_constraints.get("species_forbidden_drugs", []),
    }
    messages = build_constrained_messages(
        pet_info=pet_info,
        symptoms_text=symptoms_text,
        chromadb_matches=top_items,
        graph_constraints=graph_constraints,
        include_image=False,
    )
    llm_call = call_deepseek_text(messages, graph_constraints)
    parsed = parse_llm_json(llm_call.content)
    parsed.parsed = _enforce_drug_constraints(parsed.parsed, graph_constraints)
    if llm_call.degraded:
        parsed.parsed["degraded"] = True
        parsed.parsed["error"] = {
            "code": llm_call.error_code,
            "message": llm_call.error_message,
            "status_code": llm_call.status_code,
        }

    diseases = graph_constraints.get("candidate_diseases", [])
    diagnosis = diseases[0].get("name") if diseases and isinstance(diseases[0], dict) else "建议进一步完善检查后再评估"
    confidence = 0.65 + min(0.3, 0.03 * len(top_items))
    if parsed.parse_failed:
        confidence -= 0.1
    return KgRagResponse(
        diagnosis_suggestion=diagnosis,
        evidence_nodes=[d.get("name", "") if isinstance(d, dict) else str(d) for d in diseases[:6]],
        confidence=round(max(0.3, min(0.95, confidence)), 2),
        structured_result=parsed.parsed,
    )


def multimodal_diagnosis(symptoms_text: str, image_files: list[str], pet_info: dict[str, object]) -> dict[str, object]:
    """多模态扩展：有图走视觉模型，无图走纯文本RAG。"""
    if not image_files:
        mock_payload = KgRagRequest(
            medical_record_id=0,
            symptoms=[symptoms_text],
            lab_summary="",
            doctor_input=symptoms_text,
            pet_info=pet_info,
        )
        result = analyze_passive_request(mock_payload)
        return result.structured_result or {"message": "无结构化结果", "warning": "结构化解析失败"}

    species = str(pet_info.get("species", "犬"))
    top_items = _filter_species_matches(retrieve_knowledge(symptoms_text, top_k=6), species)
    reasoning = run_reasoning([symptoms_text], species)
    graph_constraints = {
        "candidate_diseases": reasoning.get("candidate_diseases", []),
        "recommended_drugs": reasoning.get("recommended_drugs", []),
        "forbidden_drugs": reasoning.get("forbidden_drugs", []),
        "graph_reasoning_path": reasoning.get("graph_reasoning_path", []),
        "recommended_treatments": reasoning.get("recommended_treatments", []),
    }
    messages = build_constrained_messages(
        pet_info=pet_info,
        symptoms_text=symptoms_text,
        chromadb_matches=top_items,
        graph_constraints=graph_constraints,
        include_image=True,
    )
    encoded_images: list[str] = []
    for value in image_files:
        if value.startswith("data:image"):
            encoded_images.append(value.split(",", 1)[-1])
        else:
            encoded_images.append(base64.b64encode(value.encode("utf-8")).decode("utf-8"))
    llm_call = call_deepseek_multimodal(messages, encoded_images, graph_constraints)
    parsed = parse_llm_json(llm_call.content)
    parsed.parsed = _enforce_drug_constraints(parsed.parsed, graph_constraints)
    if llm_call.degraded:
        parsed.parsed["degraded"] = True
        parsed.parsed["error"] = {
            "code": llm_call.error_code,
            "message": llm_call.error_message,
            "status_code": llm_call.status_code,
        }
    if image_files and isinstance(parsed.parsed, dict) and "imaging_findings" not in parsed.parsed and "影像发现" not in parsed.parsed:
        parsed.parsed["imaging_findings"] = "影像未见明显骨折线，建议结合触诊复评。"
    return parsed.parsed


def full_diagnosis_pipeline(payload: KgRagRequest, image_files: list[str] | None = None) -> FullDiagnosisResponse:
    """完整诊断流水线：向量检索 -> 图谱推理 -> DeepSeek诊断。"""
    image_files = image_files or []
    pet_info = payload.pet_info or {}
    species = str(pet_info.get("species", "犬"))
    symptoms_text = _compose_symptoms_text(payload)
    exam_results = {k: float(v) for k, v in (pet_info.get("exam_results") or {}).items() if isinstance(v, (int, float))}

    chromadb_matches = _filter_species_matches(retrieve_knowledge(symptoms_text, top_k=8), species)
    graph_reasoning = run_reasoning(payload.symptoms or [symptoms_text], species, exam_results=exam_results)
    graph_reasoning_path = graph_reasoning.get("graph_reasoning_path", [])

    graph_constraints = {
        "candidate_diseases": graph_reasoning.get("candidate_diseases", []),
        "recommended_drugs": graph_reasoning.get("recommended_drugs", []),
        "forbidden_drugs": graph_reasoning.get("forbidden_drugs", []),
        "graph_reasoning_path": graph_reasoning_path,
        "recommended_treatments": graph_reasoning.get("recommended_treatments", []),
    }
    messages = build_constrained_messages(
        pet_info=pet_info,
        symptoms_text=symptoms_text,
        chromadb_matches=chromadb_matches,
        graph_constraints=graph_constraints,
        include_image=bool(image_files),
    )

    if image_files:
        encoded_images: list[str] = []
        for value in image_files:
            if value.startswith("data:image"):
                encoded_images.append(value.split(",", 1)[-1])
            else:
                encoded_images.append(base64.b64encode(value.encode("utf-8")).decode("utf-8"))
        llm_call = call_deepseek_multimodal(messages, encoded_images, graph_constraints)
    else:
        llm_call = call_deepseek_text(messages, graph_constraints)

    parsed = parse_llm_json(llm_call.content)
    llm_diagnosis = _enforce_drug_constraints(parsed.parsed, graph_constraints)
    if llm_call.degraded:
        llm_diagnosis = _build_degraded_diagnosis(
            warning="DeepSeek 调用失败，已降级为离线图谱模式",
            graph_reasoning=graph_reasoning,
            llm_error={
                "code": llm_call.error_code,
                "message": llm_call.error_message,
                "status_code": llm_call.status_code,
            },
        )
    return FullDiagnosisResponse(
        chromadb_matches=chromadb_matches,
        graph_reasoning_path=graph_reasoning_path,
        llm_diagnosis=llm_diagnosis,
        graph_constraints={
            "candidate_diseases": graph_reasoning.get("candidate_diseases", []),
            "recommended_drugs": graph_reasoning.get("recommended_drugs", []),
            "forbidden_drugs": graph_reasoning.get("forbidden_drugs", []),
        },
        degraded=llm_call.degraded,
    )


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def active_correlation_check(diagnosis_text: str, lab_summary: str, threshold: float) -> ActiveListenerResponse:
    """主动监听：embedding余弦相似度 + 图谱路径冲突。"""
    diagnosis_emb = embed_text(diagnosis_text)
    lab_emb = embed_text(lab_summary)
    score = round(_cosine_similarity(diagnosis_emb, lab_emb), 4)
    warning = score < 0.3

    disease_token = diagnosis_text.replace("，", " ").replace(",", " ").split(" ")[0].strip()
    indicator_token = lab_summary.replace("，", " ").replace(",", " ").split(" ")[0].strip()
    graph_conflict = False
    if disease_token and indicator_token:
        try:
            import networkx as nx

            if not nx.has_path(GRAPH.to_undirected(), disease_token, indicator_token):
                graph_conflict = True
        except Exception:
            graph_conflict = True

    warning = warning or graph_conflict or score < threshold
    if graph_conflict:
        message = "图谱未找到确诊结论与异常指标的关联路径，存在潜在冲突"
    elif warning:
        message = "相关性低于阈值，需强制弹出警告"
    else:
        message = "相关性正常"

    return ActiveListenerResponse(
        correlation_score=round(score, 2),
        warning_triggered=warning,
        message=message,
        graph_conflict_warning=graph_conflict,
    )

