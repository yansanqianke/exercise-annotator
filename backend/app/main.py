"""FastAPI 应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin import router as admin_router
from app.api.auth import router as auth_router
from app.api.agent import router as agent_router
from app.api.documents import router as documents_router
from app.api.questions import router as questions_router
from app.api.kps import router as kps_router
from app.api.llm_config import router as llm_config_router
from app.api.subjects import router as subjects_router
from app.core.config import settings

# 预导入全部模型 — 确保 SQLAlchemy 能解析所有 relationship
from app.models.user import User  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.knowledge_point import KnowledgePoint  # noqa: F401
from app.models.question import Question, QuestionKPMap  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.config import LLMConfig, Agent, SystemLog  # noqa: F401

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

# CORS — 开发阶段允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(subjects_router)
app.include_router(kps_router)
app.include_router(llm_config_router)
app.include_router(agent_router)
app.include_router(questions_router)
app.include_router(documents_router)


@app.get("/health")
def health_check():
    """健康检查端点"""
    return {"status": "ok"}
