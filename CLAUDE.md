# 数字考古透视镜 · 项目说明

汉字编码与字形演变的科普可视化平台：原「数字考古透视镜」纯前端 HTML 工具 → 三层产品（前端 Vue3 / 后端 FastAPI / AI 层 RAG+DeepSeek）。

## 目录

- `frontend/` — Phase 1 Vue3 前端（已落地；Vercel + Cloudflare Pages 部署，Root Directory=frontend）
- `backend/` — Phase 2 FastAPI 后端（开发 SQLite，生产 PostgreSQL）
- `docs/` — 计划文档；后端接口契约与里程碑以 `docs/PHASE2-PLAN.md` 为准
- `tools/glyphs/` — 字形 SVG 构建管线（产出到 `frontend/public/glyphs/`）
- `数字考古透视镜/` — 原版纯 HTML 工具（升级起点，参考保留，勿改）
- ⚠️ 本仓库（D 盘）是唯一活跃开发目录；OneDrive 桌面同名目录是 scratch，勿在那 init git 或当当前代码。

## 技术栈

- 前端：Vue3 + TS + Vue Router + Pinia + ECharts + D3；Vite 构建；Node ≥22.12
- 后端：FastAPI + SQLAlchemy 2.0 + pydantic-settings（lifespan 建表，非 on_event）；Python ≥3.11
- 测试：前端 vitest；后端 pytest

## 常用命令

前端（`cd frontend`）：

```bash
npm install
npm run dev        # http://localhost:5173，/api 已代理到 :8000
npm run test       # 编码引擎单测（vitest）
npm run build      # vue-tsc 类型检查 + vite build
```

后端（`cd backend`）：

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"      # Windows；类 Unix 用 .venv/bin/python
.venv/Scripts/uvicorn app.main:app --reload --port 8000
.venv/Scripts/python -m pytest tests/ -q             # 对照 frontend/src/data/encoding-gold.json 金标准
```

## 关键约定（不可回退）

- API 前缀 `/api/v1`。前端 `apiFetch` 直接 `response.json()` 不做字段转换，后端 Pydantic 用 `alias_generator=to_camel` 输出 camelCase，与 `frontend/src/types` 1:1 对齐。
- 安全：任何密钥只放后端 `.env`，绝不进 `VITE_*`；access token 仅存内存；refresh token 走 HttpOnly + SameSite Cookie；生产 CSP `default-src 'self'`。
- 编码权威源 = 后端 Python `codecs`（`backend/app/services/encoding.py` 的 describe_char/summarize_text）；前端本地实现仅作离线兜底。
- 鉴权（M3）：argon2 哈希 + PyJWT HS256；access 短期、refresh 长期。

## git 推送（本机固定参数，缺一不可）

```bash
git -c http.sslBackend=schannel -c http.proxy= -c https.proxy= push
```

- openssl CA bundle 损坏 → 用 schannel（Windows 证书库）；全局 http.proxy 指向已关的 Clash 需跳过。
- 认证用 PAT（已入 Windows 凭据管理器）；origin = `github.com/zcp-12345/Cultural-Science-Popularization-Visualization-Platform.git`。

## 部署

- Cloudflare Pages（对外正式分享用这个）：`https://cultural-science-popularization-visualization-platform.pages.dev`
- Vercel（国内被墙）：`https://cultural-science-popularization-visualization-platfo-eitb8q9xo.vercel.app`
- 后端：Phase 2 MVP 本地跑（localhost:8000），尚未部署。

## 进度与协作

- 阶段进度以 memory 的 `project-phases` 为准；后端里程碑/接口契约见 `docs/PHASE2-PLAN.md`。
- 按模块分对话推进：一个里程碑一个对话，完成即更新进度 memory，再开新对话。
- 读代码：先 Grep 定位，再用 Read 的 offset/limit 精准读段；勿 cat/find 整个目录或整读大文件。
