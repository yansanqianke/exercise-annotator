"""数据初始化脚本 — 创建默认管理员、示例学科和知识点"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.knowledge_point import KnowledgePoint  # noqa: F401
from app.models.question import Question, QuestionKPMap  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.config import LLMConfig, Agent, SystemLog  # noqa: F401

# 示例数据
SAMPLE_DATA = {
    "数据结构（DS）": {
        "code": "DS",
        "description": "数据结构与算法基础",
        "kps": [
            ("线性表", "顺序表、链表的基本概念与操作"),
            ("栈和队列", "栈的FILO特性、队列的FIFO特性及其应用"),
            ("树与二叉树", "二叉树的遍历、二叉搜索树、平衡树"),
            ("图", "图的存储结构、DFS/BFS遍历、最短路径"),
            ("查找算法", "顺序查找、二分查找、哈希查找"),
            ("排序算法", "冒泡、快排、归并排序、堆排序"),
        ],
    },
    "操作系统（OS）": {
        "code": "OS",
        "description": "操作系统核心概念",
        "kps": [
            ("进程管理", "进程状态转换、PCB、进程调度算法"),
            ("线程", "线程与进程的区别、多线程编程模型"),
            ("死锁", "死锁的四个必要条件、银行家算法"),
            ("内存管理", "分页、分段、虚拟内存、页面置换算法"),
            ("文件系统", "文件组织方式、目录结构、文件分配"),
        ],
    },
}


def init_admin():
    """创建默认管理员账户"""
    # 先创建所有表（如果不存在）
    from app.models.base import Base
    from app.core.database import engine
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    existing = db.query(User).filter(User.username == "admin").first()
    if existing:
        print("[跳过] 管理员账户已存在")
    else:
        user = User(
            username="admin",
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(user)
        db.commit()
        print("管理员账户已创建（admin / admin123）")

    # 获取管理员用户用于创建学科
    admin = db.query(User).filter(User.username == "admin").first()

    # 创建示例学科和知识点
    for subject_name, data in SAMPLE_DATA.items():
        existing_subject = db.query(Subject).filter(Subject.code == data["code"]).first()
        if existing_subject:
            print(f"[跳过] 学科 {data['code']} 已存在")
            subject = existing_subject
        else:
            subject = Subject(
                code=data["code"],
                name=subject_name,
                description=data["description"],
                created_by=admin.id,
            )
            db.add(subject)
            db.commit()
            db.refresh(subject)
            print(f"学科已创建: {data['code']} {subject_name}")

        # 创建知识点
        for kp_name, kp_desc in data["kps"]:
            existing_kp = (
                db.query(KnowledgePoint)
                .filter(KnowledgePoint.subject_id == subject.id, KnowledgePoint.name == kp_name)
                .first()
            )
            if existing_kp:
                continue

            # 自动编码
            latest = (
                db.query(KnowledgePoint)
                .filter(KnowledgePoint.subject_id == subject.id)
                .order_by(KnowledgePoint.id.desc())
                .first()
            )
            if latest and latest.code.startswith(subject.code + "-KP-"):
                seq = int(latest.code.split("-KP-")[1]) + 1
            else:
                seq = 1
            code = f"{subject.code}-KP-{seq:03d}"

            kp = KnowledgePoint(
                subject_id=subject.id,
                code=code,
                name=kp_name,
                description=kp_desc,
                created_by=admin.id,
            )
            db.add(kp)
            db.commit()

            # 同步 Chroma
            try:
                from app.services.chroma_service import sync_kp_to_chroma
                sync_kp_to_chroma(kp.id, kp.code, kp.name, kp.description, kp.subject_id)
            except Exception:
                pass

        print(f"  └─ {len(data['kps'])} 个知识点已就绪")

    db.close()
    print("\n初始化完成！启动后端后访问 http://localhost:5173 即可使用。")


if __name__ == "__main__":
    init_admin()
