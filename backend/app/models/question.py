"""题目模型"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class Question(Base):
    """题目表 — 支持选择、判断、简答、编程四种题型"""

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, comment="所属学科")
    content = Column(Text, nullable=False, comment="题目正文")
    type = Column(String(20), nullable=False, default="", comment="题型：choice / judgment / short_answer / programming，未标注时为空")
    difficulty = Column(Integer, nullable=True, comment="难度 1–5，由 LLM 标注")
    source_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=True, comment="来源文档（批量导入时填写）")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="创建时间")

    # 关联
    subject = relationship("Subject", back_populates="questions")
    creator = relationship("User", back_populates="questions")
    kp_maps = relationship("QuestionKPMap", back_populates="question")


class QuestionKPMap(Base):
    """题目-知识点关联表"""

    __tablename__ = "question_kp_map"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, comment="题目 ID")
    kp_id = Column(Integer, ForeignKey("knowledge_points.id"), nullable=False, comment="知识点 ID")
    confidence = Column(Integer, nullable=True, comment="LLM 输出的置信度 0.0–1.0，实际存储为整数百分比")
    is_manual = Column(Boolean, default=False, comment="是否为教师手动修正")

    # 关联
    question = relationship("Question", back_populates="kp_maps")
    knowledge_point = relationship("KnowledgePoint", back_populates="question_maps")
