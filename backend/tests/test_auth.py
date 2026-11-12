"""用户系统（M3）端到端测试：注册 / 登录 / 刷新 / 登出 / 当前用户。"""
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


def test_register_success(client):
    r = client.post(f"{API}/auth/register", json=REGISTER)
    assert r.status_code == 201
    body = r.json()
    assert body["accessToken"]
    assert body["tokenType"] == "bearer"
    assert body["user"]["email"] == "test@example.com"
    assert body["user"]["name"] == "测试用户"
    assert body["user"]["id"]
    assert "refresh_token" in client.cookies


def test_register_duplicate_email(client):
    assert client.post(f"{API}/auth/register", json=REGISTER).status_code == 201
    r = client.post(f"{API}/auth/register", json=REGISTER)
    assert r.status_code == 409


def test_register_rejects_bad_email(client):
    r = client.post(f"{API}/auth/register", json={**REGISTER, "email": "not-an-email"})
    assert r.status_code == 422


def test_login_wrong_password(client):
    client.post(f"{API}/auth/register", json=REGISTER)
    r = client.post(
        f"{API}/auth/login",
        json={"email": REGISTER["email"], "password": "wrong-password"},
    )
    assert r.status_code == 401


def test_login_success(client):
    client.post(f"{API}/auth/register", json=REGISTER)
    r = client.post(
        f"{API}/auth/login",
        json={"email": REGISTER["email"], "password": REGISTER["password"]},
    )
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "test@example.com"


def test_me_with_token(client):
    r = client.post(f"{API}/auth/register", json=REGISTER)
    token = r.json()["accessToken"]
    me = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"


def test_me_without_token(client):
    assert client.get(f"{API}/users/me").status_code == 401


def test_refresh_flow(client):
    client.post(f"{API}/auth/register", json=REGISTER)
    r = client.post(f"{API}/auth/refresh")
    assert r.status_code == 200
    assert r.json()["accessToken"]


def test_refresh_token_rejected_as_access(client):
    client.post(f"{API}/auth/register", json=REGISTER)
    refresh = client.cookies.get("refresh_token")
    assert refresh
    r = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {refresh}"})
    assert r.status_code == 401


def test_logout_clears_cookie(client):
    client.post(f"{API}/auth/register", json=REGISTER)
    assert client.post(f"{API}/auth/logout").status_code == 204
    # 登出后 refresh cookie 已清除 → 刷新失败
    assert client.post(f"{API}/auth/refresh").status_code == 401
