"""注册 / 登录 / 刷新 / 登出。"""
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginIn, RegisterIn, TokenPair
from app.schemas.user import UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
_COOKIE_PATH = "/api/v1/auth"


def _user_out(user: User) -> UserOut:
    return UserOut(
        id=str(user.id),
        name=user.name,
        email=user.email,
        joined_at=user.joined_at,
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=token,
        max_age=settings.jwt_refresh_ttl_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=_COOKIE_PATH,
    )


def _get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.strip().lower()
    if _get_by_email(db, email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该邮箱已注册，请直接登录")

    user = User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_refresh_cookie(response, create_refresh_token(user.id))
    return AuthResponse(
        access_token=create_access_token(user.id),
        token_type="bearer",
        user=_user_out(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.strip().lower()
    user = _get_by_email(db, email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")

    _set_refresh_cookie(response, create_refresh_token(user.id))
    return AuthResponse(
        access_token=create_access_token(user.id),
        token_type="bearer",
        user=_user_out(user),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)) -> TokenPair:
    cookie = request.cookies.get(REFRESH_COOKIE)
    if not cookie:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="缺少刷新凭证，请重新登录")
    try:
        user_id = decode_token(cookie, "refresh")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新凭证已失效，请重新登录")

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    # 旋转 refresh token，避免长期复用同一凭证
    _set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenPair(access_token=create_access_token(user.id), token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout() -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(key=REFRESH_COOKIE, path=_COOKIE_PATH)
    return response
