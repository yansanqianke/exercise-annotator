"""测试全局 Fixtures — 内存数据库、测试客户端、测试用户"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.deps import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.base import Base
from app.models.user import User
# 确保所有模型都已导入，SQLAlchemy 才能正确解析 relationship
from app.models.subject import Subject  # noqa: F401
from app.models.knowledge_point import KnowledgePoint  # noqa: F401
from app.models.question import Question, QuestionKPMap  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.config import Agent, LLMConfig, SystemLog  # noqa: F401


TEST_DATABASE_URL = "sqlite:///:memory:"

# 模块级共享引擎 — 确保整个测试模块使用同一个内存数据库
_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture(scope="function")
def db_session():
    """每次测试创建独立的事务，测试结束回滚，保证隔离性"""
    # 首次创建所有表
    Base.metadata.create_all(bind=_engine)

    connection = _engine.connect()
    transaction = connection.begin()
    session = _TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI 测试客户端，注入测试数据库会话"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session) -> User:
    """创建并返回一个管理员测试用户"""
    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def teacher_user(db_session) -> User:
    """创建并返回一个教师测试用户"""
    user = User(
        username="teacher",
        email="teacher@example.com",
        password_hash=hash_password("admin123"),
        role="teacher",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def get_auth_header(user: User) -> dict:
    """为测试用户生成带 Bearer Token 的请求头"""
    token = create_access_token({"user_id": user.id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}
