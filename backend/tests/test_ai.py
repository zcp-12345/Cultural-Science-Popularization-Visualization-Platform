"""AI 对话（Phase 3）测试：SSE 通道 / prompt 组装 / RAG 检索与拒答 / 无密钥 / 空问题。

全程 mock LLM 与向量库，不发真实网络请求、不下载 embedding 模型。
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import ai as ai_service
from app.services import rag

API = "/api/v1"


class _Settings:
    def __init__(self, **kw):
        self.ai_enabled = kw.get("ai_enabled", True)
        self.deepseek_api_key = kw.get("deepseek_api_key", "sk-test")
        self.rag_top_k = kw.get("rag_top_k", 3)
        self.rag_sim_threshold = kw.get("rag_sim_threshold", 0.35)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _patch_settings(monkeypatch, **kw):
    monkeypatch.setattr("app.api.routes.ai.get_settings", lambda: _Settings(**kw))


def _patch_retrieve(monkeypatch, docs):
    monkeypatch.setattr("app.api.routes.ai.rag.retrieve", lambda *a, **k: docs)


# --- 通道与前置校验 ---


def test_rejects_empty_question(client):
    assert client.post(f"{API}/ai/chat", json={"question": "   "}).status_code == 400


def test_disabled_returns_503(client, monkeypatch):
    _patch_settings(monkeypatch, ai_enabled=False)
    r = client.post(f"{API}/ai/chat", json={"question": "你好"})
    assert r.status_code == 503


def test_no_key_returns_503(client, monkeypatch):
    _patch_settings(monkeypatch, deepseek_api_key="")
    r = client.post(f"{API}/ai/chat", json={"question": "你好"})
    assert r.status_code == 503


def test_streams_tokens_with_rag_hit(client, monkeypatch):
    docs = [rag.RetrievedDoc("utf8-bytes", "UTF-8 字节规则", "编码对比器", "UTF-8 是变长编码", 0.9)]

    async def fake_stream(question, page, char, docs=None):
        assert docs and docs[0].id == "utf8-bytes"
        yield "你好"
        yield "，世界"

    monkeypatch.setattr("app.api.routes.ai.ai_service.stream_reply", fake_stream)
    _patch_retrieve(monkeypatch, docs)
    _patch_settings(monkeypatch)

    with client.stream("POST", f"{API}/ai/chat", json={"question": "你好"}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())

    assert 'data: {"type": "token", "text": "你好"}' in body
    assert 'data: {"type": "token", "text": "，世界"}' in body
    assert 'data: {"type": "done"}' in body


def test_refuses_when_no_rag_hit(client, monkeypatch):
    _patch_retrieve(monkeypatch, [])
    _patch_settings(monkeypatch)

    with client.stream("POST", f"{API}/ai/chat", json={"question": "今天天气怎么样"}) as resp:
        body = "".join(resp.iter_text())

    assert rag.REFUSAL in body
    assert 'data: {"type": "done"}' in body


# --- prompt 组装 ---


def test_build_prompt_injects_char_facts():
    system, user = ai_service.build_prompt("它是什么？", "编码对比器", "中")
    assert "U+4E2D" in system
    assert "编码对比器" in system
    assert user == "它是什么？"


def test_build_prompt_injects_rag_context():
    docs = [
        rag.RetrievedDoc("utf8-bytes", "UTF-8 字节规则", "编码对比器", "UTF-8 是变长编码", 0.9),
        rag.RetrievedDoc("mojibake", "乱码排查", "编码对比器", "乱码来自字符集不匹配", 0.8),
    ]
    system, _ = ai_service.build_prompt("UTF-8 为什么 3 字节", "编码对比器", None, docs)
    assert "[1]《UTF-8 字节规则》：UTF-8 是变长编码" in system
    assert "[2]《乱码排查》：乱码来自字符集不匹配" in system


def test_build_prompt_combines_char_and_rag():
    docs = [rag.RetrievedDoc("gb-standards", "国标字符集", "", "GB2312 收录 6763 字", 0.9)]
    system, _ = ai_service.build_prompt("中 在 GB2312 吗", "编码对比器", "中", docs)
    assert "U+4E2D" in system  # 字符权威事实
    assert "GB2312 收录 6763 字" in system  # RAG 上下文


def test_format_char_context():
    text = ai_service.format_char_context("中")
    assert "U+4E2D" in text
    assert "E4 B8 AD" in text
    assert "GB2312 收录" in text


# --- RAG：语料与打分 ---


class _FakeDoc:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


def test_load_docs_migrates_canned_answers():
    docs = rag.load_docs()
    ids = {d["id"] for d in docs}
    assert "utf8-bytes" in ids
    assert "greeting" in ids
    assert "oracle-bone" in ids
    assert len(docs) >= 20
    for d in docs:
        assert d["id"] and d["title"] and d["body"]
        assert isinstance(d.get("keywords", []), list)


def test_rank_keeps_similar_and_drops_distant():
    results = [
        (_FakeDoc("很近的资料", {"id": "a", "title": "A", "page": "", "keywords": []}), 0.2),  # sim 0.8
        (_FakeDoc("无关的资料", {"id": "b", "title": "B", "page": "", "keywords": []}), 0.9),  # sim 0.1
    ]
    ranked = rag._rank(results, "任意问题", threshold=0.35)
    assert [d.id for d in ranked] == ["a"]


def test_rank_keyword_boost_rescues_match():
    results = [
        (_FakeDoc("UTF-8 是变长编码", {"id": "u", "title": "T", "page": "", "keywords": ["UTF-8"]}), 0.9),
    ]
    # 无关键词时 sim 0.1 会被过滤；命中关键词后 0.1+0.45=0.55 ≥ 阈值。
    assert [d.id for d in rag._rank(results, "UTF-8 为什么", threshold=0.35)] == ["u"]
    assert rag._rank(results, "天气如何", threshold=0.35) == []


def test_rank_sorts_by_score_desc():
    results = [
        (_FakeDoc("次相关", {"id": "low", "title": "", "page": "", "keywords": []}), 0.6),   # sim 0.4
        (_FakeDoc("最相关", {"id": "top", "title": "", "page": "", "keywords": []}), 0.1),   # sim 0.9
    ]
    ranked = rag._rank(results, "任意", threshold=0.35)
    assert [d.id for d in ranked] == ["top", "low"]
