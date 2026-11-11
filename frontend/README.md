# 数字考古透视镜 · Phase 1 前端

汉字编码与字形演变的科普可视化平台。本仓库是三层合一产品（Vue3 前端 + FastAPI 后端 + RAG AI 层）的 **Phase 1 前端重构**：原生 HTML/CSS/JS 迁移为 Vue3 组件化项目，数据暂用 mock，接口已为 Phase 2/3 预留。

## 技术栈

- Vue 3.5 + TypeScript + Vue Router 5 + Pinia 4
- Vite 8 + Vitest 5
- ECharts 6（编码字节开销对比，按需引入）
- D3 7（汉字演变时间轴）
- 目标部署：Vercel（SPA rewrite 已配置）

## 快速开始

```bash
npm install
npm run dev       # http://localhost:5173
npm run test      # 编码引擎单元测试
npm run build     # vue-tsc 类型检查 + 生产构建
npm run preview
```

可选：无头浏览器冒烟测试（先 `npm install --no-save playwright && npx playwright install chromium`，再 `node scripts/smoke.mjs`），会加载全部路由并断言无 console/page 错误。

## 目录结构

```
src/
  components/
    layout/      AppHeader、MobileTabBar
    magnifier/   MagnifierLens（三步变身透视镜）
    comparator/  EncodingChart（ECharts）
    timeline/    EvolutionTimeline（D3）
    ai/          AiChatDrawer（AI 对话）、AiNotesPanel（实时考古笔记）
    ui/          AppIcon、ScanChar
  views/         Home / Comparator / Timeline / Profile / NotFound
  services/
    encoding/    编码引擎（UTF-8 / UTF-16 / GB2312 / GBK / Big5）
    ai/          aiService（流式 mock，Phase 3 替换为 SSE）
    api/         FastAPI 客户端占位（Phase 2）
    mock/        abortable sleep
  stores/        ui / archaeology / user / chat（Pinia）
  data/          eras.ts（时间轴 mock）、encoding-gold.json / gb2312-characters.json（编码金标准）
  types/         编码、字符、AI、用户、路由元信息类型
  scripts/       generate_encoding_gold.py（Python codecs 生成编码金标准夹具）
tests/           encoding.test.ts、encoding-gold.test.ts（对照 Python 金标准）
```

## 已实现（Phase 1）

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 透视镜三步变身 | ✅ | 鼠标扫字 / 点击 / 键盘三种入口；步骤 0–3 循环；支持 `prefers-reduced-motion` |
| 实时考古笔记 | ✅ | 扫描结果写入右侧面板，含 UTF-8 字节与 GB2312/GBK/Big5 覆盖 |
| 编码对比器 | ✅ | 逐字切换、字节可视化、ECharts 对比图、整段文本汇总表、复制十六进制 |
| 汉字演变时间轴 | ✅ | D3 时间轴 + 选定汉字的六时期说明；字形为示意占位（见下） |
| 用户中心 | ✅（mock） | 登录/注册表单、学习进度、收藏、最近活动；数据存 localStorage |
| AI 对话面板 | ✅（mock） | 右侧抽屉、流式输出、上下文标签、建议问题；接口形态对齐 Phase 3 |
| 路由与响应式 | ✅ | 四个页面 + 404；移动端底部 TabBar；全局霓虹考古视觉 |

## 编码计算说明

浏览器没有 GBK/Big5 编码器，因此 `services/encoding/legacy.ts` 用 `TextDecoder` 枚举双字节合法区段构建「字符 → 字节」反向索引（首次调用约 20–30ms，之后缓存）：

- GB2312 使用 Python `codecs` 生成的权威 7445 字集合（`src/data/gb2312-characters.json`）判定收录范围，不再用字节区间近似；GBK 扩展字（如「镕」）正确判为 GBK 有 / GB2312 无；
- Big5 存在两处真实方言差异（已写入测试与代码注释）：
  - **HKSCS**：浏览器 `TextDecoder('big5')` 含 Big5-HKSCS 增补（如「龙」可命中），Node ICU / Python 严格 `big5` 不含；
  - **A1 标点行**：Python `big5` 含 ¥(A2 44)、•(A1 45) 等，WHATWG/浏览器 big5 不含；
- Unicode 是字符集，不参与字节数比较；UTF-8 / UTF-16 按码位 + 标记位直接计算；
- GB18030、UTF-32 等未纳入 Phase 1；
- 金标准夹具 `src/data/encoding-gold.json` 由 `scripts/generate_encoding_gold.py`（Python codecs, strict）生成，`tests/encoding-gold.test.ts` 逐字比对；
- Phase 2 起由后端 Python `codecs` 返回权威结果，前端实现作为离线兜底。

单元测试覆盖：BMP 汉字、代理对生僻字（𠮷）、ASCII、GBK 扩展字（镕）、简繁在 Big5 的覆盖差异，以及 Big5 方言分歧的显式断言。

## Phase 2 / 3 接口预留

- `src/services/api/index.ts`：`apiFetch` + `ApiError` + `withToken`，读取 `VITE_API_BASE_URL`（默认 `/api/v1`）。
- `src/types/*`：与 FastAPI 响应对应的数据结构；后端可用 OpenAPI 生成 TS 类型后替换。
- `src/services/ai/aiService.ts`：`streamReply()` 返回 `AsyncGenerator<string>`；Phase 3 换成 SSE / ReadableStream 时保持接口不变。
- 用户 store 的 `login/register/logout` 已按异步接口编写，Phase 2 替换实现即可。

## 环境变量

复制 `.env.example` 为 `.env`：

```
VITE_USE_MOCK=true
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_AI_MODE=mock
```

## Vercel 部署

1. 导入仓库，**Root Directory 选择 `frontend`**；
2. Framework Preset：Vite；Build Command：`npm run build`；Output Directory：`dist`；
3. `vercel.json` 已配置 SPA rewrite，直接访问 `/comparator` 等路由不会 404。

## 待办 / 素材约定

- 古文字字形素材：约定路径 `public/glyphs/{汉字}/{时期}.svg`（时期 id 见 `src/data/eras.ts`）。接入前必须确认字体/拓片授权，当前为大字示意占位。
- 中文字体体积大，若引入 Web 字体需先子集化；当前使用系统字体栈。
- Electron 桌面版暂不迁移，Web 优先；如需保留可复用同一构建产物。

## 文档

- [Phase 1 计划与状态](docs/PHASE1-PLAN.md)：范围、正确性/可访问性/安全加固清单、里程碑、风险与开放决策。
