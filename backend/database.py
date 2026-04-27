"""数据库连接与会话管理模块。"""

from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./shironosuke.db"


class Base(DeclarativeBase):
    """ORM模型基类。"""


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, _connection_record) -> None:
    """设置SQLite运行参数，启用WAL并保证外键约束生效。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def get_db():
    """提供请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

