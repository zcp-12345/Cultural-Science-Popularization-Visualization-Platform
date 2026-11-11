# 数字考古透视镜 · Phase 1 计划与状态

> 本文档是「纯前端 HTML 工具 → 三层合一产品」升级的 Phase 1（1–2 周）落地记录：范围、已完成的正确性 / 可访问性 / 安全加固、状态矩阵、里程碑与风险、以及留给后续阶段与用户拍板的开放决策。

## 1. 产品三层结构

| 层 | 技术 | 状态 |
| --- | --- | --- |
| 前端 | Vue3 + TypeScript + Pinia + Vue Router + ECharts + D3 + CSS3 动画 | Phase 1 落地中 |
| 后端 | Python FastAPI + PostgreSQL（开发用 SQLite） | Phase 2 预留 |
| AI 层 | RAG + DeepSeek API + LangChain + ChromaDB/FAISS | Phase 3 预留 |

Phase 1 约束：前端 UI + 交互优先，数据用 mock；组件化、可维护；为 Phase 2 保留接口形态；保留动画质量；部署到 Vercel。

## 2. 范围与状态矩阵

### 2.1 核心功能（原始需求）

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| Vite/Vue3 骨架 | ✅ | Vue 3.5 + TS + Router + Pinia，组件化目录结构 |
| 透视镜三步变身动画 | ✅ | 鼠标扫字 / 点击 / 键盘三入口；Unicode→二进制→UTF-8；支持 `prefers-reduced-motion` |
| 编码对比器 | ✅ | Unicode / UTF-8 / UTF-16 / GB2312 / GBK / Big5；ECharts 字节对比 + 整段文本汇总 |
| D3 汉字演变时间轴 | ✅ | 甲骨文→金文→小篆→隶书→楷书 + 简体字现代规范节点；字形为示意占位 |
| 用户中心 UI 骨架 | ✅（mock） | 登录/注册、学习进度、收藏、最近活动；token 仅存内存 |
| AI 聊天面板 UI 骨架 | ✅（mock） | 右侧抽屉、流式输出、22 张知识卡；接口形态对齐 Phase 3 |

### 2.2 采纳的增强项（“那就按照你的建议加入的计划来”）

以下是在原始范围之外、经确认后加入并已落地/计划落地的内容。

| 类别 | 项 | 状态 |
| --- | --- | --- |
| 内容正确性 | 三处事实错误修正（甲骨文以占卜记录为主；隶变时间线；“拆成 1–4 个字节”） | ✅ |
| 内容正确性 | 编码史与字形史在文案上严格区分（码位 vs 笔画 vs 字节） | ✅ |
| 内容正确性 | GB2312 从字节区间近似改为 Python codecs 权威 7445 字集合 | ✅ |
| 内容正确性 | Big5 两处方言分歧（HKSCS、A1 标点行）显式记录与测试 | ✅ |
| 内容正确性 | 时间轴“非等比”标注、现代字形示意标识、六段说明修正 | ✅ |
| 可访问性 | 焦点可见环、跳过链接、`<main>` 锚点、对比度修复 | ✅ |
| 可访问性 | AI 抽屉：焦点管理 + 焦点陷阱 + Escape（含 `isComposing`）+ `role=log`/`aria-live` + 500 字上限 | ✅ |
| 可访问性 | 底部附近才自动滚动（避免打断回看历史） | ✅ |
| 演示可靠性 | 首页“自动演示”按钮（中→龙→码→字 循环）+ `?demo=1` 自动开启 | ✅ |
| 演示可靠性 | 懒加载 chunk 失败自动重试 + 兜底错误页；全局错误边界 | ✅ |
| 安全加固 | token 仅内存、不落 localStorage；refresh token 走 HttpOnly cookie（Phase 2） | ✅ |
| 安全加固 | `withToken` 拒绝 `mock.` / `demo.` / `placeholder` 前缀假凭证 | ✅ |
| 安全加固 | Vercel 安全响应头 + 严格 CSP（`default-src 'self'` 等） | ✅ |
| 安全加固 | 路由 `//` 协议相对跳转防护 | ✅ |
| AI 知识库 | 22 张 mock 知识卡（含浏览器编码技术、简体字、emoji/字素簇、RAG 架构、AI 可信/幻觉、字形版权等） | ✅ |

