"""RAG 向量检索：加载 kb/docs.json → Chroma 索引 + 相似度检索 + 拒答。

Phase 3 M2。设计要点：
- 语料 `app/kb/docs.json`（已审校的编码/字形演变文案，从 aiService 的 CANNED 答案迁移）。
- embedding 用 fastembed 的 ``BAAI/bge-small-zh-v1.5``（ONNX、CPU、免 torch），首次运行自动下载模型。
- Chroma 集合用 cosine 空间；``similarity_search_with_score`` 返回距离（越小越相似），
  相似度 = 1 - 距离。
- 关键词命中作加分信号（语料 keywords 与问题做子串匹配），保证「问题里出现关键词」时一定命中。
- 相似度低于阈值或未命中 → 拒答。
- 索引懒加载：模块级单例 + 锁；首次请求时若持久目录为空则用 docs.json 建一次，之后直接加载。
  修改 docs.json 后，删除 persist 目录（默认 ./chroma_db）即可重建。
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings

# 语料嵌入模型（fastembed 的 HuggingFace 模型名）。
EMBED_MODEL = "BAAI/bge-small-zh-v1.5"
COLLECTION = "kb_docs"

# 关键词命中时加在相似度上的分（配合默认阈值 0.35：关键词命中必然通过）。
KEYWORD_BOOST = 0.45

# 检索无命中时的固定拒答文案（以 token 事件回给前端，无需调用 LLM）。
REFUSAL = (
    "这个问题暂不在当前知识库的覆盖范围内。"
    "可以问我汉字编码（Unicode / UTF-8 / GB2312 / GBK / Big5）、"
    "字形演变（甲骨文到楷书），或本产品的功能与架构。"
)


@dataclass
class RetrievedDoc:
    """一条检索命中结果，供 prompt 组装引用。"""

    id: str
    title: str
    page: str
    body: str
    score: float  # 相似度，越大越相关（含关键词加分，上限 1.0）


_store: object | None = None
_store_lock = threading.Lock()


def load_docs() -> list[dict]:
    """读取 kb/docs.json 的文档数组（纯函数，便于单测）。"""
    path = Path(get_settings().kb_source)
    payload = json.loads(path.read_text(encoding="utf-8"))
    docs = payload.get("documents")
    if not isinstance(docs, list) or not docs:
        raise ValueError(f"知识库语料为空或格式错误：{path}")
    return docs


def _make_embedding():
    from langchain_community.embeddings import FastEmbedEmbeddings

    return FastEmbedEmbeddings(model_name=EMBED_MODEL)


def _to_langchain_documents(docs: list[dict]) -> list:
    from langchain_core.documents import Document

    return [
        Document(
            page_content=d["body"],
            metadata={
                "id": d["id"],
                "title": d["title"],
                "page": d.get("page", ""),
                "keywords": d.get("keywords", []),
            },
        )
        for d in docs
    ]


def _build_store(docs: list[dict]):
    from langchain_chroma import Chroma

    persist = str(Path(get_settings().kb_persist_dir).resolve())
    return Chroma.from_documents(
        _to_langchain_documents(docs),
        _make_embedding(),
        collection_name=COLLECTION,
        persist_directory=persist,
        collection_metadata={"hnsw:space": "cosine"},
    )


def _load_store():
    from langchain_chroma import Chroma

    persist = str(Path(get_settings().kb_persist_dir).resolve())
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=_make_embedding(),
        persist_directory=persist,
        collection_metadata={"hnsw:space": "cosine"},
    )


def get_store():
    """返回 Chroma 向量库单例；无持久索引时先用 docs.json 建一次。"""
    global _store
    if _store is not None:
        return _store
    with _store_lock:
        if _store is not None:
            return _store
        docs = load_docs()
        persist = Path(get_settings().kb_persist_dir)
        if (persist / "chroma.sqlite3").exists():
            _store = _load_store()
        else:
            _store = _build_store(docs)
        return _store


def _rank(
    results: list[tuple[object, float]],
    question: str,
    threshold: float,
) -> list[RetrievedDoc]:
    """把 Chroma 的 (Document, 距离) 结果转成按相似度排序的 RetrievedDoc，低于阈值剔除。"""
    q = (question or "").lower()
    ranked: list[RetrievedDoc] = []
    for doc, distance in results:
        similarity = 1.0 - float(distance)
        meta = doc.metadata or {}
        keywords = meta.get("keywords") or []
        if any(isinstance(k, str) and k and k.lower() in q for k in keywords):
            similarity += KEYWORD_BOOST
        similarity = max(0.0, min(1.0, similarity))
        if similarity >= threshold:
            ranked.append(
                RetrievedDoc(
                    id=meta.get("id", ""),
                    title=meta.get("title", ""),
                    page=meta.get("page", ""),
                    body=doc.page_content,
                    score=round(similarity, 4),
                )
            )
    ranked.sort(key=lambda d: d.score, reverse=True)
    return ranked


def retrieve(question: str, top_k: int | None = None) -> list[RetrievedDoc]:
    """检索 top-k 片段；返回按相似度降序的结果（空列表 = 无命中，应拒答）。"""
    settings = get_settings()
    if top_k is None:
        top_k = settings.rag_top_k
    results = get_store().similarity_search_with_score(question, k=top_k)
    return _rank(results, question, settings.rag_sim_threshold)
