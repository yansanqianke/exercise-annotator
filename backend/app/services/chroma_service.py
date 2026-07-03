"""Chroma 向量数据库服务 — 管理 kp_store 和 ref_materials 两个 Collection"""

import os

import chromadb

from app.core.config import settings

# 模块级变量，通过 get_chroma_path() / init_chroma() 访问
_chroma_client = None
kp_store = None
ref_materials = None


def get_chroma_path() -> str:
    """获取 Chroma 持久化路径"""
    return settings.CHROMA_PATH


def init_chroma():
    """初始化 Chroma 客户端和 Collection（首次调用时执行）"""
    global _chroma_client, kp_store, ref_materials

    if _chroma_client is not None:
        return

    chroma_path = get_chroma_path()
    os.makedirs(chroma_path, exist_ok=True)

    _chroma_client = chromadb.PersistentClient(path=chroma_path)

    kp_store = _chroma_client.get_or_create_collection(
        name="kp_store",
        metadata={"description": "知识点向量存储"},
    )
    ref_materials = _chroma_client.get_or_create_collection(
        name="ref_materials",
        metadata={"description": "参考资料向量存储"},
    )


def _ensure_init():
    """确保 Chroma 已初始化"""
    if _chroma_client is None:
        init_chroma()


def sync_kp_to_chroma(kp_id: int, code: str, name: str, description: str, subject_id: int):
    """知识点写入 / 更新时同步到 Chroma kp_store"""
    _ensure_init()
    embedding_text = f"{name}: {description}"

    existing = kp_store.get(ids=[str(kp_id)])
    if existing["ids"]:
        kp_store.delete(ids=[str(kp_id)])

    kp_store.add(
        ids=[str(kp_id)],
        documents=[embedding_text],
        metadatas=[{
            "kp_id": kp_id,
            "code": code,
            "subject_id": subject_id,
        }],
    )


def remove_kp_from_chroma(kp_id: int):
    """软删除时从 Chroma 移除知识点向量"""
    _ensure_init()
    kp_store.delete(ids=[str(kp_id)])


def query_similar_kps(query_text: str, subject_id: int | None = None, top_k: int = 5) -> list[dict]:
    """语义检索 top-K 候选知识点，可按学科过滤"""
    _ensure_init()
    where_filter = None
    if subject_id is not None:
        where_filter = {"subject_id": subject_id}

    results = kp_store.query(
        query_texts=[query_text],
        n_results=top_k,
        where=where_filter,
    )

    if not results["metadatas"] or not results["metadatas"][0]:
        return []

    kp_list = []
    for i, meta in enumerate(results["metadatas"][0]):
        kp_list.append({
            "kp_id": meta["kp_id"],
            "code": meta["code"],
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return kp_list


def query_ref_materials(query_text: str, subject_id: int | None = None, top_k: int = 3) -> list[dict]:
    """从参考资料向量库检索相关段落"""
    _ensure_init()
    where_filter = None
    if subject_id is not None:
        where_filter = {"subject_id": subject_id}

    results = ref_materials.query(
        query_texts=[query_text],
        n_results=top_k,
        where=where_filter,
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "content": doc,
            "doc_id": results["metadatas"][0][i].get("doc_id") if results.get("metadatas") else None,
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return chunks
