"""把源 SVG 字形归一化到项目的统一格式。

规则（见 docs/GLYPH-PLAN.md §2）：
  * 单色可着色：所有 <path> 统一 fill="currentColor"，删掉源文件自带的
    fill/stroke/transform/width/height 与背景 <rect>。
  * 紧凑 viewBox：按路径包围盒重排，四周留 6% padding，让不同层的字形
    在时间轴里呈现一致的光学大小。
  * preserveAspectRatio="xMidYMid meet"，前端可自由缩放。

依赖：svgpathtools（pip install svgpathtools）
"""
from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from svgpathtools import parse_path

_SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", _SVG_NS)

_PAD = 0.06


def _path_bbox(d: str):
    """返回单个 SVG path 的 (xmin, ymin, xmax, ymax)，失败返回 None。"""
    try:
        path = parse_path(d)
    except Exception:
        return None
    bbox = path.bbox()
    if bbox is None or not all(v is not None for v in bbox):
        return None
    xmin, xmax, ymin, ymax = bbox
    if xmax <= xmin or ymax <= ymin:
        return None
    return (xmin, ymin, xmax, ymax)


def _union(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def normalize_svg(src: Path, dst: Path, pad: float = _PAD) -> None:
    """读取 src，重排 viewBox 后写一个可着色的 SVG 到 dst。"""
    tree = ET.parse(src)
    root = tree.getroot()

    paths: list[str] = []
    bbox = None
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "path":
            d = el.get("d")
            if d:
                paths.append(d)
                bbox = _union(bbox, _path_bbox(d))

    if not paths or bbox is None:
        raise ValueError(f"no usable <path> geometry in {src}")

    xmin, ymin, xmax, ymax = bbox
    w = xmax - xmin
    h = ymax - ymin
    px = w * pad
    py = h * pad
    vb = (xmin - px, ymin - py, w + 2 * px, h + 2 * py)

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{vb[0]:.3f} {vb[1]:.3f} {vb[2]:.3f} {vb[3]:.3f}" '
        'preserveAspectRatio="xMidYMid meet" fill="currentColor">',
    ]
    for d in paths:
        lines.append(f'  <path d="{d}"/>')
    lines.append("</svg>")

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
