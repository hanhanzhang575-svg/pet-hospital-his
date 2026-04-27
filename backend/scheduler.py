"""后台定时任务调度器。"""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from backend.database import SessionLocal
from backend.services.deposit_monitor import daily_deposit_job
from backend.services.expiry_monitor import expiry_monitor_job
from backend.services.prescription_expiry import expired_prescription_job

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def start_scheduler() -> None:
    """启动系统定时任务。"""
    if scheduler.running:
        return
    scheduler.add_job(
        func=lambda: daily_deposit_job(SessionLocal),
        trigger="cron",
        hour=0,
        minute=5,
        id="daily_deposit_monitor",
        replace_existing=True,
    )
    scheduler.add_job(
        func=lambda: expired_prescription_job(SessionLocal),
        trigger="interval",
        minutes=15,
        id="expired_prescription_release",
        replace_existing=True,
    )
    scheduler.add_job(
        func=lambda: expiry_monitor_job(SessionLocal),
        trigger="cron",
        hour="*/6",
        minute=0,
        id="drug_expiry_monitor",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    """停止系统定时任务。"""
    if scheduler.running:
        scheduler.shutdown(wait=False)

