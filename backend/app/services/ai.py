"""AI 层：LangChain ChatDeepSeek 流式对话 + prompt 组装。

Phase 3 M1 只做「DeepSeek 直连 + 当前字符权威数据注入」，RAG 检索在 M2 接入。
"""
from __future__ import annotations

from collections.abc import AsyncGenerator

from app.core.config import get_settings
from app.services import encoding

SYSTEM_BASE = (
    "你是「数字考古透视镜」的 AI 考古助手，面向公众科普汉字编码与字形演变。"
    "只回答与汉字编码（Unicode / UTF-8 / GB2312 / GBK / Big5）、字形演变（甲骨文到楷书）"
    "以及本产品功能相关的问题。回答要简洁准确、口语化，约 200 字以内。"
    "如果基于给定资料回答，请标注来源 [n]；资料没有相关信息就明确说不知道，不要编造。"
)

# 多轮记忆（Phase 4）：只带最近 N 条历史，且单条截断，避免 prompt 无限膨胀。
HISTORY_MAX_MESSAGES = 6
HISTORY_MAX_CHARS = 500


def format_char_context(char: str) -> str:
    """用后端权威 `describe_char` 结果，生成注入 prompt 的字符事实。"""
    desc = encoding.describe_char(char)
    legacy = desc.legacy

    def mark(available: bool) -> str:
        return "收录" if available else "未收录"

    facts = [
        f"Unicode 码位 U+{desc.unicode_hex}",
        f"UTF-8 字节 {desc.utf8.text}（{len(desc.utf8.bytes)} 字节）",
        f"GB2312 {mark(legacy.gb2312.available)}",
        f"GBK {mark(legacy.gbk.available)}",
        f"Big5 {mark(legacy.big5.available)}",
    ]
    return f"最近扫描字符「{char}」的权威编码数据：{'；'.join(facts)}。"


def format_rag_context(docs) -> str:
    """把检索命中的片段格式化为带编号的资料块，供 prompt 注入。"""
    lines = []
    for i, doc in enumerate(docs, 1):
        lines.append(f"[{i}]《{doc.title}》：{doc.body}")
    return "\n".join(lines)


def build_prompt(
    question: str,
    page: str,
    char: str | None,
    docs: list | None = None,
) -> tuple[str, str]:
    """组装 (system, user) 两条消息。纯函数，便于单测。

    `docs` 为 RAG 检索命中的片段（`rag.RetrievedDoc` 列表）；为空则不加 RAG 上下文。
    """
    system = SYSTEM_BASE
    if page:
        system += f" 用户当前页面：{page}。"
    if char and len(char) == 1:
        system += f" {format_char_context(char)}"
    if docs:
        system += (
            " 以下是知识库检索到的权威资料，请只依据它们回答并标注来源编号 [n]：\n"
            + format_rag_context(docs)
        )
    return system, question


def build_history_messages(history: list | None) -> list:
    """把前端带回的最近几轮对话转成 LangChain 消息序列（按时间顺序，截断条数与长度）。

    纯函数，便于单测。`history` 元素可为 `schemas.ai.ChatTurn`（pydantic）或 dict。
    """
    from langchain_core.messages import AIMessage, HumanMessage

    messages: list = []
    for turn in (history or [])[-HISTORY_MAX_MESSAGES:]:
        if isinstance(turn, dict):
            role = turn.get("role")
            content = turn.get("content")
        else:
            role = getattr(turn, "role", None)
            content = getattr(turn, "content", None)
        content = (content or "").strip()[:HISTORY_MAX_CHARS]
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    return messages


def _build_llm(settings):
    """懒加载构造 ChatDeepSeek，避免未装 AI 依赖时拖垮整个后端 import。"""
    try:
        from langchain_deepseek import ChatDeepSeek
    except ImportError as exc:  # pragma: no cover - 由 /ai/chat 的 503 兜住
        raise RuntimeError("AI 依赖未安装（langchain-deepseek）") from exc

    kwargs = dict(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        temperature=0.3,
        max_tokens=800,
        streaming=True,
    )
    # langchain-deepseek 不同版本对 base url 参数名不同（api_base / base_url），逐个尝试。
    try:
        return ChatDeepSeek(**kwargs, base_url=settings.deepseek_base_url)
    except TypeError:
        return ChatDeepSeek(**kwargs, api_base=settings.deepseek_base_url)


def _chunk_text(chunk) -> str:
    content = chunk.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return ""


async def stream_reply(
    question: str,
    page: str,
    char: str | None,
    docs: list | None = None,
    llm=None,
    history: list | None = None,
) -> AsyncGenerator[str, None]:
    """把一条提问变成 DeepSeek 的增量文本流。

    `docs` 为 RAG 检索命中片段，注入 prompt 作为权威资料；`llm` 可注入假对象（测试用）；
    `history` 为前端带回的最近几轮对话（`schemas.ai.ChatTurn` 列表或 dict 列表），
    按时间顺序注入到当前提问之前，实现多轮上下文。
    """
    if llm is None:
        llm = _build_llm(get_settings())

    from langchain_core.messages import HumanMessage, SystemMessage

    system, user = build_prompt(question, page, char, docs)
    messages = [SystemMessage(content=system), *build_history_messages(history)]
    messages.append(HumanMessage(content=user))

    async for chunk in llm.astream(messages):
        text = _chunk_text(chunk)
        if text:
            yield text
