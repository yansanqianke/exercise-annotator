"""知识点管理接口 — 含 Chroma 向量同步和相似推荐"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.knowledge_point import KnowledgePoint
from app.schemas.knowledge_point import KPCreate, KPResponse, KPUpdate, SimilarKPResponse
from app.services.chroma_service import query_similar_kps, remove_kp_from_chroma, sync_kp_to_chroma

router = APIRouter(prefix="/api/kps", tags=["知识点管理"])


def _generate_kp_code(subject: Subject, db: Session) -> str:
    """自动生成知识点编码：{学科代码}-KP-{三位序号}"""
    # 查询该学科下已有 KP 的最大序号
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
    return f"{subject.code}-KP-{seq:03d}"


@router.get("", response_model=list[KPResponse])
def list_kps(
    subject_id: int | None = Query(None, description="按学科过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取知识点列表，可按学科过滤"""
    query = db.query(KnowledgePoint)
    if subject_id is not None:
        query = query.filter(KnowledgePoint.subject_id == subject_id)
    return query.order_by(KnowledgePoint.id).all()


@router.post("", response_model=KPResponse, status_code=status.HTTP_201_CREATED)
def create_kp(
    body: KPCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建知识点 — 自动生成编码，写入 Chroma 向量库"""
    subject = db.query(Subject).filter(Subject.id == body.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="学科不存在")

    kp = KnowledgePoint(
        subject_id=body.subject_id,
        code=_generate_kp_code(subject, db),
        name=body.name,
        description=body.description,
        created_by=current_user.id,
    )
    db.add(kp)
    db.commit()
    db.refresh(kp)

    # 同步写入 Chroma 向量库
    try:
        sync_kp_to_chroma(kp.id, kp.code, kp.name, kp.description, kp.subject_id)
    except Exception:
        pass  # Chroma 失败不影响数据库写入

    return kp


@router.get("/{kp_id}", response_model=KPResponse)
def get_kp(
    kp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个知识点详情"""
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")
    return kp


@router.put("/{kp_id}", response_model=KPResponse)
def update_kp(
    kp_id: int,
    body: KPUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新知识点 — 同步更新 Chroma 向量"""
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")

    if body.name is not None:
        kp.name = body.name
    if body.description is not None:
        kp.description = body.description

    db.commit()
    db.refresh(kp)

    # 同步更新 Chroma
    try:
        sync_kp_to_chroma(kp.id, kp.code, kp.name, kp.description, kp.subject_id)
    except Exception:
        pass

    return kp


@router.delete("/{kp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_kp(
    kp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """软删除知识点 — Chroma 同步移除"""
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")

    kp.is_deleted = True
    db.commit()

    try:
        remove_kp_from_chroma(kp.id)
    except Exception:
        pass


@router.get("/{kp_id}/similar", response_model=list[SimilarKPResponse])
def get_similar_kps(
    kp_id: int,
    top_k: int = Query(default=5, ge=1, le=20, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """相似知识点推荐 — 基于向量语义检索"""
    kp = db.query(KnowledgePoint).filter(KnowledgePoint.id == kp_id).first()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")

    query_text = f"{kp.name}: {kp.description}"
    results = query_similar_kps(query_text, subject_id=None, top_k=top_k + 1)

    # 排除自身
    return [r for r in results if r["kp_id"] != kp_id][:top_k]
