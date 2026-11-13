"""AI 对话（Phase 3 M1）测试：SSE 通道 / prompt 组装 / 无密钥 / 空问题。全程 mock LLM，不发真实网络请求。"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import ai as ai_service

API = "/api/v1"


class _Settings:
    def __init__(self, **kw):
        self.ai_enabled = kw.get("ai_enabled", True)
        self.deepseek_api_key = kw.get("deepseek_api_key", "sk-test")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _patch_settings(monkeypatch, **kw):
    monkeypatch.setattr("app.api.routes.ai.get_settings", lambda: _Settings(**kw))


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


def test_streams_tokens(client, monkeypatch):
    async def fake_stream(question, page, char):
        yield "你好"
        yield "，世界"

    monkeypatch.setattr("app.api.routes.ai.ai_service.stream_reply", fake_stream)
    _patch_settings(monkeypatch)

    with client.stream("POST", f"{API}/ai/chat", json={"question": "你好"}) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())

    assert 'data: {"type": "token", "text": "你好"}' in body
    assert 'data: {"type": "token", "text": "，世界"}' in body
    assert 'data: {"type": "done"}' in body


def test_build_prompt_injects_char_facts():
    system, user = ai_service.build_prompt("它是什么？", "编码对比器", "中")
    assert "U+4E2D" in system
    assert "编码对比器" in system
    assert user == "它是什么？"


def test_format_char_context():
    text = ai_service.format_char_context("中")
    assert "U+4E2D" in text
    assert "E4 B8 AD" in text
    assert "GB2312 收录" in text
