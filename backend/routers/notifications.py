"""实时通知触发路由（演示联动）。"""

from __future__ import annotations

from fastapi import APIRouter

from backend.schemas.response import success_response
from backend.services.realtime_hub import dispatch_async, hub

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/nursing-abnormal")
def nursing_abnormal(doctor_id: int, pet_name: str, temperature: float) -> dict[str, object]:
    """护理录入异常体征后通知对应医生。"""
    dispatch_async(
        hub.send_to_user(
            doctor_id,
            role="doctor",
            title="体征异常",
            content=f"{pet_name}体温{temperature:.1f}℃超出阈值，请立即查看",
            level="error",
        )
    )
    return success_response(data={"ok": True})


@router.post("/schedule-updated")
def schedule_updated(doctor_id: int, schedule_text: str) -> dict[str, object]:
    """院区主任修改排班后通知受影响医生。"""
    dispatch_async(
        hub.send_to_user(
            doctor_id,
            role="doctor",
            title="排班变动",
            content=f"您{schedule_text}排班已更新",
            level="info",
        )
    )
    return success_response(data={"ok": True})

