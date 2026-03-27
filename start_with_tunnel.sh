#!/bin/bash

set -euo pipefail

APP_PORT="${PORT:-5555}"
APP_HOST="${HOST:-127.0.0.1}"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT_DIR/.run"
APP_LOG="$LOG_DIR/flask.log"
TUNNEL_LOG="$LOG_DIR/cloudflared.log"
APP_PID_FILE="$LOG_DIR/flask.pid"
TUNNEL_PID_FILE="$LOG_DIR/cloudflared.pid"

mkdir -p "$LOG_DIR"

cd "$ROOT_DIR"

echo "================================"
echo "血染钟楼 · 说书人助手"
echo "一键启动 Flask + Tunnel"
echo "================================"
echo ""

if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "检查依赖..."
pip install -q -r requirements.txt

if ! command -v cloudflared >/dev/null 2>&1; then
    echo "未检测到 cloudflared。"
    echo "请先安装：brew install cloudflared"
    exit 1
fi

cleanup() {
    echo ""
    echo "正在停止服务..."
    if [ -n "${TUNNEL_PID:-}" ] && kill -0 "$TUNNEL_PID" 2>/dev/null; then
        kill "$TUNNEL_PID" 2>/dev/null || true
    fi
    if [ -n "${APP_PID:-}" ] && kill -0 "$APP_PID" 2>/dev/null; then
        kill "$APP_PID" 2>/dev/null || true
    fi
    rm -f "$APP_PID_FILE" "$TUNNEL_PID_FILE"
}

trap cleanup EXIT INT TERM

if lsof -tiTCP:"$APP_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "端口 $APP_PORT 已被占用，先尝试自动清理旧进程..."
    if [ -x "./stop.sh" ]; then
        ./stop.sh || true
        sleep 1
    fi
fi

if lsof -tiTCP:"$APP_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "端口 $APP_PORT 仍被占用，请手动处理。"
    lsof -nP -iTCP:"$APP_PORT" -sTCP:LISTEN
    exit 1
fi

echo "启动 Flask..."
PORT="$APP_PORT" python app_new.py >"$APP_LOG" 2>&1 &
APP_PID=$!
echo "$APP_PID" > "$APP_PID_FILE"

for _ in $(seq 1 30); do
    if curl -fsS "http://$APP_HOST:$APP_PORT/" >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! curl -fsS "http://$APP_HOST:$APP_PORT/" >/dev/null 2>&1; then
    echo "Flask 启动失败，请查看日志：$APP_LOG"
    exit 1
fi

echo "本地地址: http://$APP_HOST:$APP_PORT"
echo "启动 Cloudflare Tunnel..."

cloudflared tunnel --url "http://$APP_HOST:$APP_PORT" --protocol http2 >"$TUNNEL_LOG" 2>&1 &
TUNNEL_PID=$!
echo "$TUNNEL_PID" > "$TUNNEL_PID_FILE"

TUNNEL_URL=""
for _ in $(seq 1 30); do
    if ! kill -0 "$TUNNEL_PID" 2>/dev/null; then
        echo "Tunnel 启动失败，请查看日志：$TUNNEL_LOG"
        exit 1
    fi

    TUNNEL_URL="$(sed -nE 's#.*(https://[a-z0-9-]+\.trycloudflare\.com).*#\1#p' "$TUNNEL_LOG" | tail -n 1)"
    if [ -n "$TUNNEL_URL" ]; then
        break
    fi
    sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
    echo "未拿到 Tunnel 地址，请查看日志：$TUNNEL_LOG"
    exit 1
fi

echo ""
echo "公网地址: $TUNNEL_URL"
echo "日志文件:"
echo "  Flask: $APP_LOG"
echo "  Tunnel: $TUNNEL_LOG"
echo ""
echo "按 Ctrl+C 停止全部服务"
echo ""

tail -n +1 -f "$TUNNEL_LOG"
