"""学科模型"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Subject(Base):
    """学科表"""

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, comment="学科代码，如 DS、OS")
    name = Column(String(100), nullable=False, comment="学科名称，如 数据结构")
    description = Column(Text, default="", comment="简介")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    # 关联
    creator = relationship("User", back_populates="subjects")
    knowledge_points = relationship("KnowledgePoint", back_populates="subject")
    questions = relationship("Question", back_populates="subject")
    documents = relationship("Document", back_populates="subject")
