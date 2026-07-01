"""题目相关 Pydantic Schema"""

from datetime import datetime

from pydantic import BaseModel, Field


class KPAssignment(BaseModel):
    """知识点分配"""
    kp_id: int


class KPAssignmentResponse(BaseModel):
    """题目-知识点关联响应"""
    kp_id: int
    kp_code: str
    kp_name: str
    confidence: int | None
    is_manual: bool

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
