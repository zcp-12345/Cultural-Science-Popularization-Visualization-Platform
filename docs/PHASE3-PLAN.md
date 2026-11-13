# 数字考古透视镜 · Phase 3 计划与设计（AI 层）

> 本文档是 Phase 3（AI 层）的拆解方案：目标、目录结构、接口契约、RAG 检索设计、前端改造点、里程碑与开放决策。落地时以本文为准。
>
> 技术选型已拍板（2026-11-13）：**DeepSeek + LangChain + Chroma 向量检索 + fastembed(BGE, ONNX) 本地 embedding**。详见 §10。

## 1. 目标与范围

Phase 3 把产品从「前端 + 真后端 + AI mock」推进到三层闭环，把 `aiService` 的本地 mock 换成真实 **DeepSeek 流式 + RAG 向量检索**。

| 项 | 目标 |
| --- | --- |
| 大模型 | **DeepSeek**，经 **LangChain `ChatDeepSeek`**（`langchain-deepseek`），模型 `deepseek-chat`，流式 `astream()` |
| RAG | **Chroma 向量库**（`langchain-chroma`）+ 本地 **fastembed** BGE embedding（ONNX，免 torch）；知识库只摄入已审校语料；检索不到则**拒答/转人工** |
| 接口 | 新增 `POST /api/v1/ai/chat`（SSE），前端 `streamReply` 签名不变 |
| 兜底 | 前端保留本地 mock 作为**离线/无密钥兜底**（沿用「远程优先、本地兜底」的既有模式） |
| 不在本阶段 | 引用 UI、限流、后台评测、云端 embedding、多轮会话记忆，归入 Phase 4 |

**硬约束（沿用 Phase 1/2，不可回退）**：DeepSeek/API 密钥只放后端 `.env`，绝不进 `VITE_*`；生产 CSP 保持 `default-src 'self'`（同源 SSE 无冲突，别引第三方 CDN）；鉴权沿用 M3（access 仅内存、refresh 走 HttpOnly Cookie）。AI 对话面板当前对未登录用户开放，故 `/ai/chat` **不强制鉴权**（已拍板，§10）。

## 2. 后端新增文件

沿用现有分层（routes / schemas / services / core）。知识库与向量索引是**文件**（`docs.json` 语料 + Chroma `persist_directory`），**不需要新增 SQLAlchemy model，也不动 `create_all`**。

```
backend/
├── app/
│   ├── core/config.py            # + deepseek_base_url / deepseek_api_key / deepseek_model / ai_enabled / rag_top_k / kb_persist_dir / kb_source
│   ├── api/routes/ai.py          # POST /ai/chat（StreamingResponse，text/event-stream）
│   ├── schemas/ai.py             # ChatRequest（camelCase）
│   ├── services/
│   │   ├── ai.py                 # LangChain ChatDeepSeek 客户端 + prompt 组装 + SSE 事件
│   │   └── rag.py                # 加载 docs.json → 建/读 Chroma 索引 + 相似度检索 + 拒答判定
│   └── kb/
│       └── docs.json             # 已审校语料（从 aiService 的 CANNED 答案 + 编码事实迁移而来）
├── tests/test_ai.py              # mock LLM + 内存向量库，断言 SSE / 检索 / 拒答 / 无密钥
└── .env.example                  # + DEEPSEEK_* / AI_ENABLED / RAG_TOP_K / KB_*
```

依赖（`pyproject.toml` 主依赖新增）：`langchain`、`langchain-deepseek`、`langchain-chroma`、`langchain-community`（`FastEmbedEmbeddings`）、`fastembed`。**不装 torch**（fastembed 走 ONNX runtime）。

## 3. 接口契约：`POST /api/v1/ai/chat`（SSE）

请求体 `ChatRequest`（camelCase，与前端 `AiContext` 对齐）：

```jsonc
{ "question": "UTF-8 为什么汉字占 3 字节？", "page": "编码对比器", "char": "中" }
```

- `question`：必填，非空；服务端再截断到 500 字（与前端 `store` 兜底一致）。
- `page`：当前页面名（`route.meta.title`）。
- `char`：最近扫描的单个汉字，可选。

**响应**：`Content-Type: text/event-stream`，每条 `data:` 一行 JSON（内部换行已 `\n` 转义），事件间空行分隔。MVP 只发两种事件：

```
data: {"type":"token","text":"UTF-8 是变长编码"}

data: {"type":"token","text":"：常用汉字占 3 字节……"}

data: {"type":"done"}
```

