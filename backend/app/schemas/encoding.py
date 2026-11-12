"""编码相关请求/响应模型。

字段与前端 `src/types/encoding.ts` 1:1 对齐（camelCase）。
FastAPI 默认 `response_model_by_alias=True`，配合 `alias_generator=to_camel`
即可输出前端可直接 `response.json()` 消费的 JSON。
"""
from __future__ import annotations

from pydantic import Field

from app.schemas.common import CamelModel


class Utf8BytePart(CamelModel):
    byte: int
    binary: str
    marker: str
    data: str
    is_continuation: bool


class Utf8(CamelModel):
    bytes: list[int]
    text: str
    parts: list[Utf8BytePart]


class Utf16Unit(CamelModel):
    value: int
    hex: str
    binary: str


class Utf16(CamelModel):
    units: list[Utf16Unit]
    bytes_le: list[int] = Field(alias="bytesLE")
    bytes_be: list[int] = Field(alias="bytesBE")
    is_surrogate_pair: bool


class LegacyResult(CamelModel):
    bytes: list[int] | None
    available: bool
    note: str | None = None


class Legacy(CamelModel):
    gb2312: LegacyResult
    gbk: LegacyResult
    big5: LegacyResult


class CharDescription(CamelModel):
    char: str
    code_point: int
    unicode_hex: str
    binary: str
    plane: int
    plane_name: str
    block: str
    utf8: Utf8
    utf16: Utf16
    legacy: Legacy


class EncodingAggregate(CamelModel):
    label: str
    bytes: int
    covered: int
    total: int
    missing: list[str]


class TextSummary(CamelModel):
    utf8: EncodingAggregate
    utf16: EncodingAggregate
    gb2312: EncodingAggregate
    gbk: EncodingAggregate
    big5: EncodingAggregate


class DescribeRequest(CamelModel):
    char: str


class SummarizeRequest(CamelModel):
    text: str
