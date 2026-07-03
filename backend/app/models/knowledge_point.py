"""知识点模型"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class KnowledgePoint(Base):
    """知识点表 — 软删除，编码格式 {学科代码}-KP-{三位序号}"""

    __tablename__ = "knowledge_points"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, comment="所属学科")
    code = Column(String(20), unique=True, nullable=False, comment="自动生成编码，如 DS-KP-001")
    name = Column(String(100), nullable=False, comment="知识点名称")
    description = Column(Text, default="", comment="详细描述，也是嵌入的文本来源")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者")
    is_deleted = Column(Boolean, default=False, comment="软删除标记")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联
    subject = relationship("Subject", back_populates="knowledge_points")
    creator = relationship("User", back_populates="knowledge_points")
    question_maps = relationship("QuestionKPMap", back_populates="knowledge_point")