- `token`：增量文本（前端 `streamReply` 逐段 `yield`）。
- `done`：正常结束。
- 预留（M4 引用 UI 再启用）：`{"type":"sources","items":[{"title":...,"source":...}]}`、`{"type":"error","message":...}`。

**流式前的失败**（无密钥 503 / 空问题 400 / 参数错 422）走普通 JSON `{"detail":...}` + 对应状态码，**不发 SSE**，前端据此回退本地 mock。**流式中的失败**：后端把错误文案包成一个 `token` 事件（如 `\n\n（生成中断，请重试）`）再发 `done`。

## 4. AI 服务设计（`services/ai.py`）

**DeepSeek 客户端**：LangChain `ChatDeepSeek`（`from langchain_deepseek import ChatDeepSeek`），`model=settings.deepseek_model`（默认 `deepseek-chat`）、`temperature=0.3`、`max_tokens=800`、`streaming=True`。流式用 `async for chunk in model.astream(messages)`，取 `chunk.content` 逐段 yield（DeepSeek 底层即 OpenAI 兼容 `/chat/completions` SSE，LangChain 已封装 `[DONE]` 等解析）。端点/模型名实现时以 DeepSeek 官方文档为准（`base_url` 默认 `https://api.deepseek.com`，另有更省的 `deepseek-flash` 可选）。

**Prompt 组装**（系统提示 + 权威事实注入 + RAG 上下文）：

1. **系统提示**：角色 = 数字考古科普助手；只答汉字编码 / 字形演变 / 产品相关问题；语气简洁准确、口语化科普、约 200 字；要求基于给定资料回答并标注 `[n]` 来源，资料没有就明说不知道，不编造。
2. **当前字符权威数据**：若 `char` 存在，调用既有 `services/encoding.describe_char(char)` 注入**真实编码事实**（码位 `U+XXXX`、UTF-8 字节、GB2312/GBK/Big5 是否收录）——「扫描某字后追问」无需命中检索也有权威接地。
3. **RAG 上下文**：`services/rag.py` 向量检索 top-k（默认 3）片段，格式化成带编号资料块 + 来源标题。
4. **用户问题**：原样附上。

## 5. RAG 检索设计（`services/rag.py`）

**语料** `kb/docs.json`：把 `aiService.ts` 里约 20 条 `CANNED` 答案（已审校文案）+ 编码权威事实整理为文档数组，每条：

```jsonc
{ "id": "utf8-bytes", "title": "UTF-8 字节规则",
  "keywords": ["UTF-8", "UTF8", "字节", "编码", "三字节", "3字节"],
  "page": "comparator", "body": "UTF-8 是变长编码……" }
```

迁移是一次性机械活：每条 CANNED 的 `match` 正则对应一组 `keywords`，`answer` 即 `body`（去掉「Phase 1 模拟」声明）。

**向量索引**：`FastEmbedEmbeddings(model_name="BAAI/bge-small-zh-v1.5")`（`langchain_community.embeddings`，ONNX、CPU、免 torch；首次运行自动下载约 130MB 模型）。语料 `body` 逐条 embed 写入 `Chroma(collection_name="...", persist_directory=settings.kb_persist_dir)`。

**建索引时机（懒加载）**：模块级单例 + 锁；首次 `/ai/chat` 请求时若 `persist_directory` 为空则用 `docs.json` 建一次，之后直接加载。这样不拖慢启动，AI 未用时不耗索引成本。

**检索**：`vector_store.similarity_search_with_score(question, k=top_k)`，按分数阈值过滤（`keywords`/`page` 命中可作加分或过滤的辅助信号）。

**拒答判定**：top-k 分数低于阈值或无命中 → 不进 RAG，直接返回固定拒答文案（「这个问题不在当前知识库覆盖范围，建议问我编码或字形演变相关……」）。

## 6. 前端改造点（Phase 3 需动的文件）

> 核心承诺：**`streamReply(question, context, signal): AsyncGenerator<string>` 签名不变**，`stores/chat.ts` 的 `for await` 消费方式不变。

