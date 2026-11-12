"""导入所有模型，供 create_all 建表。"""
from app.models.favorite import Favorite
from app.models.user import User
from app.models.user_stats import UserStats

__all__ = ["User", "UserStats", "Favorite"]
