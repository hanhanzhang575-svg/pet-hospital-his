"""实时通知连接池与推送服务。"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime

from fastapi import WebSocket
from sqlalchemy.orm import Session

from backend.models.core import Role, User


class RealtimeHub:
    """维护 WebSocket 连接池并支持按用户/角色推送消息。"""

    def __init__(self) -> None:
        self._user_sockets: dict[int, WebSocket] = {}
        self._role_users: dict[str, set[int]] = defaultdict(set)
        self._user_roles: dict[int, str] = {}

    async def connect(self, user_id: int, role: str, websocket: WebSocket) -> None:
        """注册连接。"""
        await websocket.accept()
        self.disconnect(user_id)
        self._user_sockets[user_id] = websocket
        self._user_roles[user_id] = role
        self._role_users[role].add(user_id)

    def disconnect(self, user_id: int) -> None:
        """移除连接。"""
        role = self._user_roles.pop(user_id, None)
        self._user_sockets.pop(user_id, None)
        if role is None:
            return
        role_users = self._role_users.get(role)
        if role_users is None:
            return
        role_users.discard(user_id)
        if not role_users:
            self._role_users.pop(role, None)

    async def send_to_user(
        self,
        user_id: int,
        *,
        role: str,
        title: str,
        content: str,
        level: str = "info",
    ) -> None:
        """向指定用户推送通知。"""
        websocket = self._user_sockets.get(user_id)
        if websocket is None:
            return
        await websocket.send_json(
            {
                "type": "notification",
                "role": role,
                "title": title,
                "content": content,
                "level": level,
                "target_user_id": user_id,
                "sent_at": datetime.utcnow().isoformat(),
            }
        )

    async def send_to_roles(
        self,
        roles: Iterable[str],
        *,
        title: str,
        content: str,
        level: str = "info",
    ) -> None:
        """向多个角色的在线用户广播通知。"""
        normalized = [self._normalize_role_name(role) for role in roles]
        for role in normalized:
            for user_id in list(self._role_users.get(role, set())):
                await self.send_to_user(
                    user_id,
                    role=role,
                    title=title,
                    content=content,
                    level=level,
                )

    @staticmethod
    def _normalize_role_name(role: str) -> str:
        """统一角色名别名。"""
        if role == "pharmacy":
            return "pharmacist"
        return role


hub = RealtimeHub()


def get_user_role(db: Session, user_id: int) -> str | None:
    """查询用户角色。"""
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if user is None:
        return None
    role = db.query(Role).filter(Role.id == user.role_id).first()
    if role is None:
        return None
    return hub._normalize_role_name(role.name)


def dispatch_async(coro) -> None:
    """在当前线程安全触发协程。"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)

