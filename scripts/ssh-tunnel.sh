#!/bin/sh
# SSH 隧道管理脚本 — 连接远端 PostgreSQL
# 用法:
#   ./scripts/ssh-tunnel.sh start   建立隧道
#   ./scripts/ssh-tunnel.sh stop    关闭隧道
#   ./scripts/ssh-tunnel.sh status  查看状态

REMOTE_HOST="${SSH_TUNNEL_HOST:-user@remote-host}"
LOCAL_PORT="${SSH_TUNNEL_LOCAL_PORT:-5434}"
REMOTE_PORT="${SSH_TUNNEL_REMOTE_PORT:-5434}"

is_alive() {
    lsof -ti:"$LOCAL_PORT" -sTCP:LISTEN >/dev/null 2>&1
}

case "${1:-status}" in
    start)
        if is_alive; then
            echo "隧道已在运行 (本地端口 $LOCAL_PORT)"
            exit 0
        fi
        ssh -fNL "$LOCAL_PORT:localhost:$REMOTE_PORT" "$REMOTE_HOST"
        if is_alive; then
            echo "隧道已建立: localhost:$LOCAL_PORT -> $REMOTE_HOST:localhost:$REMOTE_PORT"
        else
            echo "隧道建立失败，请检查 SSH 连接: $REMOTE_HOST" >&2
            exit 1
        fi
        ;;
    stop)
        if ! is_alive; then
            echo "隧道未运行"
            exit 0
        fi
        pid=$(lsof -ti:"$LOCAL_PORT" -sTCP:LISTEN)
        kill "$pid" 2>/dev/null
        echo "隧道已关闭"
        ;;
    status)
        if is_alive; then
            pid=$(lsof -ti:"$LOCAL_PORT" -sTCP:LISTEN)
            echo "隧道运行中 (PID: $pid, 本地端口: $LOCAL_PORT -> $REMOTE_HOST)"
        else
            echo "隧道未运行"
        fi
        ;;
    *)
        echo "用法: $0 {start|stop|status}"
        exit 1
        ;;
esac
