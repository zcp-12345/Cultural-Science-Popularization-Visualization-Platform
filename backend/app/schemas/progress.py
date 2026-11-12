"""学习统计与收藏（M4）请求/响应模型。"""
from typing import Literal

from pydantic import field_validator

from app.schemas.common import CamelModel


class UserStatsOut(CamelModel):
    """与前端 `src/types/user.ts` 的 UserStats 1:1。"""

    scanned: int = 0
    encoded: int = 0
    streak_days: int = 0


class ActivityIn(CamelModel):
    kind: Literal["scan", "encode"]


class FavoriteIn(CamelModel):
    char: str

    @field_validator("char")
    @classmethod
    def _single_char(cls, value: str) -> str:
        if len(value) != 1:
            raise ValueError("收藏对象必须是单个字符")
        return value


class FavoritesOut(CamelModel):
    items: list[str]
