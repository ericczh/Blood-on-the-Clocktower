@echo off
REM 血染钟楼助手 - Windows启动脚本

echo ================================
echo 血染钟楼 · 说书人助手
echo ================================
echo.

REM 检查虚拟环境
if not exist ".venv" (
    echo 创建虚拟环境...
    python -m venv .venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call .venv\Scripts\activate.bat

REM 安装依赖
echo 检查依赖...
pip install -q -r requirements.txt

REM 检查是否需要迁移
if not exist "data\botc.db" (
    echo.
    echo 检测到首次运行，开始数据迁移...
    python migrate.py
)

REM 启动应用
echo.
echo 启动应用...
echo 访问地址: http://localhost:5555
echo 外网地址: https://botc-assistant-py.loca.lt
echo 按 Ctrl+C 停止服务
echo.

REM 后台启动 Flask
start /B python app_new.py

REM 等待两秒让 Flask 先起来
timeout /t 2 /nobreak >nul

REM 启动内网穿透
call npx localtunnel --port 5555 --subdomain botc-assistant-py

pause
