"""学习统计与收藏（M4）业务逻辑。"""
from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.favorite import Favorite
from app.models.user_stats import UserStats


def get_stats(db: Session, user_id: int) -> UserStats | None:
    return db.get(UserStats, user_id)


def record_activity(db: Session, user_id: int, kind: str) -> UserStats:
    """记录一次学习行为，按 UTC 日期更新连续学习天数（streak）。

    连续规则：同一天多次活动不重复累计；昨天活动过则 +1；隔天则重置为 1。
    """
    stats = db.get(UserStats, user_id)
    if stats is None:
        stats = UserStats(user_id=user_id, scanned=0, encoded=0, streak_days=0)
        db.add(stats)

    today = date.today()
    last = stats.last_activity_date
    if last == today:
        pass  # 今天已有活动，连续天数不变
    elif last == today - timedelta(days=1):
        stats.streak_days += 1
    else:
        stats.streak_days = 1
    stats.last_activity_date = today

    if kind == "scan":
        stats.scanned += 1
    else:
        stats.encoded += 1

    db.commit()
    db.refresh(stats)
    return stats


def list_favorites(db: Session, user_id: int) -> list[str]:
    return list(
        db.scalars(
            select(Favorite.char)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at, Favorite.id)
        )
    )


def add_favorite(db: Session, user_id: int, char: str) -> list[str]:
    exists = db.scalar(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.char == char)
    )
    if exists is None:
        db.add(Favorite(user_id=user_id, char=char))
        db.commit()
    return list_favorites(db, user_id)


def remove_favorite(db: Session, user_id: int, char: str) -> list[str]:
    db.execute(
        delete(Favorite).where(Favorite.user_id == user_id, Favorite.char == char)
    )
    db.commit()
    return list_favorites(db, user_id)
