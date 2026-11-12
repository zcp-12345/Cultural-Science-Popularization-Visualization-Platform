"""用户响应模型（与前端 `src/types/user.ts` 的 UserProfile 1:1）。"""
from datetime import datetime

from app.schemas.common import CamelModel


class UserOut(CamelModel):
    id: str
    name: str
    email: str
    joined_at: datetime
