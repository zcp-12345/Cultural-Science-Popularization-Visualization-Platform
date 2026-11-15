# 部署手册（后端 Render + Neon PostgreSQL，前端 Cloudflare Pages）

三层产品的线上闭环：前端静态站（Cloudflare Pages，国内可访问）→ 后端 FastAPI（Render，Docker）→ 数据库（Neon PostgreSQL）+ AI（DeepSeek + 硅基流动）。

前端线上默认读 `VITE_API_BASE_URL`，指向后端 `/api/v1`；后端不可达时自动回退本地 mock（编码/AI），保证演示不崩。

## 0. 准备

- GitHub 仓库：`zcp-12345/Cultural-Science-Popularization-Visualization-Platform`（本仓库，已含 `render.yaml` / `backend/Dockerfile`）。
- 两个账号：Render、Neon（均免费额度，注册无需绑卡）。
- 两个密钥：DeepSeek API key、硅基流动 API key（已在本机 `backend/.env` 中，不在仓库内）。

## 1. 创建 Neon PostgreSQL

1. 登录 [neon.tech](https://neon.tech) → Create project（Free 即可）。
2. 建好后点 **Connect**，选 **SQLAlchemy** 或直接复制 connection string，形如：
   `postgresql://<user>:<password>@ep-xxx.us-east-2.aws.neon.tech/<dbname>?sslmode=require`
3. 把 `postgresql://` 改成 `postgresql+psycopg://`（后端用 psycopg3 驱动）。
4. 记下这串连接串，下一步用。**Neon 免费库会休眠**，首次请求冷启动略慢，属正常。

## 2. 部署后端到 Render（Blueprint）

1. 登录 [render.com](https://render.com) → **New → Blueprint**。
2. 连接 GitHub 仓库，选本仓库。Render 自动读取根目录 `render.yaml` 创建 `digital-archaeology-api` Web 服务。
3. Blueprint 会提示填 **sync:false 的密钥**，逐个填：
   - `DATABASE_URL`：上面 Neon 的 `postgresql+psycopg://...?sslmode=require`。
   - `DEEPSEEK_API_KEY`、`EMBEDDING_API_KEY`：本机 `backend/.env` 里的两个 key。
   - `JWT_SECRET` 已用 `generateValue` 自动生成，无需手填。
4. 创建后等构建完成，访问 `https://<服务名>.onrender.com/api/v1/health` 应返回 `{"status":"ok"}`。
5. **记下实际域名**（默认 `https://digital-archaeology-api.onrender.com`；若名字被占用 Render 会加后缀，以控制台为准）。

> 注：免费 Web 服务 15 分钟无流量会休眠，首次请求冷启动约 30–60s；AI 首问会先用云端 embedding 建一次 Chroma 索引（约几秒）。演示前先访问一次 health 预热。

## 3. 前端指向后端并重新构建

1. 到 Cloudflare Pages 项目 → **Settings → Environment variables → Production**，新增：
   - `VITE_API_BASE_URL = https://<实际域名>.onrender.com/api/v1`
2. 触发重新构建（改变量后 CF Pages 会自动重建，或在 Deployments 里 Retry）。
3. 若 Vercel 镜像也用，同样在 Vercel → Settings → Environment Variables 设置后重新部署。

前端 CSP（`vercel.json` 与 `public/_headers`）已放行 `connect-src 'self' https://*.onrender.com`，无需再改。

## 4. 验证清单

- `GET /api/v1/health` → 200。
- 线上打开 pages.dev：编码对比器应走「远程权威源」（不是本地兜底），登录/注册可用。
- AI 提问命中知识库 → 返回带 `[n]` 引用；问无关问题 → 拒答。
- 刷新页面后仍保持登录（refresh cookie 走 `SameSite=None; Secure` + CORS credentials）。

## 5. 本地仍可全量开发

后端本地 `uvicorn` + 前端 `npm run dev`（Vite proxy）同源，不受上面跨域配置影响；本地用 SQLite（`DATABASE_URL=sqlite:///./dev.db`）、`COOKIE_SECURE=false`、`COOKIE_SAMESITE=lax`。
