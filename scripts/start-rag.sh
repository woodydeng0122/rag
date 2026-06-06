#!/bin/sh
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 加载 .env
set -a; . "$PROJECT_DIR/.env"; set +a

# --- USE_DB: local=本地Docker DB, remote=远端DB(SSH隧道) ---
if [ "$USE_DB" = "remote" ]; then
    echo "[DB] 使用远端数据库，建立 SSH 隧道..."
    "$SCRIPT_DIR/ssh-tunnel.sh" start
else
    echo "[DB] 使用本地数据库"
fi

# --- RAG_START: local=本地起服务, docker=docker起服务 ---
if [ "$RAG_START" = "docker" ]; then
    echo "[START] Docker 模式启动..."
    # Docker 启动且本地 DB 时，用 host.docker.internal
    if [ "$USE_DB" = "local" ] && [ -n "$DATABASE_URL_DOCKER" ]; then
        export DATABASE_URL="$DATABASE_URL_DOCKER"
    fi
    exec docker compose -f "$PROJECT_DIR/docker-compose.yml" up --build
else
    echo "[START] 本地模式启动..."
    if ! python -c "import rag" 2>/dev/null; then
        echo "Installing dependencies..."
        pip install -e '.[dev]'
    fi
    exec python -m rag api
fi
