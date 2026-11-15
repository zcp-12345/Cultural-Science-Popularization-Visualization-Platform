# 数字考古透视镜 · 后端（FastAPI）。Render 用此 Dockerfile 构建并运行。
# 构建上下文 = backend/（见仓库根 render.yaml 的 dockerContext）。
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONPATH=/app

# fastembed 的 ONNX 运行时在 CPU 上需要 libgomp1；ca-certificates 保证出网 HTTPS（DeepSeek/硅基流动/Neon）
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先装依赖（利用 Docker 层缓存）
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 源码（含 app/kb/*.json 语料）；相对路径 app/kb/docs.json、./chroma_db 都以 /app 为 CWD 解析
COPY app ./app

EXPOSE 8000

# Render 会注入 $PORT（默认 10000）；shell 形式让 $PORT 展开
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
