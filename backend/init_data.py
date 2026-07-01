"""数据初始化脚本 — 创建默认管理员账户"""

import os
import sys

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.core.security import hash_password
# 预导入全部模型 — 确保 SQLAlchemy 能解析所有 relationship
from app.models.user import User  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.knowledge_point import KnowledgePoint  # noqa: F401
from app.models.question import Question, QuestionKPMap  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.config import LLMConfig, Agent, SystemLog  # noqa: F401


def init_admin():
    """创建默认管理员账户"""
    db = SessionLocal()

    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print("管理员账户已存在，跳过")
        db.close()
        return

    user = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    db.add(user)
    db.commit()
    db.close()
    print("默认管理员账户已创建")
    print("  用户名: admin")
    print("  密码: admin123")
    print("  登录后请尽快修改密码")


if __name__ == "__main__":
    init_admin()
