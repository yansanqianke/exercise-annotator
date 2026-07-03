"""文档管理接口 — 上传、索引、提取题目"""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.config import SystemLog
from app.services.parser import chunk_text, extract_text

router = APIRouter(prefix="/api/documents", tags=["文档管理"])

def _write_log(user_id: int, action: str, summary: str, status: str = "success"):
    """写入系统日志（独立 session）"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        log = SystemLog(user_id=user_id, action=action, input_summary=summary[:200], status=status)
        db.add(log)
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


# 上传文件存储目录
UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("")
def list_documents(
    subject_id: int | None = Query(None),
    doc_type: str | None = Query(None, description="按类型过滤：reference 或 questions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文档列表"""
    from app.models.document import Document as DocModel
    from app.schemas.document import DocumentResponse

    query = db.query(DocModel)
    if subject_id is not None:
        query = query.filter(DocModel.subject_id == subject_id)
    if doc_type is not None:
        query = query.filter(DocModel.doc_type == doc_type)
    documents = query.order_by(DocModel.id.desc()).all()
    return [
        DocumentResponse(
            id=d.id,
            filename=d.filename,
            original_name=d.original_name,
            doc_type=d.doc_type,
            subject_id=d.subject_id,
            status=d.status,
            created_at=d.created_at,
        )
        for d in documents
    ]


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(..., description="reference 或 questions"),
    subject_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """上传文档"""
    if doc_type not in ("reference", "questions"):
        raise HTTPException(status_code=400, detail="doc_type 必须为 reference 或 questions")

    # 保存文件
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else ""
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 创建数据库记录
    doc = Document(
        filename=file_path,
        original_name=file.filename,
        doc_type=doc_type,
        subject_id=subject_id,
        status="pending",
        created_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"id": doc.id, "original_name": doc.original_name, "status": doc.status}


@router.post("/{doc_id}/index")
def index_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """将参考资料解析并写入 Chroma ref_materials"""
    from app.models.document import Document as DocModel
    from app.services.chroma_service import ref_materials, init_chroma

    doc_record = db.query(DocModel).filter(DocModel.id == doc_id).first()
    if not doc_record:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc_record.doc_type != "reference":
        raise HTTPException(status_code=400, detail="只有参考资料可以索引")

    doc_record.status = "processing"
    db.commit()

    try:
        with open(doc_record.filename, "rb") as f:
            content = f.read()
        text = extract_text(doc_record.filename, content)
        chunks = chunk_text(text)

        # 确保 Chroma 已初始化
        init_chroma()

        # 写入 Chroma ref_materials collection
        for i, chunk in enumerate(chunks):
            ref_materials.add(
                ids=[f"doc_{doc_id}_chunk_{i}"],
                documents=[chunk],
                metadatas=[{
                    "doc_id": doc_id,
                    "subject_id": doc_record.subject_id,
                    "chunk_index": i,
                }],
            )

        doc_record.status = "done"
        db.commit()
        _write_log(current_user.id, "index_doc", doc_record.original_name[:200])
        return {"status": "done", "chunks": len(chunks)}
    except Exception as e:
        doc_record.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"索引失败: {str(e)}")


@router.post("/{doc_id}/extract")
def extract_questions(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从题目文档提取题目并自动入库"""
    from app.models.document import Document as DocModel
    from app.models.question import Question
    from app.services.llm import build_client

    doc_record = db.query(DocModel).filter(DocModel.id == doc_id).first()
    if not doc_record:
        raise HTTPException(status_code=404, detail="文档不存在")
    if doc_record.doc_type != "questions":
        raise HTTPException(status_code=400, detail="只有题目文档可以提取")

    try:
        with open(doc_record.filename, "rb") as f:
            content = f.read()
        text = extract_text(doc_record.filename, content)

        # 使用 LLM 提取题目列表
        client, model = build_client(db)
        prompt = f"""从以下文档内容中提取所有题目，返回 JSON 数组格式。只输出 JSON 数组，不要有其他内容。

每道题目包含：
- content: 题目完整正文
- type: 题型，choice(选择题)/judgment(判断题)/short_answer(简答题)/programming(编程题)
- difficulty: 预估难度 1(易)-5(难)

文档内容：
{text[:8000]}

输出示例：
[{{"content":"以下哪个是线性数据结构？A. 树 B. 栈 C. 图 D. 堆","type":"choice","difficulty":1}}]"""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )

        import json, re
        raw = response.choices[0].message.content
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
            raw = re.sub(r"\n?```\s*$", "", raw)
        questions = json.loads(raw)

        # 自动入库
        saved = 0
        valid_types = {"choice", "judgment", "short_answer", "programming"}
        for q in questions:
            if q.get("content", "").strip():
                qtype = q.get("type", "short_answer")
                if qtype not in valid_types:
                    qtype = "short_answer"
                difficulty = q.get("difficulty")
                if difficulty is not None:
                    difficulty = max(1, min(5, int(difficulty)))
                question = Question(
                    subject_id=doc_record.subject_id,
                    content=q["content"].strip(),
                    type=qtype,
                    difficulty=difficulty,
                    source_doc_id=doc_id,
                    created_by=current_user.id,
                )
                db.add(question)
                saved += 1

        doc_record.status = "done"
        db.commit()
        _write_log(current_user.id, "extract_questions", f"提取{saved}题")
        return {"questions": questions, "saved": saved}
    except Exception as e:
        doc_record.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"提取失败: {str(e)}")
