"""为时间轴构建真实古文字字形 SVG。

读取 config.yaml，把每个 (字, 时期) 解析到 hanzi-glyphs-svg 里的源 SVG
（svg 模式）或 OFL 字体（font 模式），归一化后写入：

  frontend/public/glyphs/{字}/{时期}.svg
  frontend/public/glyphs/manifest.json
  frontend/public/glyphs/CREDITS.md

用法：
  python tools/glyphs/build_glyphs.py
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

from normalize import normalize_svg

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
CONFIG = SCRIPT_DIR / "config.yaml"
REPO = REPO_ROOT / "assets" / "glyphs-src" / "hanzi-glyphs-svg"
FONTS = REPO_ROOT / "assets" / "glyphs-src" / "fonts"
OUT = REPO_ROOT / "frontend" / "public" / "glyphs"

_PAD = 0.06


def load_index(layer: str) -> dict[str, list[dict]]:
    """把 <layer>/index.csv 读成 {modern_char: [行...]}，保持库内顺序。"""
    path = REPO / "glyphs" / layer / "index.csv"
    rows: dict[str, list[dict]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.setdefault(r["modern_char"], []).append(r)
    return rows


def is_jgw_oracle(row: dict) -> bool:
    """甲骨层里 JGW 批是 CC BY 4.0，其余（汉典/小學堂）是 CC0。"""
    return bool((row.get("char_form") or "").strip()) or (
        row.get("source_path", "").startswith("data/")
    )


def extract_font_glyph(ttf: Path, char: str, dst: Path, pad: float = _PAD) -> bool:
    """从 OFL 字体提取单个汉字的轮廓，写成紧凑 viewBox 的 SVG。"""
    font = TTFont(str(ttf))
    try:
        glyph_name = font.getBestCmap().get(ord(char))
        if glyph_name is None:
            return False
        glyphset = font.getGlyphSet()
        glyph = glyphset[glyph_name]

        bp = BoundsPen(glyphset)
        glyph.draw(bp)
        if bp.bounds is None:
            return False
        xmin, ymin, xmax, ymax = bp.bounds
        if xmax <= xmin or ymax <= ymin:
            return False

        sp = SVGPathPen(glyphset)
        glyph.draw(sp)
        d = sp.getCommands()
        if not d:
            return False
    finally:
        font.close()

    w = xmax - xmin
    h = ymax - ymin
    px = w * pad
    py = h * pad
    vb = (xmin - px, ymin - py, w + 2 * px, h + 2 * py)

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vb[0]:.3f} {vb[1]:.3f} {vb[2]:.3f} {vb[3]:.3f}" '
        'preserveAspectRatio="xMidYMid meet" fill="currentColor">\n'
        f'  <path d="{d}"/>\n</svg>\n',
        encoding="utf-8",
    )
    return True


def main() -> int:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    characters = cfg["characters"]
    sources = cfg["sources"]

    indexes = {
        era: load_index(s["layer"])
        for era, s in sources.items()
        if s.get("layer")
    }

    glyphs = []
    for c in characters:
        display = c["char"]
        for era, src in sources.items():
            query = c["query"][era]
            out_file = OUT / display / f"{era}.svg"
            record = {
                "char": display,
                "era": era,
                "queryChar": query,
                "status": "missing",
                "file": None,
                "license": src.get("license"),
                "attribution": src.get("attribution"),
            }
            ok = False
            if src.get("kind") == "svg":
                rows = indexes[era].get(query, [])
                if rows:
                    pick = rows[0]
                    if era == "oracle":
                        cc0 = [r for r in rows if not is_jgw_oracle(r)]
                        if cc0:
                            pick = cc0[0]
                    svg = REPO / "glyphs" / src["layer"] / pick["file"]
                    if svg.exists():
                        normalize_svg(svg, out_file)
                        ok = True
                        record.update(
                            status="real",
                            file=f"{display}/{era}.svg",
                            sourceId=pick.get("glyph_id")
                            or pick.get("codepoint")
                            or pick.get("source_id"),
                            sourceBook=(pick.get("source_book") or "").strip()
                            or (pick.get("variant") or "").strip(),
                            sourceUrl=pick.get("source_url") or "",
                            sourceFile=f"{src['layer']}/{pick['file']}",
                        )
            elif src.get("kind") == "font":
                ttf = FONTS / src["font"]
                if ttf.exists() and extract_font_glyph(ttf, query, out_file):
                    ok = True
                    record.update(
                        status="real",
                        file=f"{display}/{era}.svg",
                        sourceFile=src["font"],
                    )
            if not ok:
                record["note"] = f"未找到「{query}」在 {era} 层的可用字形"
            glyphs.append(record)

    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "sources": sources,
                "glyphs": glyphs,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# 字形出处与授权台账",
        "",
        "本目录字形由 `tools/glyphs/build_glyphs.py` 生成。来源与许可如下：",
        "",
        "| 字 | 时期 | 状态 | 来源文件 | 许可 | 署名 |",
        "|---|---|---|---|---|---|",
    ]
    for g in glyphs:
        lines.append(
            f"| {g['char']} | {g['era']} | {g['status']} | "
            f"{g.get('sourceFile') or '—'} | {g.get('license') or '—'} | "
            f"{g.get('attribution') or '—'} |"
        )
    (OUT / "CREDITS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    real = sum(1 for g in glyphs if g["status"] == "real")
    missing = len(glyphs) - real
    print(f"done: {real} real, {missing} missing")
    for g in glyphs:
        suffix = f" ({g['note']})" if g.get("note") else ""
        print(f"  {g['char']}/{g['era']}: {g['status']}{suffix}")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
