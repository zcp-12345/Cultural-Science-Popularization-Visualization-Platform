# 文化科普可视化平台 · 数字考古透视镜

汉字编码与字形演变的科普可视化平台。目标是把原「数字考古透视镜」纯前端 HTML 工具，升级为三层合一的完整产品：

- **前端**：Vue3 + TypeScript + ECharts + D3（Phase 1，已落地）
- **后端**：Python FastAPI + PostgreSQL（开发用 SQLite）（Phase 2，规划中）
- **AI 层**：RAG + DeepSeek + LangChain + ChromaDB/FAISS（Phase 3，规划中）

## 目录

```
数字考古透视镜/   原版纯 HTML/CSS/JS 工具（升级起点，作参考保留）
frontend/        Phase 1 Vue3 前端（Vercel 部署，Root Directory 选 frontend）
docs/            项目计划等文档
```

## 快速开始

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run test       # 编码引擎单元测试
npm run build      # 类型检查 + 生产构建
```

详见 [frontend/README.md](frontend/README.md) 与 [frontend/docs/PHASE1-PLAN.md](frontend/docs/PHASE1-PLAN.md)。

## 路线图

- **Phase 1（进行中）**：前端 UI + 交互，mock 数据，编码引擎金标准，Vercel 部署。
- **Phase 2**：FastAPI 后端，编码结果切到 Python `codecs` 权威源，JWT 用户系统。
- **Phase 3**：RAG 知识库 + DeepSeek 流式问答，替换前端 mock AI。
