"""DeepSeek客户端：图谱约束注入与严格JSON输出。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None


def _resolve_api_key() -> str:
    # 兼容从项目根目录或 backend 目录启动服务的情况
    service_file = Path(__file__).resolve()
    backend_dir = service_file.parents[1]
    project_dir = service_file.parents[2]
    env_candidates = [
        backend_dir / ".env",
        project_dir / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in env_candidates:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
    return os.getenv("DEEPSEEK_API_KEY", "").strip()


@dataclass
class LlmResult:
    raw_text: str
    parsed: dict[str, object]
    parse_failed: bool


@dataclass
class LlmCallResult:
    content: str
    degraded: bool
    error_code: str | None = None
    error_message: str | None = None
    status_code: int | None = None


def _json_spec(include_image: bool) -> dict[str, object]:
    fields = [
        "differential_diagnosis:[{name,confidence,evidence}]",
        "recommended_exams:[string]",
        "medication_plan:[{drug_name,dose,caution}]",
        "forbidden_warnings:[string]",
    ]
    if include_image:
        fields.append("imaging_findings:string")
    return {
        "format": "json-only",
        "must_have": fields,
        "sort_rule": "differential_diagnosis confidence descending",
        "schema": {
            "type": "object",
            "properties": {
                "diagnosis": {"type": "string"},
                "treatment_plan": {"type": "string"},
                "differential_diagnosis": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "string"},
                        },
                        "required": ["name", "confidence", "evidence"],
                    },
                },
                "recommended_exams": {"type": "array", "items": {"type": "string"}},
                "medication_plan": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "dose": {"type": "string"},
                            "caution": {"type": "string"},
                        },
                        "required": ["drug_name", "dose", "caution"],
                    },
                },
                "forbidden_warnings": {"type": "array", "items": {"type": "string"}},
                "imaging_findings": {"type": "string"},
            },
            "required": ["diagnosis", "treatment_plan", "differential_diagnosis", "recommended_exams", "medication_plan", "forbidden_warnings"],
        },
    }


def build_constrained_messages(
    *,
    pet_info: dict[str, object],
    symptoms_text: str,
    chromadb_matches: list[str],
    graph_constraints: dict[str, object],
    include_image: bool,
) -> list[dict[str, object]]:
    candidate_diseases = graph_constraints.get("candidate_diseases", [])
    recommended_drugs = graph_constraints.get("recommended_drugs", [])
    forbidden_drugs = graph_constraints.get("forbidden_drugs", [])

    system_prompt = {
        "role": "system",
        "content": (
            "你是专业兽医临床助手。必须严格遵守知识图谱约束，只允许在候选疾病和允许药物范围内推理。"
            "禁止给出 forbidden_warnings 中药物的推荐。输出只能是JSON对象，禁止输出任何额外文本。"
        ),
    }

    user_payload = {
        "pet_info": pet_info,
        "symptoms": symptoms_text,
        "chromadb_matches": chromadb_matches,
        "graph_constraints": {
            "candidate_diseases": candidate_diseases,
            "recommended_drugs": recommended_drugs,
            "forbidden_drugs": forbidden_drugs,
            "graph_reasoning_path": graph_constraints.get("graph_reasoning_path", []),
            "recommended_treatments": graph_constraints.get("recommended_treatments", []),
        },
        "output_spec": _json_spec(include_image),
    }
    return [system_prompt, {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)}]


def _mock_result(include_image: bool, graph_constraints: dict[str, object]) -> str:
    diseases = graph_constraints.get("candidate_diseases", [])
    drugs = graph_constraints.get("recommended_drugs", [])
    forbidden = graph_constraints.get("forbidden_drugs", [])
    top_disease = diseases[0]["name"] if diseases else "建议完善检查"
    payload: dict[str, object] = {
        "diagnosis": top_disease,
        "treatment_plan": "先行补液与对症支持治疗，48小时复评并结合复查结果调整方案。",
        "differential_diagnosis": [
            {
                "name": top_disease,
                "confidence": 0.74,
                "evidence": "基于症状聚类与图谱多跳路径",
            }
        ],
        "recommended_exams": ["血常规", "生化全套", "影像复查"],
        "medication_plan": [
            {
                "drug_name": (drugs[0] if drugs else "补液支持"),
                "dose": "按体重评估",
                "caution": "48小时复评",
            }
        ],
        "forbidden_warnings": [f"禁用：{x}" for x in forbidden[:5]],
    }
    if include_image:
        payload["imaging_findings"] = "影像存在轻度异常，建议结合体征与复查。"
    return json.dumps(payload, ensure_ascii=False)


def _error_text(
    code: str,
    message: str,
    graph_constraints: dict[str, object],
    include_image: bool,
    status_code: int | None = None,
) -> LlmCallResult:
    return LlmCallResult(
        content=_mock_result(include_image, graph_constraints),
        degraded=True,
        error_code=code,
        error_message=message,
        status_code=status_code,
    )


def call_deepseek_text(messages: list[dict[str, object]], graph_constraints: dict[str, object]) -> LlmCallResult:
    api_key = _resolve_api_key()
    if not api_key:
        return LlmCallResult(
            content=_mock_result(False, graph_constraints),
            degraded=True,
            error_code="api_key_missing",
            error_message="DEEPSEEK_API_KEY 未在 .env 中配置，请检查环境变量",
        )
    if httpx is None:
        return LlmCallResult(
            content=_mock_result(False, graph_constraints),
            degraded=True,
            error_code="http_client_unavailable",
            error_message="httpx 不可用，无法连接 DeepSeek",
        )
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "deepseek-chat", "messages": messages, "temperature": 0.1, "response_format": {"type": "json_object"}},
            )
            if resp.status_code >= 400:
                return LlmCallResult(
                    content=_mock_result(False, graph_constraints),
                    degraded=True,
                    error_code=f"http_{resp.status_code}",
                    error_message=(resp.text or "DeepSeek 请求失败")[:400],
                    status_code=resp.status_code,
                )
            return LlmCallResult(content=str(resp.json()["choices"][0]["message"]["content"]), degraded=False)
    except httpx.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        return LlmCallResult(
            content=_mock_result(False, graph_constraints),
            degraded=True,
            error_code=f"http_{status_code}" if status_code else "http_error",
            error_message=str(exc),
            status_code=status_code,
        )
    except Exception as exc:
        return _error_text("unexpected_error", str(exc), graph_constraints, include_image=False)


def call_deepseek_multimodal(
    messages: list[dict[str, object]],
    image_base64_list: list[str],
    graph_constraints: dict[str, object],
) -> LlmCallResult:
    api_key = _resolve_api_key()
    if not api_key:
        return LlmCallResult(
            content=_mock_result(True, graph_constraints),
            degraded=True,
            error_code="api_key_missing",
            error_message="DEEPSEEK_API_KEY 未在 .env 中配置，请检查环境变量",
        )
    if httpx is None:
        return LlmCallResult(
            content=_mock_result(True, graph_constraints),
            degraded=True,
            error_code="http_client_unavailable",
            error_message="httpx 不可用，无法连接 DeepSeek",
        )
    try:
        multimodal_content = [{"type": "text", "text": str(messages[-1]["content"])}]
        multimodal_content.extend(
            [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}} for img in image_base64_list]
        )
        with httpx.Client(timeout=45) as client:
            resp = client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-vl",
                    "messages": [messages[0], {"role": "user", "content": multimodal_content}],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
            )
            if resp.status_code >= 400:
                return LlmCallResult(
                    content=_mock_result(True, graph_constraints),
                    degraded=True,
                    error_code=f"http_{resp.status_code}",
                    error_message=(resp.text or "DeepSeek 多模态请求失败")[:400],
                    status_code=resp.status_code,
                )
            return LlmCallResult(content=str(resp.json()["choices"][0]["message"]["content"]), degraded=False)
    except httpx.HTTPError as exc:
        status_code = getattr(exc.response, "status_code", None)
        return LlmCallResult(
            content=_mock_result(True, graph_constraints),
            degraded=True,
            error_code=f"http_{status_code}" if status_code else "http_error",
            error_message=str(exc),
            status_code=status_code,
        )
    except Exception as exc:
        return _error_text("unexpected_error", str(exc), graph_constraints, include_image=True)


def parse_llm_json(text: str) -> LlmResult:
    try:
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("not an object")
        return LlmResult(raw_text=text, parsed=payload, parse_failed=False)
    except Exception:
        return LlmResult(raw_text=text, parsed={"raw": text, "parse_failed": True}, parse_failed=True)
