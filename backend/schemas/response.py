"""统一API响应模型。"""

from __future__ import annotations

from typing import Any


def success_response(data: Any = None, message: str = "success", code: int = 200, **extra: Any) -> dict[str, Any]:
    """返回统一成功响应结构。"""
    payload: dict[str, Any] = {"code": code, "message": message, "data": data if data is not None else {}}
    if extra:
        payload.update(extra)
    return payload

