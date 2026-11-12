"""用户学习统计（M4）：扫描/编码计数 + 连续学习天数。"""
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserStats(Base):
    """每个用户一条统计记录（user_id 即主键，1:1 关联 User）。"""

    __tablename__ = "user_stats"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    scanned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    encoded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
