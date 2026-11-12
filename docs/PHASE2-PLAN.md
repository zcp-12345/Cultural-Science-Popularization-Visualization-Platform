# 数字考古透视镜 · Phase 2 计划与设计

> 本文档是 Phase 2（后端）的拆解方案：目标、目录结构、接口契约、鉴权设计、编码引擎移植、前端改造点、里程碑与开放决策。落地时以本文为准。

## 1. 目标与范围

Phase 2 把产品从「纯前端 + mock」推进到「前端 + 真后端」：

| 项 | 目标 |
| --- | --- |
| 后端框架 | Python **FastAPI** + SQLAlchemy 2.0，开发用 **SQLite**、生产切 **PostgreSQL** |
| 用户系统 | 真实注册/登录/登出/刷新；**JWT**（access token 仅内存 + refresh token HttpOnly Cookie） |
| 编码权威源 | 编码结果（尤其 GB2312/GBK/Big5）切到后端 **Python `codecs`**；前端本地实现降级为离线兜底 |
| AI 层 | 不在本阶段（Phase 3），接口继续预留 |

**硬约束（沿用 Phase 1，不可回退）**：任何 DeepSeek/API 密钥只放后端环境变量，不进 `VITE_*`；access token 不落 localStorage；refresh token 走 HttpOnly + SameSite Cookie；生产 CSP 保持 `default-src 'self'`。

## 2. 后端目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # create_app()：注册路由、CORS、启动建表
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # pydantic-settings：DATABASE_URL / JWT_SECRET / CORS_ORIGINS / TTL
│   │   ├── security.py         # argon2 哈希 + PyJWT 签发/校验
│   │   └── deps.py             # get_db / get_current_user
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy Base
│   │   └── session.py          # engine / SessionLocal / get_db
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py             # User（id, name, email, password_hash, joined_at）
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py             # RegisterIn / LoginIn / TokenPair
│   │   ├── user.py             # UserOut（= 前端 UserProfile）
│   │   └── encoding.py         # CharDescription / TextSummary（camelCase，与前端 TS 类型 1:1）
│   ├── services/
│   │   ├── __init__.py
│   │   └── encoding.py         # describe_char() / summarize_text()：Python codecs 权威实现
│   └── api/
│       ├── __init__.py         # api_router = APIRouter(prefix="/api/v1")
│       └── routes/
│           ├── __init__.py
│           ├── health.py       # GET /health
│           ├── auth.py         # register / login / refresh / logout
│           ├── users.py        # GET /users/me
│           └── encoding.py     # POST /encoding/describe、/encoding/summarize
├── tests/
│   ├── conftest.py
│   ├── test_encoding.py        # 对照 Python codecs 金标准
│   └── test_auth.py
├── alembic/                    # 迁移（MVP 可先 create_all，后补 Alembic）
├── pyproject.toml              # 依赖 + 工具配置
├── .env.example
└── README.md
```

依赖（`pyproject.toml`）：`fastapi`、`uvicorn[standard]`、`sqlalchemy>=2.0`、`pydantic>=2`、`pydantic-settings`、`PyJWT`、`argon2-cffi`（或 `bcrypt`）；生产加 `psycopg[binary]`；测试加 `pytest`、`httpx`。

## 3. 接口契约（对齐前端已预留类型）

> 关键点：前端 `apiFetch` 直接 `response.json()` 不做字段转换，且 TS 类型是 **camelCase**，所以后端必须用 Pydantic `alias_generator=to_camel`（或逐字段 `alias`）输出 camelCase JSON，保证 1:1 对齐。

所有路径前缀 `/api/v1`（对应 `VITE_API_BASE_URL` 默认值）。

### 3.1 编码

`POST /encoding/describe` — 请求 `{"char":"中"}`，返回 `CharDescription`（字段与 `src/types/encoding.ts` 完全一致）：

```jsonc
{
  "char": "中", "codePoint": 20013, "unicodeHex": "4E2D",
  "binary": "0100111000101101", "plane": 0, "planeName": "基本多文种平面", "block": "CJK 统一表意文字",
  "utf8": { "bytes": [228,184,173], "text": "E4 B8 AD",
    "parts": [{"byte":228,"binary":"11100100","marker":"1110","data":"0100","isContinuation":false}, ...] },
  "utf16": { "units":[{"value":20013,"hex":"4E2D","binary":"0100111000101101"}],
    "bytesLE":[45,78], "bytesBE":[78,45], "isSurrogatePair":false },
  "legacy": {
    "gb2312": {"bytes":[214,208], "available":true},
    "gbk":     {"bytes":[214,208], "available":true},
    "big5":    {"bytes":[164,164], "available":true}
  }
}
```

`POST /encoding/summarize` — 请求 `{"text":"..."}`，返回 `TextSummary`（`utf8/utf16/gb2312/gbk/big5` 各一份 `EncodingAggregate`，见 `src/types/encoding.ts`）。

### 3.2 鉴权与用户

| 方法/路径 | 请求体 | 响应 |
| --- | --- | --- |
| `POST /auth/register` | `{name,email,password}` | `201 {access_token, token_type:"bearer", user:UserOut}` + `Set-Cookie: refresh_token` |
| `POST /auth/login` | `{email,password}` | `200 {access_token, token_type, user}` + `Set-Cookie: refresh_token` |
| `POST /auth/refresh` | （凭 Cookie） | `200 {access_token, token_type}` + 新 `Set-Cookie` |
| `POST /auth/logout` | （Bearer） | `204` + 清 Cookie / 撤销 refresh |
| `GET /users/me` | （Bearer） | `200 UserOut` |

`UserOut` 与前端 `UserProfile`（`src/types/user.ts`）一致：`{id, name, email, joinedAt}`（`joinedAt` 为 ISO 字符串）。

### 3.3 前端对接方式（复用已预留的 `apiFetch`）

```ts
// 登录示例（stores/user.ts 改真实实现）
const data = await apiFetch<LoginResponse>('/auth/login', {
  method: 'POST', body: JSON.stringify({ email, password }),
})
token.value = data.access_token   // 仅内存
```

## 4. 鉴权设计

- **密码哈希**：argon2（`argon2-cffi`），只存哈希。
- **access token**：PyJWT HS256，短期（建议 15 分钟），放响应体，前端**仅存内存**。
- **refresh token**：长期（建议 7 天），放 `HttpOnly; Secure; SameSite=Lax` Cookie；`/auth/refresh` 用它换新 access。
- **前端启动流程**：内存无 access 但有 refresh cookie → 自动 `POST /auth/refresh`；401 时尝试刷新一次，仍失败则登出。
- `get_current_user` 依赖：解析 `Authorization: Bearer <JWT>` → 查库 → 注入当前用户。

## 5. 编码引擎移植（Python codecs 权威源）

`app/services/encoding.py` 用 Python 标准库 `codecs` 实现 `describe_char` / `summarize_text`，逐字段对齐前端：

- `utf8`：`char.encode('utf-8')`，按前端规则拆 marker/data（首字节 marker 长度 = 字节数==1 ? 1 : 字节数+1；续字节固定 2）。
- `utf16`：`char.encode('utf-16-le')` 得 `bytesLE`，反转得 `bytesBE`；`len(units)==2` 判定代理对。
- `legacy`：`char.encode('gb2312'|'gbk'|'big5', errors='strict')`，成功则 `available=true + bytes`，抛 `UnicodeEncodeError` 则 `available=false + bytes=null + note`（说明该字不在该字符集）。
- `plane/planeName/block`：Unicode 元数据，非编码权威，但为保持 `CharDescription` 1:1，把 `src/services/encoding/unicodeBlocks.ts` 的区间表一次性移植为 Python 常量表（机械活）。

**校验**：后端 `test_encoding.py` 逐字对照仓库已有的金标准 `frontend/src/data/encoding-gold.json`（由 `scripts/generate_encoding_gold.py` 生成），并补充「龙/龍/马/馬/镕/𠮷/¥/•」等简繁与 Big5 方言分歧用例。

**前端降级**：`services/encoding` 增加 `describeCharRemote()` —— 在线调后端，失败/离线回退本地 `describeChar()`（离线兜底保留）。

## 6. 前端改造点（Phase 2 需动的文件）

| 文件 | 改动 |
| --- | --- |
| `stores/user.ts` | `login/register/logout` 换真实 `apiFetch`；`token` 存内存；启动时用 refresh cookie 换 access；`isLoggedIn` 改为**校验 token**（profile 不再作权限依据） |
| `services/api/index.ts` | 可加一个「401 → 自动 refresh 一次」的轻量封装（MVP 可先不做，手动处理） |
| `services/encoding/index.ts` | 加 `describeCharRemote`/`summarizeTextRemote`，视图层切到「远程优先、本地兜底」 |
| `.env`（前端） | `VITE_API_BASE_URL=http://localhost:8000/api/v1`（开发） |

