"""AI 对话请求模型（camelCase，与前端 `AiContext` 对齐）。"""
from app.schemas.common import CamelModel


class ChatRequest(CamelModel):
    question: str
    page: str = ""
    char: str | None = None
