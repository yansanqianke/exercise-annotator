"""题目相关 Pydantic Schema"""

from datetime import datetime

from pydantic import BaseModel, Field


class KPAssignment(BaseModel):
    """知识点分配"""
    kp_id: int


class KPInfo(BaseModel):
    """知识点简要信息（来自关联的 knowledge_point）"""
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class KPAssignmentResponse(BaseModel):
    """题目-知识点关联响应"""
    kp_id: int
    confidence: int | None
    is_manual: bool
    knowledge_point: KPInfo

    model_config = {"from_attributes": True}


class QuestionResponse(BaseModel):
    """题目响应"""
    id: int
    subject_id: int
    content: str
    type: str
    difficulty: int | None
    created_at: datetime
    kp_maps: list[KPAssignmentResponse] = []

    model_config = {"from_attributes": True}