## 7. 里程碑

- **M1 后端骨架**：FastAPI 应用 + SQLite + CORS + `/health`；`uvicorn` 本地跑通。
- **M2 编码权威源**：`/encoding/*` 落地，`test_encoding.py` 对照金标准全绿；前端切「远程优先、本地兜底」。
- **M3 用户系统**：注册/登录/刷新/登出 + JWT + HttpOnly refresh Cookie；前端 store 换真实实现；浏览器走通完整登录流。
- **M4（可选）**：学习进度/收藏持久化到后端（替换 `stores/user.ts` 里写死的 `stats`）。

## 8. 环境变量

后端 `.env.example`：

```
DATABASE_URL=sqlite:///./dev.db          # 生产换 postgresql+psycopg://...
JWT_SECRET=change-me                      # 生产必改强随机
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=7
CORS_ORIGINS=http://localhost:5173,https://cultural-science-popularization-visualization-platform.pages.dev,https://cultural-science-popularization-visualization-platfo-eitb8q9xo.vercel.app
```

## 9. 开放决策（2026-11-12 已拍板）

> 用户确认按推荐执行：① MVP 先本地跑、暂不部署；② SQLite 现在、PostgreSQL 留到部署时再切；③ 预留 `POST /ai/chat` SSE stub；④ stats 保持前端 mock（M4 可选，不在本轮硬做）。

1. **后端部署**：Phase 2 的 MVP 先「后端本地跑（localhost:8000）+ 前端本地连」，交付可演示。真后端部署到哪（Render / Railway / Fly.io / 腾讯云 / 阿里云 VPS）是独立里程碑——且要面对与 vercel.app 相同的**国内可达性**问题，需另行评估。
2. **数据库**：MVP 用 SQLite（零运维）；是否在 Phase 2 内就上 PostgreSQL + 迁移（Alembic），还是留到部署时再切。
3. **AI 边界**：Phase 2 不接 DeepSeek；但可在后端预留 `POST /ai/chat`（SSE）的 stub，方便 Phase 3 无缝接入。
4. **stats 持久化**：是否纳入 Phase 2（M4），还是保持前端 mock 计数。
