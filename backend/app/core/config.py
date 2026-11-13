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

    # AI 层（Phase 3）
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    ai_enabled: bool = True

    # RAG（Phase 3 M2）
    rag_top_k: int = 3
    # 检索相似度阈值（cosine，含关键词加分；低于此值视为未命中并拒答）。
    rag_sim_threshold: float = 0.35
    kb_source: str = "app/kb/docs.json"
    kb_eval_source: str = "app/kb/eval.json"
    kb_persist_dir: str = "./chroma_db"

    # 云端 embedding（Phase 4）：provider 为 "cloud" 且配了 key 时用 OpenAI 兼容接口（默认硅基流动），
    # 否则回退本地 fastembed。切换 provider 后需删除 chroma_db 重建索引（维度不同）。
    embedding_provider: str = "local"  # "local" | "cloud"
    embedding_api_base: str = "https://api.siliconflow.cn/v1"
    embedding_api_key: str = ""
    embedding_model: str = "BAAI/bge-m3"

    # 限流（Phase 4）：/ai/chat 按 IP 滑动窗口限流。requests<=0 表示不限流。
    ai_rate_limit_requests: int = 10
    ai_rate_limit_window_seconds: int = 60
    # 反向代理后是否信任 X-Forwarded-For 取真实客户端 IP。
    ai_rate_limit_trust_xff: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