## 3. 已确认的编码事实（Phase 2 后端需保持一致）

- Unicode 是**字符集**，不给每个字一个字节数；字节数由具体编码决定。
- UTF-8：ASCII 1 字节、BMP 汉字 3 字节、辅助平面（如 𠮷）4 字节；标记位 0 / 110 / 1110 / 11110。
- UTF-16：BMP 1 个码元（2 字节）、辅助平面代理对 2 个码元（4 字节）。
- GB2312：严格 7445 字；「龙/马/华」收录，「龍/馬/華」不收录；扩展区字（镕）属 GBK 不属 GB2312。
- Big5 方言分歧：浏览器含 HKSCS；Python `big5` 含 A1 标点行（¥/•）而浏览器不含。Phase 2 以 Python `codecs`（strict）为权威源，前端作为离线兜底，需在文档中注明该分歧。

## 4. 里程碑

- **M1（已完成）**：骨架 + 三步变身 + 编码引擎（含金标准夹具）+ 对比器 + 时间轴。
- **M2（已完成）**：AI 面板 / 用户中心骨架 + 可访问性与安全加固 + 内容正确性修正 + 自动演示。
- **M3（已完成验证，待部署）**：`npm run test`（43/43 通过）+ `npm run build`（vue-tsc 类型检查 + vite 生产构建通过）；headless Chromium 冒烟测试（5 条路由渲染正常、无 console/page 错误）；Vercel 部署待仓库就位后执行。
- **M4（Phase 2）**：FastAPI + PostgreSQL，编码结果切到后端权威源，JWT 用户系统（access token 内存 + refresh token HttpOnly cookie）。
- **M5（Phase 3）**：RAG 知识库 + DeepSeek SSE 流式，替换 `aiService` 的 mock 实现（接口不变）。

## 5. 风险与开放决策（待用户拍板）

1. **仓库位置**：当前工作目录在 OneDrive 内，**不建议在 OneDrive 内初始化 git**（文件锁 / 同步冲突 / 大体积 node_modules）。需用户确认目标仓库路径后再迁移。
2. **竞赛/评审规则**：是否允许使用 DeepSeek 等外部 API、是否限制第三方服务，需按比赛要求确认后再定 Phase 3 接入方式。
3. **古文字字形素材**：`public/glyphs/{汉字}/{时期}.svg` 为约定路径，当前为大字示意占位；接入前必须确认字体/拓片授权（避免字形版权问题）。
4. **中文字体体积**：如需 Web 字体须子集化；当前用系统字体栈。
5. **Big5 方言差异**：演示/文档需说明“浏览器 Big5 ≈ Big5-HKSCS”，避免与后端 Python 结果不一致造成困惑。

## 6. 接口预留（供 Phase 2/3 替换）

- `src/services/api/index.ts`：`apiFetch` / `ApiError` / `withToken`，读 `VITE_API_BASE_URL`（默认 `/api/v1`）。
- `src/services/ai/aiService.ts`：`streamReply()` 返回 `AsyncGenerator<string>`；Phase 3 换 SSE/ReadableStream 保持签名。
- `src/stores/user.ts`：`login/register/logout` 已按异步接口编写；token 内存态，`persist()` 只写 `profile`。
- `src/types/*`：与 FastAPI 响应对齐；后端 OpenAPI 生成 TS 类型后可替换。

## 7. 安全约定（不可回退）

- 任何 DeepSeek / API 密钥**不得**放 `VITE_*`（会打进前端包），一律后端环境变量。
- 前端 token 不落 localStorage；Phase 2 access token 仅内存、refresh token 走 HttpOnly + SameSite cookie。
- 生产环境 CSP 保持 `default-src 'self'`，引入外部脚本/字体需显式放宽并经评审。
