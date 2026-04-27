"""联邦学习状态路由。"""

from __future__ import annotations

from collections import defaultdict

from fastapi import APIRouter

from ai_module.federated.server import FederatedServer
from backend.database import engine
from backend.schemas.response import success_response

router = APIRouter(prefix="/federated", tags=["federated"])
_server = FederatedServer(engine)


def _derive_federated_insights(data: dict[str, object]) -> dict[str, object]:
    logs = list(data.get("training_logs") or [])
    round_loss: dict[int, list[float]] = defaultdict(list)
    round_acc: dict[int, list[float]] = defaultdict(list)
    round_size: dict[int, dict[str, int]] = defaultdict(dict)
    for row in logs:
        rid = int(row.get("round_id") or 0)
        cid = str(row.get("clinic_id") or "")
        round_loss[rid].append(float(row.get("global_loss") or 0.0))
        round_acc[rid].append(float(row.get("global_accuracy") or 0.0))
        size = int(row.get("data_size") or 0)
        if cid:
            round_size[rid][cid] = size

    rounds = sorted([r for r in round_loss.keys() if r > 0])
    loss_curve = [round(sum(round_loss[r]) / max(1, len(round_loss[r])), 4) for r in rounds]
    acc_curve = [round(sum(round_acc[r]) / max(1, len(round_acc[r])), 4) for r in rounds]
    slope = 0.0
    if len(loss_curve) >= 2:
        slope = round((loss_curve[-1] - loss_curve[0]) / max(1, len(loss_curve) - 1), 5)
    if slope <= -0.003:
        convergence_state = "improving"
    elif slope >= 0.003:
        convergence_state = "degrading"
    else:
        convergence_state = "stable"

    personalized = {k: float(v) for k, v in (data.get("personalized_accuracy") or {}).items()}
    fairness_gap = 0.0
    if personalized:
        fairness_gap = round(max(personalized.values()) - min(personalized.values()), 2)
    if fairness_gap <= 1.5:
        fairness_state = "balanced"
    elif fairness_gap <= 3.0:
        fairness_state = "watch"
    else:
        fairness_state = "skewed"

    privacy_budget_used = float(data.get("privacy_budget_used") or 0.0)
    if privacy_budget_used >= 0.9:
        privacy_state = "critical"
    elif privacy_budget_used >= 0.75:
        privacy_state = "warning"
    else:
        privacy_state = "safe"

    latest_round = int(data.get("current_round") or 0)
    latest_sizes = round_size.get(latest_round, {})
    total_size = sum(latest_sizes.values()) or 1
    client_weights = [
        {"clinic_id": cid, "data_size": n, "weight": round(n / total_size, 4)}
        for cid, n in sorted(latest_sizes.items())
    ]

    recommendations: list[str] = []
    if convergence_state == "degrading":
        recommendations.append("全局Loss上升，建议降低本地学习率并增加聚合频率。")
    elif convergence_state == "stable":
        recommendations.append("模型收敛趋于平稳，可进入验证轮并准备灰度下发。")
    else:
        recommendations.append("收敛趋势良好，可继续执行下一轮联邦训练。")
    if fairness_state != "balanced":
        recommendations.append("院区个性化准确率差距偏大，建议对低准确率院区增加个性化微调步数。")
    if privacy_state != "safe":
        recommendations.append("隐私预算接近阈值，建议调高噪声强度并控制轮次。")

    return {
        "convergence": {
            "state": convergence_state,
            "loss_slope": slope,
            "rounds": rounds,
            "loss_curve": loss_curve,
            "accuracy_curve": acc_curve,
        },
        "fairness": {
            "state": fairness_state,
            "personalized_gap": fairness_gap,
        },
        "privacy": {
            "state": privacy_state,
            "budget_used": round(privacy_budget_used, 2),
            "budget_left": round(max(0.0, 1 - privacy_budget_used), 2),
        },
        "client_weights": client_weights,
        "recommendations": recommendations,
    }


@router.get("/status")
def federated_status() -> dict[str, object]:
    """返回联邦学习当前状态。"""
    if _server.current_round == 0:
        _server.run_round()
    data = _server.get_status()
    data["insights"] = _derive_federated_insights(data)
    return success_response(data=data)

