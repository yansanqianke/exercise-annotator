"""智能体调用接口 — SSE 流式传输"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.annotator import annotate_stream
from app.services.llm import chat_stream

router = APIRouter(prefix="/api/agent", tags=["智能体调用"])


class ChatRequest(BaseModel):
    """对话请求体"""
    messages: list[dict] = Field(description="消息列表，格式 [{'role':'user','content':'...'}]")


class AnnotateRequest(BaseModel):
    """题目标注请求体"""
    content: str | None = Field(default=None, description="题目正文（不传 question_id 时必填）")
    subject_id: int = Field(description="所属学科 ID")
    question_id: int | None = Field(default=None, description="已有题目 ID，传入则重新标注该题目")


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


@router.post("/annotate")
async def annotate(
    body: AnnotateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """题目标注 — SSE 流式返回推理过程 + 最终结果
    传 question_id 则重新标注已有题目，否则输入 content 创建新题目并标注
    """

    async def event_generator():
        try:
            for event_json in annotate_stream(
                db, body.content, body.subject_id, current_user.id, body.question_id,
            ):
                yield f"data: {event_json}\n\n"
        except ValueError as e:
            yield _sse_event("error", str(e))
        except Exception as e:
            yield _sse_event("error", f"标注失败: {str(e)}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
