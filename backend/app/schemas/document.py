"""文档相关 Pydantic Schema"""

from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    filename: str
    original_name: str
    doc_type: str
    subject_id: int
    status: str
    created_at: datetime
