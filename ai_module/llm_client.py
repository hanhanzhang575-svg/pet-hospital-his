"""DeepSeek推理客户端（结构化JSON输出 + 多模态支持）。"""

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
    # ai_module 独立运行时也能命中 backend/.env
    module_file = Path(__file__).resolve()
    project_dir = module_file.parents[1]
    backend_dir = project_dir / "backend"
    env_candidates = [
        backend_dir / ".env",
        project_dir / ".env",
        Path.cwd() / ".env",
    ]
    for env_path in env_candidates:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)
    return os.getenv("DEEPSEEK_API_KEY", "").strip()


SYSTEM_PROMPT = (
    "你是一位专业兽医诊断助手，只能基于以下提供的知识图谱上下文进行推理，"
    "不得凭空生成未经验证的医疗建议。"
)


@dataclass
class LlmResult:
    raw_text: str
    parsed: dict[str, object]
    parse_failed: bool


def build_structured_prompt(
    *,
    pet_info: dict[str, object],
    symptoms_text: str,
    retrieval_items: list[str],
    graph_constraints: dict[str, object],
    include_image: bool,
) -> str:
    """拼接三层RAG输入为结构化Prompt。"""
    payload = {
        "系统角色设定": SYSTEM_PROMPT,
        "患宠基本信息": pet_info,
        "本次症状描述": symptoms_text,
        "ChromaDB检索结果Top5": retrieval_items,
        "知识图谱约束": graph_constraints,
        "输出要求": {
            "格式": "JSON",
            "字段": [
                "鉴别诊断列表:[{疾病名,置信度,依据}]",
                "推荐检查项目:[]",
                "用药建议:[{药品名,剂量,注意事项}]",
                "禁忌提示:[]",
                "影像发现(有图片时必须输出)",
            ],
        },
        "是否包含影像": include_image,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _mock_response(pet_info: dict[str, object], include_image: bool) -> str:
    species = str(pet_info.get("species", "犬"))
    forbidden = {
        "猫": ["对乙酰氨基酚", "阿司匹林", "布洛芬"],
        "犬": ["木糖醇", "葡萄提取物"],
        "兔": ["青霉素类抗生素"],
    }.get(species, [])
    data = {
        "鉴别诊断列表": [
            {"疾病名": "急性胃肠炎", "置信度": 0.79, "依据": "呕吐腹泻与脱水体征匹配"},
            {"疾病名": "胰腺炎", "置信度": 0.53, "依据": "腹痛+食欲废绝提示胰腺问题"},
        ],
        "推荐检查项目": ["血常规", "生化全套", "腹部超声"],
        "用药建议": [
            {"药品名": "止吐药", "剂量": "按体重0.1mg/kg", "注意事项": "先纠正脱水再口服"},
            {"药品名": "输液支持", "剂量": "维持液+缺失液补充", "注意事项": "4小时复评电解质"},
        ],
        "禁忌提示": [f"{species}禁用：{'、'.join(forbidden)}"] if forbidden else [],
    }
    if include_image:
        data["影像发现"] = "可见软组织轻度肿胀，未见明显骨折线，建议结合触诊复评。"
    return json.dumps(data, ensure_ascii=False)


def call_deepseek_text(prompt: str) -> str:
    """调用DeepSeek文本模型，失败回退本地mock。"""
    api_key = _resolve_api_key()
    if not api_key:
        return json.dumps(
            {"error_code": "api_key_missing", "error_message": "DEEPSEEK_API_KEY 未配置", "degraded": True},
            ensure_ascii=False,
        )
    if httpx is None:
        return json.dumps(
            {"error_code": "http_client_unavailable", "error_message": "httpx 不可用", "degraded": True},
            ensure_ascii=False,
        )
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        return json.dumps(
            {"error_code": "deepseek_request_failed", "error_message": str(exc), "degraded": True},
            ensure_ascii=False,
        )


def call_deepseek_multimodal(prompt: str, image_base64_list: list[str]) -> str:
    """调用DeepSeek视觉模型，失败回退本地mock。"""
    api_key = _resolve_api_key()
    if not api_key:
        return json.dumps(
            {"error_code": "api_key_missing", "error_message": "DEEPSEEK_API_KEY 未配置", "degraded": True},
            ensure_ascii=False,
        )
    if httpx is None:
        return json.dumps(
            {"error_code": "http_client_unavailable", "error_message": "httpx 不可用", "degraded": True},
            ensure_ascii=False,
        )
    try:
        content = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}} for img in image_base64_list
        ]
        with httpx.Client(timeout=45) as client:
            response = client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek-vl",
                    "messages": [{"role": "user", "content": content}],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        return json.dumps(
            {"error_code": "deepseek_request_failed", "error_message": str(exc), "degraded": True},
            ensure_ascii=False,
        )


def parse_llm_json(text: str) -> LlmResult:
    """严格解析JSON，失败则返回降级结构。"""
    try:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("响应不是JSON对象")
        return LlmResult(raw_text=text, parsed=parsed, parse_failed=False)
    except Exception:
        return LlmResult(
            raw_text=text,
            parsed={"message": text, "warning": "结构化解析失败"},
            parse_failed=True,
        )


