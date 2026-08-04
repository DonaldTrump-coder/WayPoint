# -*- mode: python ; coding: utf-8 -*-
"""Waypoint PyInstaller 打包配置（one-dir 模式）。

构建: cd F:\Projects\WayPoints && .venv\Scripts\pyinstaller.exe packaging\waypoint.spec
产物: dist\Waypoint\ （目录）
      ├── Waypoint.exe        # 小启动器（黑框提示地址 + 自动开浏览器）
      └── _internal\          # Python 解释器 + 全部依赖 + 前端资源
数据: exe 旁 data\ 子目录（跟随安装路径，不写 C 盘/APPDATA），卸载/升级不丢
特点: one-dir → 秒启动、零临时解压、彻底不碰系统临时目录
"""

import os
from pathlib import Path

# PyInstaller 的 SPECPATH = spec 文件所在目录（packaging/）→ parent = 项目根
ROOT = Path(SPECPATH).resolve().parent

datas = [
    (str(ROOT / "frontend" / "dist"), "dist"),       # 前端静态资源 → _MEIPASS/dist
    (str(ROOT / "icon.png"), "."),                    # 图标文件（运行时用不到，仅打包进包）
]

a = Analysis(
    [str(ROOT / "app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "uvicorn.lifespan.auto",
        "sqlalchemy.dialects.sqlite",
        "openai",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PySide6", "matplotlib", "pandas", "numpy", "PIL"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# one-dir：EXE 只含引导代码（pyz + scripts），binaries/datas 交给 COLLECT
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Waypoint",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # 黑框：显示访问地址
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "packaging" / "icon.ico"),
)

# 收集全部依赖到 dist/Waypoint/（_internal\ 子目录）
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Waypoint",
)
