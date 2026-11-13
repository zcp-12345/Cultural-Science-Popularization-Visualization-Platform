"""金标准评测集（Phase 3 M4）测试：逐条校验「问题 → 期望引用 id」。

不下载 embedding 模型、不发网络请求，只用语料 keywords + `_rank` 的确定性打分
验证评测集与语料自洽：每条金标准问题的期望引用，在最坏情况（embedding 相似度
低于阈值）下也必须能被关键词加分救回。改 docs.json 的 keywords 破坏了某条引用时，
会在此处失败。
"""
from app.services import rag


class _FakeDoc:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


def test_eval_set_well_formed_and_covers_corpus():
    docs = {d["id"] for d in rag.load_docs()}
    items = rag.load_eval()
    assert items, "评测集不能为空"

    covered: set[str] = set()
    for item in items:
        assert item.get("question", "").strip(), "评测集条目缺少 question"
        expect_ids = item.get("expect_ids")
        assert isinstance(expect_ids, list) and expect_ids, "评测集条目缺少 expect_ids"
        for eid in expect_ids:
            assert eid in docs, f"评测集引用了不存在的语料 id：{eid}"
            covered.add(eid)

    # 每个语料文档至少被一条金标准问题覆盖（评测集完整性）。
    assert covered == docs, f"评测集未覆盖语料：{docs - covered}"


def test_eval_keyword_coverage_rescues_expected_citations():
    """每条金标准问题的期望引用 id，必须能被 keywords 加分救回（阈值 0.35 下）。"""
    docs = {d["id"]: d for d in rag.load_docs()}
    for item in rag.load_eval():
        question = item["question"]
        results = [
            (
                _FakeDoc(
                    d["body"],
                    {
                        "id": d["id"],
                        "title": d["title"],
                        "page": d.get("page", ""),
                        "keywords": d.get("keywords", []),
                    },
                ),
                0.9,  # 相似度 = 1 - 0.9 = 0.1，低于阈值，仅关键词命中才能救回
            )
            for d in docs.values()
        ]
        ranked = rag._rank(results, question, threshold=0.35)
        got_ids = {d.id for d in ranked}
        for eid in item["expect_ids"]:
            assert eid in got_ids, f"「{question}」的期望引用 {eid} 未被关键词救回"
