# 部署手册

三层产品的线上闭环：前端静态站（Cloudflare Pages，国内可访问）→ 后端 FastAPI（香港服务器，Docker）→ PostgreSQL（服务器本机容器）+ AI（DeepSeek + 硅基流动，均为国内可访问服务）。

> 面向国内演示，**后端只能上国内/香港服务器**：Render / Railway / Fly / Vercel 等海外免费 PaaS 的域名国内基本被墙（后端访问不到 = 前端自动回退 mock）。前端是 HTTPS（pages.dev），后端也必须 HTTPS（浏览器混合内容限制），所以需要一个域名（香港服务器免备案）。

## 方案：香港轻量服务器 + 域名 + Docker Compose（推荐）

### 1. 买服务器和域名

- 阿里云/腾讯云 → **轻量应用服务器** → **香港地域**，镜像选 **Ubuntu 22.04 或 24.04**，2核2G 起步。
- 记下**公网 IP**，设置 root 登录密码。
- 买一个**域名**（同家更省事），在 DNS 解析里加一条 **A 记录**：`api`（或任意子域名）→ 服务器公网 IP。
- 云控制台**防火墙/安全组**放行端口：`22`（SSH）、`80`、`443`。

### 2. 登录服务器、装 Docker

用云控制台的「远程连接/Web 终端」或本地 `ssh root@<公网IP>` 登录，然后：

```bash
# 官方一键脚本安装 Docker（含 compose 插件）
curl -fsSL https://get.docker.com | sh
```

### 3. 拉代码、填配置

```bash
git clone https://github.com/zcp-12345/Cultural-Science-Popularization-Visualization-Platform.git
cd Cultural-Science-Popularization-Visualization-Platform/deploy
cp .env.example .env
vi .env   # 填 API_DOMAIN / POSTGRES_PASSWORD / JWT_SECRET / DEEPSEEK_API_KEY / EMBEDDING_API_KEY
```

`.env` 里各字段说明见 `.env.example` 注释。域名 A 记录必须已生效（Caddy 首次启动要申请证书）。

### 4. 启动

```bash
docker compose up -d --build
```

首次会拉镜像 + 打后端镜像（约几分钟）。Caddy 会自动申请并续期 Let's Encrypt 证书。

验证：浏览器访问 `https://<API_DOMAIN>/api/v1/health` → 应返回 `{"status":"ok"}`。

### 5. 前端接后端

Cloudflare Pages 项目 → Settings → Environment variables → Production，加：
- `VITE_API_BASE_URL = https://<API_DOMAIN>/api/v1`

改完自动重建（或 Deployments 里 Retry）。打开 pages.dev 验证：编码对比器走远程权威源、可注册登录、AI 命中带 `[n]` 引用。

### 6. 更新后端

以后后端改了代码，服务器上：

```bash
cd Cultural-Science-Popularization-Visualization-Platform
git pull
cd deploy && docker compose up -d --build
```

## 技术要点（已内建，无需改动）

- **跨域**：前端 pages.dev 与后端不同源，refresh cookie 用 `SameSite=None; Secure`（`COOKIE_SAMESITE=none` + `COOKIE_SECURE=true`），CORS 白名单在 `deploy/docker-compose.yml` 的 `CORS_ORIGINS`。
- **PostgreSQL 驱动**：`psycopg[binary]`（`backend/pyproject.toml` / `requirements.txt`），连接串 `postgresql+psycopg://...`，引擎带 `pool_pre_ping`。
- **AI/向量**：DeepSeek + 硅基流动都是国内服务，从香港直连稳定；`EMBEDDING_PROVIDER=cloud` 不下载本地模型。
- **SSE**：Caddy 关闭响应缓冲（`flush_interval -1`），保证 AI 流式输出不被延迟。

## 附：海外可访问场景（非国内演示）

若演示对象在海外（能访问 Render），可用根目录 `render.yaml` + Neon PostgreSQL 走 Render Blueprint；但国内访问不到，故默认不推荐。
