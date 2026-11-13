"""按客户端 IP 的滑动窗口限流（内存实现）。

Phase 4。`/ai/chat` 不强制鉴权，故以来源 IP 作限流键；单进程 uvicorn 下内存字典足够，
无需引入 Redis。时间用 `time.monotonic()`（单调时钟，不受系统时间回拨影响）。

- `allow(ip, limit, window, now=None)` 纯函数，`now` 可注入便于确定性单测。
- `reset()` 清空计数，供测试隔离。
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from app.core.config import get_settings

_lock = threading.Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def client_ip(request, settings=None) -> str:
    """从请求里解析客户端 IP；反向代理后优先取 X-Forwarded-For 的首个地址。

    `settings` 可注入（测试用），默认取 `get_settings()`。
    """
    settings = settings or get_settings()
    if settings.ai_rate_limit_trust_xff:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def allow(ip: str, limit: int, window: float, now: float | None = None) -> bool:
    """记录一次访问并判断是否放行；超过窗口内次数上限返回 False。"""
    if limit <= 0:
        return True
    now = time.monotonic() if now is None else now
    with _lock:
        q = _hits[ip]
        # 弹出窗口之外的旧记录（滑动窗口）
        while q and now - q[0] >= window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True


def reset() -> None:
    """清空所有计数（测试隔离用）。"""
    with _lock:
        _hits.clear()
