#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT_DIR/.run"
APP_PID_FILE="$LOG_DIR/flask.pid"
TUNNEL_PID_FILE="$LOG_DIR/cloudflared.pid"
APP_PORT="${PORT:-5555}"

stop_pid_file() {
    local pid_file="$1"
    local name="$2"

    if [ ! -f "$pid_file" ]; then
        echo "$name: 未找到 PID 文件"
        return
    fi

    local pid
    pid="$(cat "$pid_file")"

    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null || true
        echo "$name: 已停止 (PID $pid)"
    else
        echo "$name: 进程不存在，清理 PID 文件"
    fi

    rm -f "$pid_file"
}

stop_port_processes() {
    local port="$1"
    local name="$2"
    local pids

    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -z "$pids" ]; then
        echo "$name: 端口 $port 没有监听进程"
        return
    fi

    for pid in $pids; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            echo "$name: 已停止端口 $port 进程 (PID $pid)"
        fi
    done
}

echo "停止血染钟楼助手相关服务..."

stop_pid_file "$TUNNEL_PID_FILE" "Cloudflare Tunnel"
stop_pid_file "$APP_PID_FILE" "Flask"
stop_port_processes "$APP_PORT" "Flask"

echo "完成"
