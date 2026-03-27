#!/bin/bash

# 血染钟楼助手 - 启动脚本

echo "================================"
echo "血染钟楼 · 说书人助手"
echo "================================"
echo ""

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

# 检查是否需要迁移
if [ ! -f "data/botc.db" ]; then
    echo ""
    echo "检测到首次运行，开始数据迁移..."
    python migrate.py
fi

# 启动应用
echo ""
echo "启动应用..."
echo "访问地址: http://localhost:5555"
echo "外网地址: https://botc-assistant-py.loca.lt"
echo "按 Ctrl+C 停止服务"
echo ""

# 后台启动 Flask
python app_new.py &
FLASK_PID=$!

# 等待两秒让 Flask 先起来
sleep 2

# 启动内网穿透
npx localtunnel --port 5555 --subdomain botc-assistant-py

# 如果 localtunnel 退出，顺便杀掉后端的 Flask
kill $FLASK_PID
