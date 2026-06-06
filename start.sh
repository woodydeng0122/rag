#!/bin/sh
set -e

SCRIPT_DIR="$(cd scripts && pwd)"
PROJECT_DIR="$(pwd)"

# 加载 .env
set -a; . ".env"; set +a

# --- USE_DB: local=本地Docker DB, remote=远端DB(SSH隧道) ---
if [ "$USE_DB" = "remote" ]; then
    echo "[DB] 使用远端数据库，建立 SSH 隧道..."
    "$SCRIPT_DIR/ssh-tunnel.sh" start
else
    echo "[DB] 使用本地数据库"
    docker compose -f "$PROJECT_DIR/docker-compose.db.yml" up -d
fi

# --- RAG_START: local=本地起服务, docker=docker起服务 ---
if [ "$RAG_START" = "docker" ]; then
    echo "[START] Docker 模式启动..."
    # Docker 容器内 localhost 无法访问宿主机，需替换为 host.docker.internal
    # 直接从 .env 文件读取 DATABASE_URL，避免 shell 展开 $ 符号
    if [ "$USE_DB" = "local" ] && [ -n "$DATABASE_URL_DOCKER" ]; then
        export DATABASE_URL="$DATABASE_URL_DOCKER"
    else
        RAW_DB_URL="$(grep '^DATABASE_URL=' .env | head -1 | cut -d'=' -f2-)"
        export DATABASE_URL="$(echo "$RAW_DB_URL" | sed 's/@localhost:/@host.docker.internal:/')"
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
