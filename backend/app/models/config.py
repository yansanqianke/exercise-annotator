"""大模型配置 & 智能体 & 系统日志模型"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base


class LLMConfig(Base):
    """大模型配置表 — 同一时间只有一个激活"""

    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="配置名称")
    provider = Column(String(20), nullable=False, comment="提供商：openai / qwen / deepseek")
    model = Column(String(50), nullable=False, comment="模型名称，如 deepseek-chat")
    api_key = Column(String(200), nullable=False, comment="API Key（生产环境应加密存储）")
    base_url = Column(String(200), default="", comment="自定义 API 端点")
    is_active = Column(Boolean, default=False, comment="当前使用的配置")


class Agent(Base):
    """智能体配置表"""

    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="智能体名称")
    description = Column(Text, default="", comment="功能介绍")
    agent_type = Column(String(20), nullable=False, comment="类型：annotator / chat")
    config_json = Column(Text, default="{}", comment="JSON 格式，存储 top_k、温度等参数")
    is_active = Column(Boolean, default=True, comment="是否启用")


class SystemLog(Base):
    """系统调用日志表"""

    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="调用用户")
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, comment="关联智能体")
    action = Column(String(50), nullable=False, comment="动作：annotate / chat / index_doc")
    input_summary = Column(Text, default="", comment="输入摘要（前 100 字）")
    tokens_used = Column(Integer, default=0, comment="消耗 token 数")
    latency_ms = Column(Integer, default=0, comment="耗时（毫秒）")
    status = Column(String(20), default="success", comment="状态：success / error")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="调用时间")
