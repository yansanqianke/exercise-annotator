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

    # 未指定 base_url 时，按 provider 使用默认端点
    base_url = config.base_url or {
        "deepseek": "https://api.deepseek.com",
        "openai": "https://api.openai.com/v1",
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    }.get(config.provider, "")

    client = OpenAI(
        api_key=config.api_key,
        base_url=base_url or None,
    )
    return client, config.model


def estimate_tokens(text: str) -> int:
    """估算 token 数：英文 0.3/字符，中文 0.6/字符"""
    en = sum(1 for c in text if c.isascii() and not c.isspace())
    zh = sum(1 for c in text if not c.isascii() and not c.isspace())
    return int(en * 0.3 + zh * 0.6)


def chat_stream(db: Session, messages: list[dict], usage_container: dict | None = None):
    """流式对话 — 生成器逐块返回响应文本，usage_container 接收 LLM 返回的 token 用量"""
    client, model = build_client(db)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        if chunk.usage and usage_container is not None:
            usage_container["completion"] = chunk.usage.completion_tokens or 0
            usage_container["total"] = chunk.usage.total_tokens or 0
