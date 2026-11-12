"""API 路由聚合，统一挂在 /api/v1 前缀下。"""
from fastapi import APIRouter

from app.api.routes import auth, encoding, health, progress, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(encoding.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(progress.router)
