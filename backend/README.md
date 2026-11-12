# 数字考古透视镜 · 后端（Phase 2）

FastAPI + SQLAlchemy 2.0，开发用 SQLite，生产切 PostgreSQL。

## 运行（本地开发）

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # Windows；类 Unix 用 .venv/bin/python
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

健康检查：`GET http://localhost:8000/api/v1/health` → `{"status":"ok"}`。

编码权威源（M2）：

- `POST /api/v1/encoding/describe` — 请求 `{"char":"中"}`，返回 `CharDescription`（camelCase，与前端 `src/types/encoding.ts` 1:1）。
- `POST /api/v1/encoding/summarize` — 请求 `{"text":"..."}`，返回 `TextSummary`。

运行测试：`.venv/Scripts/python -m pytest tests/ -q`（对照 `frontend/src/data/encoding-gold.json` 金标准）。

## 目录

见 `docs/PHASE2-PLAN.md`。里程碑：

- M1 骨架（已完成）：应用 + SQLite + CORS + `/health` + User 建表。
- M2 编码权威源（已完成）：`POST /encoding/describe`、`POST /encoding/summarize`，Python `codecs` 实现，对照金标准测试。
- M3 用户系统（未做）：注册/登录/刷新/登出 + JWT + HttpOnly refresh Cookie。
- M4（可选）：学习进度持久化。

## 硬约束

任何密钥只放后端环境变量，不进 `VITE_*`；access token 不落 localStorage；refresh token 走 HttpOnly Cookie；生产 CSP 保持 `default-src 'self'`。
