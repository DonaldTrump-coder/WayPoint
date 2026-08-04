@echo off
REM ============================================
REM  Waypoint - Windows 一键启动脚本
REM  首次运行会自动创建 venv 并安装依赖
REM ============================================
cd /d "%~dp0"

echo.
echo  🚀 Waypoint 启动中...
echo.

REM ---- 1. Python venv ----
if not exist ".venv\Scripts\python.exe" (
    echo  [1/3] 创建 Python 环境...
    python -m venv .venv || goto :err
)
if not exist ".venv\Scripts\fastapi.exe" (
    if exist ".venv\Scripts\python.exe" (
        echo  [1/3] 安装依赖...
        ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q || goto :err
    )
)

REM ---- 2. 前端构建 ----
if not exist "frontend\dist\index.html" (
    if exist "frontend\package.json" (
        echo  [2/3] 构建前端...
        pushd frontend
        call npm install --silent
        call npm run build
        popd
    )
)

REM ---- 3. 启动 ----
echo  [3/3] 启动服务: http://localhost:8600
echo.
start "" http://localhost:8600
".venv\Scripts\python.exe" app.py
goto :eof

:err
echo.
echo  ❌ 启动失败，请检查上方错误信息
pause
