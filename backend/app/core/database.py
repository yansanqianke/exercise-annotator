"""数据库引擎与会话管理"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 确保数据目录存在
db_dir = os.path.dirname(settings.SQLITE_PATH)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# SQLite 引擎（check_same_thread=False 以支持异步 FastAPI）
engine = create_engine(
    f"sqlite:///{settings.SQLITE_PATH}",
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI 依赖注入：获取数据库会话，请求结束时自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
