
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent


def _resolve_data_dir() -> Path:
    env = os.environ.get("WAYPOINT_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        return exe_dir / "data"
    return BASE_DIR


DATA_DIR = _resolve_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "waypoint.db"
BACKUP_DIR = DATA_DIR / "backups"


def _migrate_legacy_db():
    if DB_PATH.exists():
        return
    import shutil

    legacy_candidates = []
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        legacy_candidates.append(exe_dir / "waypoint.db")
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
            legacy_candidates.append(Path(appdata) / "Waypoint" / "waypoint.db")
    legacy_candidates.append(BASE_DIR / "waypoint.db")

    for legacy in legacy_candidates:
        if legacy.exists():
            shutil.copy2(legacy, DB_PATH)
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
            print(f"[迁移] 旧数据库 {legacy} -> {DB_PATH}")
            return


_migrate_legacy_db()

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    BACKUP_DIR.mkdir(exist_ok=True)
    from models import AIConfig
    from models import CalendarEvent  # noqa: F401
    from models import ChatMessage  # noqa: F401
    from models import ChatState  # noqa: F401
    from models import KanbanColumn  # noqa: F401
    from models import Label  # noqa: F401
    from models import Project  # noqa: F401
    from models import Subtask  # noqa: F401
    from models import Task  # noqa: F401
    from models import TaskNote  # noqa: F401
    from models import task_labels  # noqa: F401

    Base.metadata.create_all(engine)
    _migrate_columns()


def _migrate_columns():
    import sqlite3

    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        migrations = [
            ("ai_configs", "models_cache", 'TEXT DEFAULT "[]"'),
        ]
        for table, col, definition in migrations:
            try:
                cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
            except sqlite3.OperationalError:
                continue
            if col not in cols:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")
                conn.commit()
                print(f"[migrate] {table}.{col} 列已添加")
    finally:
        conn.close()
