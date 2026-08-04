
import os
import shutil
import sys
import threading
import webbrowser
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import BACKUP_DIR, DATA_DIR, DB_PATH, init_db
from routers import projects, tasks, kanban, settings, agent, calendar, notes

BASE_DIR = Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    DIST_DIR = Path(sys._MEIPASS) / "dist"
else:
    DIST_DIR = BASE_DIR / "frontend" / "dist"


def backup_db():
    if not DB_PATH.exists():
        return
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy2(DB_PATH, BACKUP_DIR / f"waypoint_{stamp}.db")
    backups = sorted(BACKUP_DIR.glob("waypoint_*.db"))
    for old in backups[:-30]:
        old.unlink()


@asynccontextmanager
async def lifespan(app: FastAPI):
    backup_db()
    init_db()
    yield


app = FastAPI(title="Waypoint", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(kanban.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(notes.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Not Found"}, status_code=404)
        candidate = DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(DIST_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    port = int(os.environ.get("WAYPOINT_PORT", "8600"))
    url = f"http://localhost:{port}"

    print("=" * 52)
    print("  Waypoint 已启动")
    print(f"  请在浏览器打开: {url}")
    print(f"  数据目录: {DATA_DIR}")
    print("  关闭本窗口即停止服务")
    print("=" * 52)

    threading.Timer(1.2, lambda: webbrowser.open(url)).start()

    uvicorn.run(app, host="127.0.0.1", port=port)
