"""学习统计与收藏（M4）端到端测试。"""
from datetime import date, timedelta
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

API = "/api/v1"
REGISTER = {"name": "测试用户", "email": "test@example.com", "password": "secret123"}


@pytest.fixture()
def client():
    # 每次测试用独立的内存 SQLite，避免污染 dev.db。
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def _register(client) -> str:
    r = client.post(f"{API}/auth/register", json=REGISTER)
    assert r.status_code == 201
    return r.json()["accessToken"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---- 统计 ----

def test_stats_default_zero(client):
    token = _register(client)
    r = client.get(f"{API}/users/me/stats", headers=_auth(token))
    assert r.status_code == 200
    assert r.json() == {"scanned": 0, "encoded": 0, "streakDays": 0}


def test_stats_requires_auth(client):
    assert client.get(f"{API}/users/me/stats").status_code == 401


def test_record_scan_and_encode(client):
    token = _register(client)
    h = _auth(token)

    r1 = client.post(f"{API}/users/me/stats/activity", json={"kind": "scan"}, headers=h)
    assert r1.status_code == 200
    assert r1.json() == {"scanned": 1, "encoded": 0, "streakDays": 1}

    # 同一天第二次活动：计数累加，连续天数不变
    r2 = client.post(f"{API}/users/me/stats/activity", json={"kind": "scan"}, headers=h)
    assert r2.json() == {"scanned": 2, "encoded": 0, "streakDays": 1}

    r3 = client.post(f"{API}/users/me/stats/activity", json={"kind": "encode"}, headers=h)
    assert r3.json() == {"scanned": 2, "encoded": 1, "streakDays": 1}


def test_record_rejects_bad_kind(client):
    token = _register(client)
    r = client.post(
        f"{API}/users/me/stats/activity", json={"kind": "explode"}, headers=_auth(token)
    )
    assert r.status_code == 422


def test_streak_increments_and_resets():
    """直接调用 service 校验连续学习天数：+1 → 隔天重置。"""
    from app.models.user import User
    from app.models.user_stats import UserStats
    from app.services import progress

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine)()

    user = User(name="u", email="streak@example.com", password_hash="x")
    db.add(user)
    db.commit()

    assert progress.record_activity(db, user.id, "scan").streak_days == 1

    # 拨回昨天 → 连续天数 +1
    stats = db.get(UserStats, user.id)
    stats.last_activity_date = date.today() - timedelta(days=1)
    db.commit()
    assert progress.record_activity(db, user.id, "scan").streak_days == 2

    # 隔了一天 → 重置为 1
    stats = db.get(UserStats, user.id)
    stats.last_activity_date = date.today() - timedelta(days=3)
    db.commit()
    assert progress.record_activity(db, user.id, "encode").streak_days == 1
    db.close()


# ---- 收藏 ----

def test_favorites_default_empty(client):
    token = _register(client)
    r = client.get(f"{API}/users/me/favorites", headers=_auth(token))
    assert r.status_code == 200
    assert r.json() == {"items": []}


def test_favorites_require_auth(client):
    assert client.get(f"{API}/users/me/favorites").status_code == 401
    assert client.post(f"{API}/users/me/favorites", json={"char": "中"}).status_code == 401


def test_add_list_remove_favorite(client):
    token = _register(client)
    h = _auth(token)

    r = client.post(f"{API}/users/me/favorites", json={"char": "中"}, headers=h)
    assert r.json() == {"items": ["中"]}

    # 重复收藏不产生重复项
    r = client.post(f"{API}/users/me/favorites", json={"char": "中"}, headers=h)
    assert r.json() == {"items": ["中"]}

    r = client.post(f"{API}/users/me/favorites", json={"char": "龍"}, headers=h)
    assert r.json() == {"items": ["中", "龍"]}

    # 代理对字符（𠮷）也可收藏
    r = client.post(f"{API}/users/me/favorites", json={"char": "𠮷"}, headers=h)
    assert r.json() == {"items": ["中", "龍", "𠮷"]}

    r = client.delete(f"{API}/users/me/favorites/{quote('中')}", headers=h)
    assert r.json() == {"items": ["龍", "𠮷"]}


def test_favorite_rejects_non_single_char(client):
    token = _register(client)
    r = client.post(f"{API}/users/me/favorites", json={"char": "中华"}, headers=_auth(token))
    assert r.status_code == 422


def test_favorites_are_per_user(client):
    token_a = _register(client)
    client.cookies.clear()
    r = client.post(
        f"{API}/auth/register",
        json={"name": "另一个", "email": "other@example.com", "password": "secret123"},
    )
    token_b = r.json()["accessToken"]

    client.post(f"{API}/users/me/favorites", json={"char": "中"}, headers=_auth(token_a))
    # B 的收藏列表不受 A 影响
    rb = client.get(f"{API}/users/me/favorites", headers=_auth(token_b))
    assert rb.json() == {"items": []}
