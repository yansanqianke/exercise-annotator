"""LLM 客户端服务 — 多 provider 适配（DeepSeek / OpenAI / Qwen）"""

from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.config import LLMConfig


def _get_active_config(db: Session) -> LLMConfig | None:
    """获取当前激活的 LLM 配置"""
    return db.query(LLMConfig).filter(LLMConfig.is_active == True).first()


def build_client(db: Session) -> tuple[OpenAI, str]:
    """根据激活的配置构建 OpenAI 兼容客户端，返回 (client, model_name)"""
    config = _get_active_config(db)
    if not config:
        raise ValueError("没有激活的大模型配置，请先在管理页面配置并激活")

    client = OpenAI(
        api_key=config.api_key,
        base_url=config.base_url or None,
    )
    return client, config.model


def chat_stream(db: Session, messages: list[dict]):
    """流式对话 — 生成器逐块返回响应文本"""
    client, model = build_client(db)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
