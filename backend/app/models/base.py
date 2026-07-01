"""SQLAlchemy 声明式基类，统一提供 id 和通用时间戳"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """ORM 基类，所有模型继承此类"""
    pass


class TimestampMixin:
    """混入创建时间 / 更新时间字段"""

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
