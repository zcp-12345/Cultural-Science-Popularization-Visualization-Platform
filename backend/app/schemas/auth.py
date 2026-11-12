"""鉴权请求/响应模型。"""
from pydantic import Field, field_validator

from app.schemas.common import CamelModel
from app.schemas.user import UserOut


class RegisterIn(CamelModel):
    name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)

    @field_validator("email")
    @classmethod
    def _email_format(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("邮箱格式不正确")
        return value


class LoginIn(CamelModel):
    email: str
    password: str


class TokenPair(CamelModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(TokenPair):
    user: UserOut
