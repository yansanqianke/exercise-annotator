"""知识点相关 Pydantic Schema"""

from datetime import datetime

from pydantic import BaseModel, Field


class KPCreate(BaseModel):
    """创建知识点请求"""
    subject_id: int = Field(description="所属学科 ID")
    name: str = Field(min_length=1, max_length=100, description="知识点名称")
    description: str = Field(default="", description="详细描述")


class KPUpdate(BaseModel):
    """更新知识点请求"""
    name: str | None = Field(default=None, max_length=100, description="知识点名称")
    description: str | None = Field(default=None, description="详细描述")


class KPResponse(BaseModel):
    """知识点响应"""
    id: int
    subject_id: int
    code: str
    name: str
    description: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SimilarKPResponse(BaseModel):
    """相似知识点推荐响应"""
    kp_id: int
    code: str
    distance: float | None = None
