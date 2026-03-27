#!/bin/bash

# 血染钟楼助手 - 启动脚本

echo "================================"
echo "血染钟楼 · 说书人助手"
echo "================================"
echo ""

# 检查并清理旧进程
PORT=5555
PIDS=$(lsof -ti :$PORT)
if [ -n "$PIDS" ]; then
    echo "检测到端口 $PORT 已被占用，正在清理旧进程 (PIDs: $PIDS)..."
    echo "$PIDS" | xargs kill -9 > /dev/null 2>&1
    sleep 1
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 安装依赖
echo "检查依赖..."
pip install -q -r requirements.txt

# 启动应用
echo ""
echo "🚀 正在启动服务..."
echo "📍 本地访问: http://localhost:$PORT"
echo "🌍 外网访问: https://botc-assistant-py.loca.lt"
echo "💡 如果首次访问需要密码，请输入你的公网 IP"
echo "⌨️  按 Ctrl+C 停止全部服务"
echo ""

# 后台启动 Flask
python app_new.py > /dev/null 2>&1 &
FLASK_PID=$!

# 注册退出钩子：确保退出时同时关掉 Flask
trap 'echo -e "\n正在关闭服务..."; kill $FLASK_PID 2>/dev/null; exit' INT TERM

# 等待两秒让 Flask 先起来
sleep 2

# 启动内网穿透
if ! command -v npx >/dev/null 2>&1; then
    echo "错误: 未检测到 npm/npx，请先安装 Node.js"
    kill $FLASK_PID
    exit 1
fi

npx localtunnel --port $PORT --subdomain botc-assistant-py
