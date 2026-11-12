"""应用配置（pydantic-settings，从环境变量 / .env 读取）。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "数字考古透视镜 API"
    api_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./dev.db"

    # 鉴权（M3 启用）
    jwt_secret: str = "change-me"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7
    # refresh cookie 是否带 Secure 标记：本地 http 开发置 False，生产 https 置 True。
    cookie_secure: bool = False

    # 允许的前端来源（CORS）。如需用环境变量覆盖，请传 JSON 数组字符串。
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
