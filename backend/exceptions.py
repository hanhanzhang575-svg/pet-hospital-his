"""统一业务异常定义。"""

from __future__ import annotations


class ApiError(Exception):
    """统一业务异常，映射API错误码与消息。"""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

