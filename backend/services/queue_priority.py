"""动态优先级排队算法模块。"""

from __future__ import annotations


def _urgency_to_score(urgency_level: str) -> float:
    """将紧急程度转换为基础分值。"""
    mapping = {"常规": 30.0, "优先": 65.0, "急诊": 100.0}
    return mapping.get(urgency_level, 30.0)


def calculate_priority_score(urgency_level: str, waiting_minutes: float, age_years: float) -> float:
    """基于紧急程度、等待时长和宠物年龄计算优先级评分。"""
    urgency_score = _urgency_to_score(urgency_level)
    waiting_score = min(max(waiting_minutes, 0.0), 240.0) / 240.0 * 100.0
    age_score = min(max(age_years, 0.0), 20.0) / 20.0 * 100.0
    return round(urgency_score * 0.5 + waiting_score * 0.3 + age_score * 0.2, 2)

