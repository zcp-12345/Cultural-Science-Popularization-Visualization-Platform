"""RAG 金标准评测：用真实向量检索逐条校验引用（需要已下载 embedding 模型）。

用法（在 backend 目录运行）：
    .venv/Scripts/python scripts/eval_rag.py

首次运行会触发 fastembed 下载模型，需 CA/HF_ENDPOINT 环境变量（见 README.md）。
改 docs.json 后请先删除 chroma_db/ 再跑，确保索引为最新语料。
"""
from __future__ import annotations

import sys
from pathlib import Path

# Windows 控制台默认 GBK，输出含生僻字（如「𠮷」）会 UnicodeEncodeError；显式用 UTF-8。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover - 已重定向的 stdout 可能不支持 reconfigure
    pass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services import rag  # noqa: E402


def main() -> int:
    items = rag.load_eval()
    print(f"金标准评测集：{len(items)} 条\n")

    failures = 0
    for item in items:
        question = item["question"]
        expect = set(item["expect_ids"])
        got = {d.id for d in rag.retrieve(question)}
        missing = expect - got
        ok = not missing
        failures += 0 if ok else 1

        mark = "PASS" if ok else "FAIL"
        print(f"[{mark}] {question}")
        print(f"        期望引用: {sorted(expect)}")
        print(f"        实际引用: {sorted(got)}")
        if missing:
            print(f"        缺失引用: {sorted(missing)}")

    print(f"\n{len(items) - failures}/{len(items)} 通过")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
