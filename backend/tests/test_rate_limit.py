"""限流器（Phase 4）：滑动窗口纯函数 + 客户端 IP 解析。"""
from app.services import rate_limit


class _Req:
    def __init__(self, host="1.2.3.4", xff=None):
        self.client = type("C", (), {"host": host})()
        self.headers = {"x-forwarded-for": xff} if xff else {}


class _Settings:
    def __init__(self, trust_xff=True):
        self.ai_rate_limit_trust_xff = trust_xff


def test_allow_within_window():
    rate_limit.reset()
    assert rate_limit.allow("a", limit=2, window=10, now=0) is True
    assert rate_limit.allow("a", limit=2, window=10, now=1) is True
    assert rate_limit.allow("a", limit=2, window=10, now=2) is False  # 第 3 次超限


def test_allow_window_slides():
    rate_limit.reset()
    rate_limit.allow("a", limit=1, window=10, now=0)
    # 窗口外（now=10 恰好滑出）后放行
    assert rate_limit.allow("a", limit=1, window=10, now=10) is True


def test_allow_disabled_when_limit_zero():
    rate_limit.reset()
    assert rate_limit.allow("a", limit=0, window=10, now=0) is True
    assert rate_limit.allow("a", limit=0, window=10, now=0) is True


def test_client_ip_uses_xff_first():
    assert rate_limit.client_ip(_Req(host="10.0.0.1", xff="9.9.9.9, 8.8.8.8"), _Settings(True)) == "9.9.9.9"


def test_client_ip_falls_back_to_client_host():
    assert rate_limit.client_ip(_Req(host="10.0.0.1"), _Settings(True)) == "10.0.0.1"


def test_client_ip_ignores_xff_when_disabled():
    assert rate_limit.client_ip(_Req(host="10.0.0.1", xff="9.9.9.9"), _Settings(False)) == "10.0.0.1"
