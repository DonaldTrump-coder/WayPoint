#!/usr/bin/env bash
# ============================================
#  Waypoint - Linux 一键启动脚本
#  首次运行会自动创建 venv 并安装依赖
# ============================================
set -e
cd "$(dirname "$0")"

echo ""
echo "  🚀 Waypoint 启动中..."
echo ""

# ---- 1. Python venv ----
if [ ! -f ".venv/bin/python" ]; then
    echo "  [1/3] 创建 Python 环境..."
    python3 -m venv .venv
fi
if ! .venv/bin/python -c "import fastapi" 2>/dev/null; then
    echo "  [1/3] 安装依赖..."
    .venv/bin/python -m pip install -r requirements.txt -q
fi

# ---- 2. 前端构建 ----
if [ ! -f "frontend/dist/index.html" ]; then
    if [ -f "frontend/package.json" ]; then
        echo "  [2/3] 构建前端..."
        (cd frontend && npm install --silent && npm run build)
    fi
fi

# ---- 3. 启动 ----
echo "  [3/3] 启动服务: http://localhost:8600"
echo ""
(xdg-open http://localhost:8600 >/dev/null 2>&1 &) || true
.venv/bin/python app.py
