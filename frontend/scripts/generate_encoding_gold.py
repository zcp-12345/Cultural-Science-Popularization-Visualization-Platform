#!/usr/bin/env python3
"""用 Python codecs 生成编码金标准 fixture（Phase 2 后端的权威口径）。

产物：
- src/data/encoding-gold.json     教学字的逐字节真值
- src/data/gb2312-characters.json GB2312 可编码字符集合（供前端精确判定）

用法：python scripts/generate_encoding_gold.py
"""
from __future__ import annotations

import json
import platform
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "src" / "data"

# 覆盖：基本区 / 繁体 / 扩展 A / 扩展 B / ASCII / 符号 / emoji
CHARS = list(
    "中龙龍码馬马华華字水龘㐀𠮷日月山川人大 小文音心火木金土雨風风A1¥•😀"
)
# 去掉空白并保序去重
seen: set[str] = set()
chars: list[str] = []
for ch in CHARS:
    if ch.strip() == "":
        continue
    if ch not in seen:
        seen.add(ch)
        chars.append(ch)


def encode(char: str, encoding: str) -> str | None:
    try:
        return char.encode(encoding).hex(" ").upper()
    except (UnicodeEncodeError, LookupError):
        return None


def build_entry(char: str) -> dict[str, str | None]:
    return {
        "char": char,
        "codePoint": f"U+{ord(char):04X}",
        "utf8": encode(char, "utf-8"),
        "utf16le": encode(char, "utf-16-le"),
        "utf16be": encode(char, "utf-16-be"),
        "gb2312": encode(char, "gb2312"),
        "gbk": encode(char, "gbk"),
        "gb18030": encode(char, "gb18030"),
        "big5": encode(char, "big5"),
    }


def dump(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    gold = {
        "generatedBy": f"Python {platform.python_version()} codecs (strict)",
        "note": "GB2312/GBK/Big5 为 Python 标准库口径；浏览器 Big5 含 HKSCS 增补，个别字符可能不同。",
        "characters": [build_entry(char) for char in chars],
    }
    dump(OUT_DIR / "encoding-gold.json", gold)

    gb2312_chars: list[str] = []
    for code_point in range(0x80, 0x10000):  # 跳过 ASCII，代理区编码会报错
        char = chr(code_point)
        try:
            char.encode("gb2312")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        gb2312_chars.append(char)

    dump(
        OUT_DIR / "gb2312-characters.json",
        {
            "generatedBy": f"Python {platform.python_version()} codecs",
            "count": len(gb2312_chars),
            "chars": "".join(gb2312_chars),
        },
    )

    print(f"characters: {len(chars)}")
    print(f"gb2312 characters: {len(gb2312_chars)}")
    print(f"written to: {OUT_DIR}")


if __name__ == "__main__":
    main()
