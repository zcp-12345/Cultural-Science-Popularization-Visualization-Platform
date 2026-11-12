"""学习统计与收藏（M4）。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.progress import ActivityIn, FavoriteIn, FavoritesOut, UserStatsOut
from app.services import progress

router = APIRouter(prefix="/users/me", tags=["progress"])


@router.get("/stats", response_model=UserStatsOut)
def get_stats(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserStatsOut:
    stats = progress.get_stats(db, user.id)
    if stats is None:
        return UserStatsOut(scanned=0, encoded=0, streak_days=0)
    return UserStatsOut(
        scanned=stats.scanned, encoded=stats.encoded, streak_days=stats.streak_days
    )


@router.post("/stats/activity", response_model=UserStatsOut)
def record_activity(
    payload: ActivityIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserStatsOut:
    stats = progress.record_activity(db, user.id, payload.kind)
    return UserStatsOut(
        scanned=stats.scanned, encoded=stats.encoded, streak_days=stats.streak_days
    )


@router.get("/favorites", response_model=FavoritesOut)
def list_favorites(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> FavoritesOut:
    return FavoritesOut(items=progress.list_favorites(db, user.id))


@router.post("/favorites", response_model=FavoritesOut)
def add_favorite(
    payload: FavoriteIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoritesOut:
    return FavoritesOut(items=progress.add_favorite(db, user.id, payload.char))


@router.delete("/favorites/{char}", response_model=FavoritesOut)
def remove_favorite(
    char: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FavoritesOut:
    return FavoritesOut(items=progress.remove_favorite(db, user.id, char))
