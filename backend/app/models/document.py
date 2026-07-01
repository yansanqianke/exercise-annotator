"""文档模型"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class Document(Base):
    """文档表 — 参考资料或题目文档"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(200), nullable=False, comment="服务器存储路径")
    original_name = Column(String(200), nullable=False, comment="原始文件名")
    doc_type = Column(String(20), nullable=False, comment="类型：reference（参考资料）/ questions（题目文档）")
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False, comment="所属学科")
    status = Column(String(20), default="pending", comment="状态：pending / processing / done / failed")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传者")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="上传时间")

    # 关联
    creator = relationship("User", back_populates="documents")
    subject = relationship("Subject", back_populates="documents")
