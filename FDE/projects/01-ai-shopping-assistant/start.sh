#!/usr/bin/env bash
set -euo pipefail

# ╔══════════════════════════════════════════════════════════════╗
# ║     乐高智能导购助手 — macOS / Linux 一键启动脚本            ║
# ║     LEGO Smart Shopping Assistant Starter                    ║
# ╚══════════════════════════════════════════════════════════════╝

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

log_info()  { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step()  { echo -e "\n${CYAN}=== $1 ===${NC}"; }

usage() {
    cat <<'EOF'
用法: ./start.sh [local|docker|stop|ingest|help]

  local   默认，本地启动后端 + 客户端 + 客服端（推荐）
  docker  使用 Docker Compose 启动后端
  stop    停止 Docker 服务
  ingest  重建向量库
  help    显示帮助

首次运行会自动：
  1. 从 .env.example 生成 .env
  2. uv sync 安装 Python 依赖
  3. npm ci 安装两个前端依赖
  4. 检查/拉取 Ollama 模型
  5. 初始化 SQLite 并构建向量库
EOF
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        log_error "未找到命令：$1"
        echo "  $2"
        exit 1
    fi
}

ensure_env() {
    if [ ! -f .env ]; then
        cp .env.example .env
        log_info "已从 .env.example 创建 .env"
    fi
}

sync_python() {
    require_cmd uv "安装 uv：curl -LsSf https://astral.sh/uv/install.sh | sh"
    log_step "同步 Python 依赖"
    uv sync --extra dev
}

sync_frontend() {
    require_cmd npm "安装 Node.js：https://nodejs.org 或 brew install node"
    for dir in public admin; do
        if [ ! -d "$dir/node_modules" ]; then
            log_step "安装前端依赖：$dir"
            (cd "$dir" && npm ci --no-audit --no-fund)
        fi
    done
}

ensure_ollama() {
    if ! command -v ollama >/dev/null 2>&1; then
        log_warn "未安装 Ollama：聊天功能不可用，但 API/前端仍可启动。"
        log_warn "macOS: brew install ollama   或访问 https://ollama.com/download"
        return
    fi

    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        log_warn "Ollama 未运行，正在启动..."
        (ollama serve >/tmp/ollama-serve.log 2>&1 &)
        sleep 3
    fi

    local models
    models="$(ollama list 2>/dev/null || true)"
    local needed="qwen2.5:3b"
    if grep -q '^EMBED_PROVIDER=ollama' .env 2>/dev/null; then
        needed="$needed bge-m3:latest"
    fi

    for model in $needed; do
        if ! echo "$models" | grep -q "$model"; then
            log_step "拉取 Ollama 模型：$model"
            ollama pull "$model"
        fi
    done
}

ensure_data() {
    log_step "初始化本地 SQLite 商品/库存数据"
    uv run python scripts/init_db.py

    local provider="hash"
    if grep -q '^EMBED_PROVIDER=' .env 2>/dev/null; then
        provider="$(grep '^EMBED_PROVIDER=' .env | head -n1 | cut -d= -f2 | tr -d '[:space:]')"
    fi

    if [ ! -f "db/.ingest_${provider}" ]; then
        log_step "构建向量库（首次运行）"
        uv run python main.py ingest
    fi
}

start_local() {
    ensure_env
    sync_python
    sync_frontend
    ensure_ollama
    ensure_data

    log_step "启动服务"
    uv run python main.py serve &
    BACKEND_PID=$!

    (cd public && npm run dev) &
    PUBLIC_PID=$!

    (cd admin && npm run dev) &
    ADMIN_PID=$!

    trap 'log_info "正在关闭所有服务..."; kill $BACKEND_PID $PUBLIC_PID $ADMIN_PID 2>/dev/null || true; exit 0' INT TERM

    echo ""
    log_info "后端 API:    http://localhost:8000"
    log_info "API 文档:    http://localhost:8000/docs"
    log_info "客户端聊天:  http://localhost:3000"
    log_info "客服端:      http://localhost:3001"
    echo ""
    log_info "按 Ctrl+C 停止所有服务"

    wait
}

start_docker() {
    require_cmd docker "安装 Docker Desktop：https://www.docker.com/products/docker-desktop/"
    log_step "Docker Compose 启动"
    docker compose up -d --build

    log_info "拉取 Ollama 模型（容器内）..."
    docker compose exec -T ollama ollama pull qwen2.5:3b || true

    log_info "构建容器内向量库..."
    docker compose exec -T backend uv run python main.py ingest || true

    echo ""
    log_info "后端 API: http://localhost:8000"
    log_info "前端请本地启动：cd public && npm run dev"
    log_info "                cd admin  && npm run dev"
}

stop_docker() {
    if command -v docker >/dev/null 2>&1; then
        docker compose down
        log_info "Docker 服务已停止"
    else
        log_warn "未安装 Docker，无需停止"
    fi
}

do_ingest() {
    ensure_env
    sync_python
    log_step "重建向量库"
    uv run python main.py ingest
}

case "${1:-local}" in
    local)   start_local ;;
    docker)  start_docker ;;
    stop)    stop_docker ;;
    ingest)  do_ingest ;;
    help|-h|--help) usage ;;
    *)
        log_error "未知命令: $1"
        usage
        exit 1
        ;;
esac
