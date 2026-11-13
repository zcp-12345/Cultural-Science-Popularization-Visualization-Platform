"""AI 对话（Phase 3 M1）：POST /ai/chat 以 SSE 流式返回 DeepSeek 增量文本。"""
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.config import get_settings
from app.schemas.ai import ChatRequest
from app.services import ai as ai_service
from app.services import rag, rate_limit

router = APIRouter(prefix="/ai", tags=["ai"])


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _sources_event(docs) -> str:
    """把 RAG 命中片段转成 sources 事件（引用 UI 用；顺序即 [n] 编号，与 token 内标注对应）。"""
    items = [{"id": d.id, "title": d.title, "page": d.page} for d in docs]
    return _sse({"type": "sources", "items": items})


def _enforce_rate_limit(request: Request, settings) -> None:
    """/ai/chat 不鉴权，以来源 IP 做滑动窗口限流（超限返回 429）。"""
    limit = settings.ai_rate_limit_requests
    if limit <= 0:
        return
    ip = rate_limit.client_ip(request, settings)
    if not rate_limit.allow(ip, limit, settings.ai_rate_limit_window_seconds):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")


@router.post("/chat")
async def chat(payload: ChatRequest, request: Request) -> StreamingResponse:
    settings = get_settings()
    _enforce_rate_limit(request, settings)

    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    if not settings.ai_enabled or not settings.deepseek_api_key:
        raise HTTPException(status_code=503, detail="AI 服务未启用")

    async def event_stream():
        try:
            docs = rag.retrieve(question[:500], top_k=settings.rag_top_k)
            if not docs:
                yield _sse({"type": "token", "text": rag.REFUSAL})
                yield _sse({"type": "done"})
                return
            yield _sources_event(docs)
            async for text in ai_service.stream_reply(
                question[:500],
                payload.page,
                payload.char,
                docs=docs,
                history=payload.history,
            ):
                yield _sse({"type": "token", "text": text})
            yield _sse({"type": "done"})
        except Exception:
            yield _sse({"type": "token", "text": "\n\n（生成中断，请重试）"})
            yield _sse({"type": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
