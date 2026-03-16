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
echo "按 Ctrl+C 停止服务"
echo ""
python app_new.py
