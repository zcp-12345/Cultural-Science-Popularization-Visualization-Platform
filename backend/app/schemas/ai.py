"""AI 对话请求模型（camelCase，与前端 `AiContext` 对齐）。"""
from typing import Literal

from pydantic import Field

from app.schemas.common import CamelModel


class ChatTurn(CamelModel):
    """一轮对话（多轮记忆用）：前端把最近几轮历史随请求带回，后端注入 LLM 消息序列。"""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(CamelModel):
    question: str
    page: str = ""
    char: str | None = None
    history: list[ChatTurn] = Field(default_factory=list)
