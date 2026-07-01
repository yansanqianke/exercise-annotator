"""习题标注智能体 — RAG 双路检索 + LLM 推理"""

import json
import re

from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question, QuestionKPMap
from app.services.chroma_service import query_similar_kps
from app.services.llm import build_client


# 标注 Prompt 模板
ANNOTATION_PROMPT = """你是一个专业的教育领域知识点标注专家。

## 候选知识点列表（来自 {subject_name} 学科）：
{kp_list}

## 参考资料上下文：
{ref_context}

## 任务
请分析以下题目，完成标注任务。输出必须是合法 JSON，格式严格如下：
{{
  "kp_codes": ["DS-KP-XXX", ...],
  "suggest_kps": [{{"name": "知识点名称", "description": "简要描述"}}, ...],
  "difficulty": 3,
  "question_type": "programming",
  "reasoning": "..."
}}

- kp_codes: 涉及的知识点编码列表，从候选列表中选择，1-5个。若无匹配则传空数组 []
- suggest_kps: **重要** 如果题目涉及的知识点在候选列表中不存在，建议创建新知识点。每个建议包含 name（名称）和 description（简要描述，50字以内）。若无建议传空数组 []
- difficulty: 难度 1(易)-5(难)
- question_type: 题型，choice(选择题)/judgment(判断题)/short_answer(简答题)/programming(编程题)
- reasoning: 简要说明标注依据（50字以内）

## 题目内容：
{question_content}"""


def _get_kp_list_text(subject_id: int, db: Session) -> str:
    """获取学科知识点列表文本，用于 Prompt 注入"""
    kps = (
        db.query(KnowledgePoint)
        .filter(KnowledgePoint.subject_id == subject_id, KnowledgePoint.is_deleted == False)
        .order_by(KnowledgePoint.code)
        .all()
    )
    if not kps:
        return "（暂无知识点）"
    lines = [f"- {kp.code}: {kp.name}" for kp in kps]
    return "\n".join(lines)


def _parse_llm_json(text: str) -> dict | None:
    """解析 LLM 返回的结构化 JSON，容错处理"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试从 markdown 代码块中提取
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试捕获 {} 块
    match = re.search(r'\{[^{}]*"kp_codes"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _validate_kp_codes(kp_codes: list[str], subject_id: int, db: Session) -> list:
    """校验知识点编码是否存在于数据库中，返回有效的 KnowledgePoint 列表"""
    valid = (
        db.query(KnowledgePoint)
        .filter(
            KnowledgePoint.code.in_(kp_codes),
            KnowledgePoint.subject_id == subject_id,
            KnowledgePoint.is_deleted == False,
        )
        .all()
    )
    return valid


def annotate_stream(db: Session, content: str, subject_id: int, user_id: int):
    """
    标注管道 — 生成器逐块返回文本

    流程：检索候选 KP → 构造 Prompt → LLM 流式推理 → 解析 JSON → 持久化
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        yield json.dumps({"type": "error", "content": "学科不存在"})
        return

    # ① 双路并行检索
    yield json.dumps({"type": "thinking", "content": "正在检索相关知识点..."})

    # 语义检索 top-10 候选知识点
    similar_results = query_similar_kps(content, subject_id=subject_id, top_k=10)
    similar_kp_ids = {r["kp_id"] for r in similar_results}

    # 获取完整知识点列表作为 Prompt 候选
    kp_list_text = _get_kp_list_text(subject_id, db)

    # 参考资料检索（目前可能为空，P5 文档上传后可用）
    ref_context = "（暂无参考资料）"
    # TODO P5: 从 ref_materials 检索参考段落

    # ② 构造 Prompt
    yield json.dumps({"type": "thinking", "content": "正在调用大模型进行标注推理..."})

    prompt = ANNOTATION_PROMPT.format(
        subject_name=subject.name,
        kp_list=kp_list_text,
        ref_context=ref_context,
        question_content=content,
    )

    # ③ LLM 流式推理
    client, model = build_client(db)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    full_text = ""
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            full_text += text
            yield json.dumps({"type": "thinking", "content": text})

    # ④ 解析结构化结果
    parsed = _parse_llm_json(full_text)
    if not parsed:
        yield json.dumps({"type": "error", "content": f"无法解析 LLM 输出为 JSON: {full_text[:200]}..."})
        return

    kp_codes = parsed.get("kp_codes", [])
    suggest_kps = parsed.get("suggest_kps", [])
    difficulty = parsed.get("difficulty", 3)
    question_type = parsed.get("question_type", "short_answer")
    reasoning = parsed.get("reasoning", "")

    # 校验知识点编码
    valid_kps = _validate_kp_codes(kp_codes, subject_id, db)

    # ⑤ 持久化题目
    question = Question(
        subject_id=subject_id,
        content=content,
        type=question_type,
        difficulty=difficulty,
        created_by=user_id,
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    for kp in valid_kps:
        kp_map = QuestionKPMap(
            question_id=question.id,
            kp_id=kp.id,
            confidence=100,
        )
        db.add(kp_map)
    db.commit()

    # ⑥ 推送最终结果（含建议知识点）
    result = {
        "type": "result",
        "question_id": question.id,
        "kp_codes": [kp.code for kp in valid_kps],
        "suggest_kps": suggest_kps,  # 新知识点建议
        "difficulty": difficulty,
        "question_type": question_type,
        "reasoning": reasoning,
    }
    yield json.dumps(result)

    yield json.dumps({"type": "done", "content": "标注完成"})
