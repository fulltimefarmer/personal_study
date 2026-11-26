FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install uv

# 先复制构建项目所需的最小文件，利用 Docker 层缓存
COPY pyproject.toml uv.lock README.md ./
COPY app ./app
RUN uv sync --frozen --no-dev

# 再复制运行时数据、脚本和前端源码
COPY . .

RUN mkdir -p db/chroma

EXPOSE 8000

CMD ["uv", "run", "python", "main.py", "serve"]
