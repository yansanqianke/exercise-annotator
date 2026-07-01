"""大模型配置相关 Pydantic Schema"""

from pydantic import BaseModel, Field


class LLMConfigCreate(BaseModel):
    """创建 LLM 配置请求"""
    name: str = Field(min_length=1, max_length=50, description="配置名称")
    provider: str = Field(min_length=1, max_length=20, description="提供商：openai / qwen / deepseek")
    model: str = Field(min_length=1, max_length=50, description="模型名称")
    api_key: str = Field(min_length=1, max_length=200, description="API Key")
    base_url: str = Field(default="", max_length=200, description="自定义 API 端点")


class LLMConfigUpdate(BaseModel):
    """更新 LLM 配置请求"""
    name: str | None = Field(default=None, max_length=50)
    provider: str | None = Field(default=None, max_length=20)
    model: str | None = Field(default=None, max_length=50)
    api_key: str | None = Field(default=None, max_length=200)
    base_url: str | None = Field(default=None, max_length=200)


class LLMConfigResponse(BaseModel):
    """LLM 配置响应（不含 api_key）"""
    id: int
    name: str
    provider: str
    model: str
    base_url: str
    is_active: bool

    model_config = {"from_attributes": True}
