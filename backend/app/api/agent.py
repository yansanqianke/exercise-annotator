"""智能体调用接口 — SSE 流式传输"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.llm import chat_stream

router = APIRouter(prefix="/api/agent", tags=["智能体调用"])


class ChatRequest(BaseModel):
    """对话请求体"""
    messages: list[dict] = Field(description="消息列表，格式 [{'role':'user','content':'...'}]")


def _sse_event(event_type: str, data: str) -> str:
    """格式化 SSE 事件"""
    return f"data: {json.dumps({'type': event_type, 'content': data})}\n\n"


@router.post("/chat")
async def chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """大模型对话 — SSE 流式输出"""

    async def event_generator():
        try:
            for text_chunk in chat_stream(db, body.messages):
                yield _sse_event("thinking", text_chunk)
            yield _sse_event("done", "对话完成")
        except ValueError as e:
            yield _sse_event("error", str(e))
        except Exception as e:
            yield _sse_event("error", f"调用失败: {str(e)}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
