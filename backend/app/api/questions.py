"""题目管理接口"""

import csv
import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.question import Question, QuestionKPMap
from app.models.knowledge_point import KnowledgePoint
from pydantic import BaseModel, Field

from app.schemas.question import KPAssignment, QuestionResponse

router = APIRouter(prefix="/api/questions", tags=["题目管理"])


class QuestionCreate(BaseModel):
    """创建题目请求（不含标注）"""
    content: str = Field(min_length=1, description="题目正文")
    subject_id: int = Field(description="所属学科 ID")


def _enrich_kp_maps(question: Question) -> Question:
    """为题目关联的知识点填充编码和名称"""
    for kpm in question.kp_maps:
        kp = kpm.knowledge_point
    return question


@router.get("", response_model=list[QuestionResponse])
def list_questions(
    subject_id: int | None = Query(None, description="按学科过滤"),
    type: str | None = Query(None, description="按题型过滤"),
    difficulty: int | None = Query(None, description="按难度过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取题目列表，支持按学科/题型/难度过滤"""
    query = db.query(Question).options(joinedload(Question.kp_maps).joinedload(QuestionKPMap.knowledge_point))

    # 注意：关系是 "kp_maps" 不是 "question_kp_map" — 需要确认
    if subject_id is not None:
        query = query.filter(Question.subject_id == subject_id)
    if type is not None:
        query = query.filter(Question.type == type)
    if difficulty is not None:
        query = query.filter(Question.difficulty == difficulty)

    return query.order_by(Question.id.desc()).all()


@router.get("/export")
def export_questions(
    fmt: str = Query(default="csv", description="导出格式：csv 或 json"),
    ids: str | None = Query(default=None, description="题目 ID 列表，逗号分隔"),
    subject_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出题目（CSV / JSON）— 必须在 /{question_id} 之前定义"""
    query = db.query(Question).options(
        joinedload(Question.kp_maps).joinedload(QuestionKPMap.knowledge_point)
    )

    if ids:
        id_list = [int(i) for i in ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(Question.id.in_(id_list))
    if subject_id is not None:
        query = query.filter(Question.subject_id == subject_id)

    questions = query.order_by(Question.id).all()
    type_map = {"choice": "选择题", "judgment": "判断题", "short_answer": "简答题", "programming": "编程题"}

    if fmt == "json":
        data = []
        for q in questions:
            data.append({
                "id": q.id, "subject_id": q.subject_id, "content": q.content,
                "type": q.type, "difficulty": q.difficulty,
                "kp_codes": [m.knowledge_point.code for m in q.kp_maps if m.knowledge_point],
            })
        return Response(content=json.dumps(data, ensure_ascii=False, indent=2), media_type="application/json")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "学科ID", "题型", "难度", "知识点编码", "题目正文"])
    for q in questions:
        kp_str = "; ".join(m.knowledge_point.code for m in q.kp_maps if m.knowledge_point)
        writer.writerow([q.id, q.subject_id, type_map.get(q.type, q.type or ""), q.difficulty or "", kp_str, q.content])
    csv_content = output.getvalue()
    output.close()
    return Response(content=csv_content, media_type="text/csv; charset=utf-8-sig")


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    body: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建题目（仅保存到题库，不触发标注）"""
    question = Question(
        subject_id=body.subject_id,
        content=body.content,
        type=None,
        created_by=current_user.id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("/{question_id}", response_model=QuestionResponse)
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取题目详情（含标注结果）"""
    question = (
        db.query(Question)
        .options(joinedload(Question.kp_maps).joinedload(QuestionKPMap.knowledge_point))
        .filter(Question.id == question_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    return question


@router.put("/{question_id}/kps")
def update_question_kps(
    question_id: int,
    body: list[KPAssignment],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动修正题目知识点关联 — 用传入的 KP 列表替换现有关联"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 清除旧关联
    db.query(QuestionKPMap).filter(QuestionKPMap.question_id == question_id).delete()

    # 创建新关联（标记为手动修正）
    for kp_item in body:
        kpm = QuestionKPMap(
            question_id=question_id,
            kp_id=kp_item.kp_id,
            is_manual=True,
        )
        db.add(kpm)

    db.commit()
    return {"message": "已更新"}


@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除题目"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    db.query(QuestionKPMap).filter(QuestionKPMap.question_id == question_id).delete()
    db.delete(question)
    db.commit()
