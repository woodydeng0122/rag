#!/bin/sh
# 数据库迁移脚本
# 用法: ./scripts/migrate.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 加载 .env
if [ -f "$PROJECT_DIR/.env" ]; then
    . "$PROJECT_DIR/.env"
fi

# 切换到项目目录
cd "$PROJECT_DIR"

# 激活虚拟环境
. .venv/bin/activate

# 数据库连接
if [ "${USE_DB}" = "remote" ]; then
    echo "[DB] 使用远端数据库，建立 SSH 隧道..."
    "$SCRIPT_DIR/ssh-tunnel.sh" start
else
    echo "[DB] 使用本地数据库"
fi

# 执行迁移
python -m rag migrate
