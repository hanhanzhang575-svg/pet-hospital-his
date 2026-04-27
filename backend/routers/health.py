"""系统健康检查路由。"""

from fastapi import APIRouter

from backend.schemas.response import success_response

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check() -> dict[str, object]:
    """返回服务基础健康状态（统一响应格式）。"""
    return success_response(data={"status": "ok"})


