"""编码权威源：Python 标准库 `codecs` 实现 describe_char / summarize_text。

字段与前端 `src/services/encoding` 逐位对齐；legacy（GB2312/GBK/Big5）以
Python `codecs` 为准，取代前端 TextDecoder 反向索引 / GB2312 成员集近似。

Big5 口径说明：Python 的 `big5` 为传统 Big5（不含 HKSCS），但包含 A1 标点行
（如 ¥=A2 44、•=A1 45），与浏览器 WHATWG `big5` 存在两处已知分歧，见
`frontend/tests/encoding-gold.test.ts` 的注释。
"""
from __future__ import annotations

from collections.abc import Callable

from app.schemas.encoding import (
    CharDescription,
    EncodingAggregate,
    Legacy,
    LegacyResult,
    TextSummary,
    Utf16,
    Utf16Unit,
    Utf8,
    Utf8BytePart,
)

# --- Unicode 区段表（移植自前端 src/services/encoding/unicodeBlocks.ts）---

BLOCKS: list[tuple[int, int, str]] = [
    (0x0000, 0x007F, "基本拉丁字母（ASCII）"),
    (0x0080, 0x00FF, "拉丁字母补充"),
    (0x2000, 0x206F, "通用标点"),
    (0x2190, 0x21FF, "箭头"),
    (0x2E80, 0x2EFF, "CJK 部首补充"),
    (0x2F00, 0x2FDF, "康熙部首"),
    (0x3000, 0x303F, "CJK 符号和标点"),
    (0x3400, 0x4DBF, "CJK 统一表意文字扩展 A"),
    (0x4E00, 0x9FFF, "CJK 统一表意文字（基本区）"),
    (0xF900, 0xFAFF, "CJK 兼容表意文字"),
    (0xFF00, 0xFFEF, "半角及全角形式"),
    (0x20000, 0x2A6DF, "CJK 统一表意文字扩展 B"),
    (0x2A700, 0x2B73F, "CJK 统一表意文字扩展 C"),
    (0x2B740, 0x2B81F, "CJK 统一表意文字扩展 D"),
    (0x2B820, 0x2CEAF, "CJK 统一表意文字扩展 E"),
    (0x2CEB0, 0x2EBEF, "CJK 统一表意文字扩展 F"),
    (0x30000, 0x3134F, "CJK 统一表意文字扩展 G"),
    (0x31350, 0x323AF, "CJK 统一表意文字扩展 H"),
]

PLANE_NAMES = [
    "基本多文种平面（BMP）",
    "第一辅助平面（SMP）",
    "第二表意文字平面（SIP）",
    "第三表意文字平面（TIP）",
]


def unicode_block_of(cp: int) -> str:
    for start, end, name in BLOCKS:
        if start <= cp <= end:
            return name
    return f"未收录区段 U+{cp:X}"


def plane_name_of(plane: int) -> str:
    if plane < len(PLANE_NAMES):
        return PLANE_NAMES[plane]
    return f"第 {plane + 1} 平面"


def _format_hex_bytes(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def _utf16_units(cp: int) -> list[Utf16Unit]:
    def unit(value: int) -> Utf16Unit:
        return Utf16Unit(value=value, hex=f"{value:04X}", binary=f"{value:016b}")

    if cp <= 0xFFFF:
        return [unit(cp)]
    # 代理对：U+10000..U+10FFFF
    v = cp - 0x10000
    return [unit(0xD800 + (v >> 10)), unit(0xDC00 + (v & 0x3FF))]


def _utf8_parts(data: bytes) -> list[Utf8BytePart]:
    parts: list[Utf8BytePart] = []
    n = len(data)
    for index, byte in enumerate(data):
        binary = f"{byte:08b}"
        marker_length = (1 if n == 1 else n + 1) if index == 0 else 2
        parts.append(
            Utf8BytePart(
                byte=byte,
                binary=binary,
                marker=binary[:marker_length],
                data=binary[marker_length:],
                is_continuation=index > 0,
            )
        )
    return parts


def _gb2312_result(char: str) -> LegacyResult:
    try:
        data = char.encode("gb2312")
    except UnicodeEncodeError:
        try:
            char.encode("gbk")
        except UnicodeEncodeError:
            note = "不在 GBK 字符集内，因此也不在 GB2312 内"
        else:
            note = "位于 GBK 扩展区，GB2312 未收录"
        return LegacyResult(bytes=None, available=False, note=note)

    if len(data) == 1:
        return LegacyResult(
            bytes=list(data), available=True, note="ASCII 单字节，GB2312 与 GBK 共用"
        )
    return LegacyResult(bytes=list(data), available=True)


def _gbk_result(char: str) -> LegacyResult:
    try:
        data = char.encode("gbk")
    except UnicodeEncodeError:
        return LegacyResult(bytes=None, available=False, note="不在 GBK 字符集内")
    return LegacyResult(bytes=list(data), available=True)


def _big5_result(char: str) -> LegacyResult:
    try:
        data = char.encode("big5")
    except UnicodeEncodeError:
        return LegacyResult(
            bytes=None, available=False, note="不在 Big5 字符集内（Big5 以繁体字为主）"
        )
    return LegacyResult(bytes=list(data), available=True)


def describe_char(char: str) -> CharDescription:
    """描述单个 Unicode 码位在各编码下的字节形态。`char` 必须是单个码位。"""
    cp = ord(char)

    utf8_data = char.encode("utf-8")
    utf16_le = char.encode("utf-16-le")
    utf16_be = char.encode("utf-16-be")
    units = _utf16_units(cp)

    return CharDescription(
        char=char,
        code_point=cp,
        unicode_hex=f"{cp:04X}",
        binary=f"{cp:0{16 if cp <= 0xFFFF else 21}b}",
        plane=cp >> 16,
        plane_name=plane_name_of(cp >> 16),
        block=unicode_block_of(cp),
        utf8=Utf8(
            bytes=list(utf8_data),
            text=_format_hex_bytes(utf8_data),
            parts=_utf8_parts(utf8_data),
        ),
        utf16=Utf16(
            units=units,
            bytes_le=list(utf16_le),
            bytes_be=list(utf16_be),
            is_surrogate_pair=len(units) == 2,
        ),
        legacy=Legacy(
            gb2312=_gb2312_result(char),
            gbk=_gbk_result(char),
            big5=_big5_result(char),
        ),
    )


def summarize_text(text: str) -> TextSummary:
    """整段文本的编码汇总（UTF-8 / UTF-16 / GB2312 / GBK / Big5）。"""
    descriptions = [describe_char(ch) for ch in text]

    def aggregate(
        label: str, get_bytes: Callable[[CharDescription], list[int] | None]
    ) -> EncodingAggregate:
        total_bytes = 0
        covered = 0
        missing: list[str] = []
        for description in descriptions:
            value = get_bytes(description)
            if value:
                total_bytes += len(value)
                covered += 1
            else:
                missing.append("空格" if description.char.strip() == "" else description.char)
        return EncodingAggregate(
            label=label,
            bytes=total_bytes,
            covered=covered,
            total=len(descriptions),
            missing=missing,
        )

    return TextSummary(
        utf8=aggregate("UTF-8", lambda d: d.utf8.bytes),
        utf16=aggregate("UTF-16", lambda d: d.utf16.bytes_le),
        gb2312=aggregate("GB2312", lambda d: d.legacy.gb2312.bytes),
        gbk=aggregate("GBK", lambda d: d.legacy.gbk.bytes),
        big5=aggregate("Big5", lambda d: d.legacy.big5.bytes),
    )
