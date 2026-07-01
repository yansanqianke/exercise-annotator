"""学科相关 Pydantic Schema"""

from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    """创建学科请求"""
    code: str = Field(min_length=1, max_length=10, description="学科代码，如 DS、OS")
    name: str = Field(min_length=1, max_length=100, description="学科名称")
    description: str = Field(default="", description="简介")


class SubjectUpdate(BaseModel):
    """更新学科请求"""
    name: str | None = Field(default=None, max_length=100, description="学科名称")
    description: str | None = Field(default=None, description="简介")


class SubjectResponse(BaseModel):
    """学科响应"""
    id: int
    code: str
    name: str
    description: str
    created_by: int

    model_config = {"from_attributes": True}
