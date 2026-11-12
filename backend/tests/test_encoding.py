"""编码权威源测试：对照 Python codecs 金标准 + 结构断言。

金标准来自 `frontend/src/data/encoding-gold.json`（由
`frontend/scripts/generate_encoding_gold.py` 用 Python codecs 生成），
后端 `app/services/encoding.py` 以同一 codecs 口径实现，逐字对齐。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.encoding import describe_char, summarize_text

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLD_PATH = REPO_ROOT / "frontend" / "src" / "data" / "encoding-gold.json"

_gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
CHARACTERS = _gold["characters"]


def _hex(data: list[int] | None) -> str | None:
    if data is None:
        return None
    return " ".join(f"{b:02X}" for b in data)


@pytest.mark.parametrize(
    "entry",
    CHARACTERS,
    ids=[entry["char"] for entry in CHARACTERS],
)
def test_describe_char_matches_gold(entry: dict) -> None:
    d = describe_char(entry["char"])

    assert d.utf8.text == entry["utf8"]
    assert _hex(d.utf16.bytes_le) == entry["utf16le"]
    assert _hex(d.utf16.bytes_be) == entry["utf16be"]
    assert _hex(d.legacy.gb2312.bytes) == entry["gb2312"]
    assert _hex(d.legacy.gbk.bytes) == entry["gbk"]
    assert _hex(d.legacy.big5.bytes) == entry["big5"]

    # 码位解析：U+4E2D → 0x4E2D（含扩展 B 区 U+20BB7 的五位十六进制）
    assert d.code_point == int(entry["codePoint"][2:], 16)


def test_describe_char_zhong_structure() -> None:
    d = describe_char("中")

    assert d.code_point == 0x4E2D
    assert d.unicode_hex == "4E2D"
    assert d.utf8.bytes == [0xE4, 0xB8, 0xAD]
    assert [p.marker for p in d.utf8.parts] == ["1110", "10", "10"]
    assert len(d.utf16.units) == 1
    assert d.utf16.is_surrogate_pair is False
    assert d.legacy.gb2312.bytes == [0xD6, 0xD0]
    assert d.legacy.gbk.bytes == [0xD6, 0xD0]
    assert d.legacy.big5.bytes == [0xA4, 0xA4]
    assert "CJK" in d.block


def test_describe_char_surrogate_pair() -> None:
    d = describe_char("𠮷")

    assert d.code_point == 0x20BB7
    assert d.utf8.bytes == [0xF0, 0xA0, 0xAE, 0xB7]
    assert [p.marker for p in d.utf8.parts] == ["11110", "10", "10", "10"]
    assert d.utf16.is_surrogate_pair is True
    assert d.utf16.units[0].hex == "D842"
    assert d.utf16.units[1].hex == "DFB7"
    assert d.legacy.gbk.available is False
    assert "扩展 B" in d.block


def test_ascii_single_byte() -> None:
    d = describe_char("A")

    assert d.utf8.bytes == [0x41]
    assert d.utf8.parts[0].marker == "0"
    assert d.legacy.gb2312.bytes == [0x41]
    assert d.legacy.gbk.bytes == [0x41]
    assert d.legacy.big5.bytes == [0x41]


def test_gbk_extension_vs_gb2312() -> None:
    d = describe_char("镕")

    assert d.legacy.gbk.available is True
    assert d.legacy.gb2312.available is False
    assert d.legacy.gb2312.note is not None


def test_big5_simplified_vs_traditional() -> None:
    assert describe_char("码").legacy.big5.available is False
    assert describe_char("龍").legacy.big5.available is True
    assert describe_char("龍").legacy.gb2312.available is False


def test_summarize_text() -> None:
    summary = summarize_text("中码A")

    assert summary.utf8.bytes == 3 + 3 + 1
    assert summary.utf16.bytes == 2 + 2 + 2
    assert summary.gb2312.covered == 3
    assert summary.gb2312.missing == []
    assert summary.big5.covered == 2
    assert summary.big5.missing == ["码"]


def test_summarize_empty() -> None:
    summary = summarize_text("")

    assert summary.utf8.total == 0
    assert summary.utf8.bytes == 0
    assert summary.gbk.covered == 0
