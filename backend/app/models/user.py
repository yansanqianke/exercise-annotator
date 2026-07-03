"""用户模型"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class User(Base):
    """用户表 — 支持 admin / teacher 两种角色"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="登录用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(128), nullable=False, comment="bcrypt 密码哈希")
    role = Column(String(20), nullable=False, default="teacher", comment="角色：admin / teacher")
    is_active = Column(Boolean, nullable=False, default=True, comment="账号是否启用")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="注册时间")

    # 关联
    subjects = relationship("Subject", back_populates="creator")
    knowledge_points = relationship("KnowledgePoint", back_populates="creator")
    questions = relationship("Question", back_populates="creator")
    documents = relationship("Document", back_populates="creator")