| 文件 | 改动 |
| --- | --- |
| `services/ai/aiService.ts` | 现有 mock 抽成 `mockReply`（离线兜底）；`streamReply` 改为 `fetch(BASE_URL + '/ai/chat', { method:'POST', body, signal, credentials:'include' })`，用 `ReadableStream` 逐行解析 `data:` 的 `token` 事件并 `yield`。**预检失败**（网络错/503）→ 回退 `mockReply`；**用户中止**（AbortError）→ 原样抛出让 store 静默停止；**流式中断** → yield 一条错误提示文本 |
| `stores/chat.ts` | 近乎零改动：catch 里「（模拟回答中断，请重试）」改「（回答中断，请重试）」；其余不变 |
| `components/ai/AiChatDrawer.vue` | 文案改真实：标题副行「模拟模式 · Phase 1」→「DeepSeek + RAG」、`msg__tag`「AI 生成 · 模拟」→「AI 生成 · 已联网」、composer hint 去掉「Phase 3 接入……」 |
| `views/HomeView.vue` | AI 入口「数据暂为 mock」文案改真实 |

`apiFetch` 不用于这条（它是 `response.json()` 的，SSE 需要读原始 `response.body`），新增独立 `services/ai/sse.ts` 放行解析器。

## 7. 测试（沿用金标准式的确定性测试）

`tests/test_ai.py`（**mock LLM + 内存/临时目录向量库，不发真实网络请求**）：

- SSE 通道：假 DeepSeek 流 → 断言 `POST /ai/chat` 返回 `text/event-stream` 且 token 按序、`done` 收尾。
- Prompt 组装：请求带 `char` 时，注入的上下文含 `describe_char` 的真实 `unicodeHex`。
- 检索：命中「UTF-8 字节」类问题返回对应片段；无关问题触发**拒答文案**。
- 无密钥：`AI_ENABLED=false` 或 `deepseek_api_key` 为空 → `503` JSON。
- 参数：空 `question` → `400`。

前端补 `test_aiService`：mock `fetch` 的 `ReadableStream`，断言 `streamReply` 逐段 yield + 中止时抛 `AbortError`。

## 8. 里程碑

- **M1 — 后端 SSE 通道 + DeepSeek 直连（无 RAG）**：config 加 `deepseek_*`/`ai_enabled`；`services/ai.py`（LangChain `ChatDeepSeek` 流式 + prompt 组装含 `describe_char` 注入）；`schemas/ai.py`、`routes/ai.py`；`.env.example`；`test_ai.py`（mock LLM）。`uvicorn` 本地 `curl` 打通 SSE。
- **M2 — 知识库 + Chroma 向量检索**：`kb/docs.json`（迁移 CANNED 答案 + 编码事实）；`services/rag.py`（fastembed 建索引 + 相似度检索 + 拒答）；prompt 接 top-k 上下文与来源标注；补检索/拒答测试。
- **M3 — 前端切换**：`aiService.ts` 换 SSE 实现（保留 `mockReply` 兜底）+ `sse.ts` 解析器；改 `AiChatDrawer`/`HomeView` 文案；本地双端跑通真实流式回答，验证「停网/无密钥 → 回退 mock」。
- **M4（拉伸，可后置）**：`sources` 事件 + 引用 UI；金标准评测集（固定 Q&A 逐条校验引用）；拒答体验打磨；多轮会话记忆 / 云端 embedding / 限流。

## 9. 环境变量（`.env.example` 追加）

```
# AI 层（Phase 3）
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=sk-...              # 生产必填；仅后端，绝不进 VITE_*
DEEPSEEK_MODEL=deepseek-chat
AI_ENABLED=true                      # false 或密钥为空 → /ai/chat 返回 503，前端回退 mock
RAG_TOP_K=3
KB_SOURCE=app/kb/docs.json           # 语料文件路径
KB_PERSIST_DIR=./chroma_db           # Chroma 持久化目录（首次运行自动建索引）
```

## 10. 技术选型（2026-11-13 已拍板）

| 决策 | 结论 |
| --- | --- |
| 检索 | **向量检索**：Chroma + `FastEmbedEmbeddings`（`BAAI/bge-small-zh-v1.5`，fastembed/ONNX，本地免 torch） |
| 框架 | **LangChain**：`ChatDeepSeek` + `langchain-chroma` + `FastEmbedEmbeddings` |
| 鉴权 | `/ai/chat` **不强制鉴权**（保持未登录也能问 AI 的演示体验） |
| 模型 | 默认 **`deepseek-chat`**（`deepseek-flash` 作更省备选；`deepseek-reasoner` 留给深度追问） |
| 前端 mock | **保留为离线/无密钥兜底**，不复用其正文当正式回答 |
