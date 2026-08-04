
import json
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import AIConfig, Label, Project, Subtask, Task
from schemas import (
    AIConfigCreate,
    AIConfigOut,
    AIConfigSelect,
    AIConfigTestResult,
    AIConfigUpdate,
)

router = APIRouter(tags=["ai", "settings"])

PRESETS = {
    "OpenAI": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "DeepSeek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "Moonshot": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "Ollama (本地)": {"base_url": "http://localhost:11434/v1", "model": "llama3.1"},
}


def _mask(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def _to_out(cfg: AIConfig) -> AIConfigOut:
    try:
        models_cache = json.loads(cfg.models_cache or "[]")
    except json.JSONDecodeError:
        models_cache = []
    return AIConfigOut(
        id=cfg.id,
        name=cfg.name,
        base_url=cfg.base_url,
        model=cfg.model,
        temperature=cfg.temperature,
        is_default=cfg.is_default,
        api_key_masked=_mask(cfg.api_key),
        models_cache=models_cache,
    )


@router.get("/ai/presets")
def list_presets():
    return PRESETS


@router.get("/ai/providers", response_model=list[AIConfigOut])
def list_providers(db: Session = Depends(get_db)):
    cfgs = db.query(AIConfig).order_by(AIConfig.created_at).all()
    return [_to_out(c) for c in cfgs]


@router.post("/ai/providers", response_model=AIConfigOut, status_code=201)
def create_provider(payload: AIConfigCreate, db: Session = Depends(get_db)):
    cfg = AIConfig(**payload.model_dump())
    if db.query(AIConfig).count() == 0:
        cfg.is_default = True
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return _to_out(cfg)


@router.patch("/ai/providers/{cfg_id}", response_model=AIConfigOut)
def update_provider(cfg_id: int, payload: AIConfigUpdate, db: Session = Depends(get_db)):
    cfg = db.get(AIConfig, cfg_id)
    if not cfg:
        raise HTTPException(404, "提供商不存在")
    data = payload.model_dump(exclude_unset=True)
    if data.get("api_key") is None:
        data.pop("api_key", None)
    for k, v in data.items():
        setattr(cfg, k, v)
    if "model" in data and data["model"]:
        try:
            cached = json.loads(cfg.models_cache or "[]")
        except json.JSONDecodeError:
            cached = []
        if data["model"] not in cached:
            cached.insert(0, data["model"])
            cfg.models_cache = json.dumps(cached, ensure_ascii=False)
    db.commit()
    db.refresh(cfg)
    return _to_out(cfg)


@router.delete("/ai/providers/{cfg_id}", status_code=204)
def delete_provider(cfg_id: int, db: Session = Depends(get_db)):
    cfg = db.get(AIConfig, cfg_id)
    if not cfg:
        raise HTTPException(404, "提供商不存在")
    was_default = cfg.is_default
    db.delete(cfg)
    db.commit()
    if was_default:
        rest = db.query(AIConfig).order_by(AIConfig.created_at).first()
        if rest:
            rest.is_default = True
            db.commit()


@router.post("/ai/providers/{cfg_id}/default", status_code=204)
def set_default_provider(cfg_id: int, db: Session = Depends(get_db)):
    cfg = db.get(AIConfig, cfg_id)
    if not cfg:
        raise HTTPException(404, "提供商不存在")
    db.query(AIConfig).update({AIConfig.is_default: False})
    cfg.is_default = True
    db.commit()


@router.post("/ai/providers/select", response_model=AIConfigOut)
def select_provider_model(payload: AIConfigSelect, db: Session = Depends(get_db)):
    cfg = db.get(AIConfig, payload.provider_id)
    if not cfg:
        raise HTTPException(404, "提供商不存在")
    model = payload.model.strip()
    if not model:
        raise HTTPException(400, "模型名不能为空")
    db.query(AIConfig).update({AIConfig.is_default: False})
    cfg.is_default = True
    cfg.model = model
    try:
        cached = json.loads(cfg.models_cache or "[]")
    except json.JSONDecodeError:
        cached = []
    if model not in cached:
        cached.append(model)
        cfg.models_cache = json.dumps(cached, ensure_ascii=False)
    db.commit()
    db.refresh(cfg)
    return _to_out(cfg)


@router.post("/ai/providers/{cfg_id}/test", response_model=AIConfigTestResult)
def test_provider(cfg_id: int, db: Session = Depends(get_db)):
    cfg = db.get(AIConfig, cfg_id)
    if not cfg:
        raise HTTPException(404, "提供商不存在")
    if not cfg.api_key and "ollama" not in cfg.base_url:
        raise HTTPException(400, "请先填写 API Key")
    import time

    import httpx

    url = cfg.base_url.rstrip("/") + "/models"
    headers = {}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    t0 = time.monotonic()
    try:
        resp = httpx.get(url, headers=headers, timeout=10)
        latency = int((time.monotonic() - t0) * 1000)
        if resp.status_code == 401 or resp.status_code == 403:
            return AIConfigTestResult(ok=False, error="认证失败，请检查 API Key")
        if resp.status_code != 200:
            return AIConfigTestResult(
                ok=False, error=f"HTTP {resp.status_code}: {resp.text[:120]}"
            )
        data = resp.json()
        models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
        if not models:
            models = [m.get("name") or m.get("model", "") for m in data.get("models", []) if m.get("name") or m.get("model")]
            models = [m for m in models if m]
        cfg.models_cache = json.dumps(models, ensure_ascii=False)
        db.commit()
        return AIConfigTestResult(ok=True, latency_ms=latency, models=models)
    except Exception as e:  # noqa: BLE001
        return AIConfigTestResult(ok=False, error=str(e)[:200])


@router.post("/ai/providers/{cfg_id}/models", response_model=AIConfigTestResult)
def fetch_provider_models(cfg_id: int, db: Session = Depends(get_db)):
    cfg = db.get(AIConfig, cfg_id)
    if not cfg:
        raise HTTPException(404, "提供商不存在")
    if not cfg.api_key and "ollama" not in cfg.base_url:
        raise HTTPException(400, "请先填写 API Key")
    import httpx

    url = cfg.base_url.rstrip("/") + "/models"
    headers = {}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    try:
        resp = httpx.get(url, headers=headers, timeout=10)
        if resp.status_code == 401 or resp.status_code == 403:
            return AIConfigTestResult(ok=False, error="认证失败，请检查 API Key")
        if resp.status_code != 200:
            return AIConfigTestResult(
                ok=False, error=f"HTTP {resp.status_code}: {resp.text[:120]}"
            )
        data = resp.json()
        models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
        if not models:
            models = [m.get("name") or m.get("model", "") for m in data.get("models", []) if m.get("name") or m.get("model")]
            models = [m for m in models if m]
        cfg.models_cache = json.dumps(models, ensure_ascii=False)
        db.commit()
        return AIConfigTestResult(ok=True, models=models)
    except Exception as e:  # noqa: BLE001
        return AIConfigTestResult(ok=False, error=str(e)[:200])


@router.get("/export")
def export_data(db: Session = Depends(get_db)):
    from models import AIConfig, CalendarEvent, ChatMessage, ChatState, KanbanColumn, TaskNote

    projects = db.query(Project).all()
    tasks = db.query(Task).all()
    subtasks = db.query(Subtask).all()
    labels = db.query(Label).all()
    notes = db.query(TaskNote).all()
    columns = db.query(KanbanColumn).all()
    events = db.query(CalendarEvent).all()
    ai_cfgs = db.query(AIConfig).all()
    chat_msgs = db.query(ChatMessage).order_by(ChatMessage.id).all()
    chat_state = db.query(ChatState).first()
    payload = {
        "version": 2,
        "exported_at": datetime.now().isoformat(),
        "projects": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "status": p.status,
                "color": p.color,
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "end_date": p.end_date.isoformat() if p.end_date else None,
            }
            for p in projects
        ],
        "tasks": [
            {
                "project_id": t.project_id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "start_date": t.start_date.isoformat() if t.start_date else None,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "progress": t.progress,
                "is_milestone": t.is_milestone,
                "assignee": t.assignee,
            }
            for t in tasks
        ],
        "subtasks": [
            {
                "task_id": s.task_id,
                "title": s.title,
                "done": s.done,
                "order": s.order,
            }
            for s in subtasks
        ],
        "labels": [{"name": l.name, "color": l.color} for l in labels],
        "task_notes": [
            {"task_id": n.task_id, "content": n.content}
            for n in notes
        ],
        "kanban_columns": [
            {
                "project_id": c.project_id,
                "name": c.name,
                "status": c.status,
                "order": c.order,
                "wip_limit": c.wip_limit,
            }
            for c in columns
        ],
        "calendar_events": [
            {
                "date": e.date.isoformat(),
                "title": e.title,
                "color": e.color,
            }
            for e in events
        ],
        "ai_configs": [
            {
                "name": c.name,
                "base_url": c.base_url,
                "api_key": c.api_key,
                "model": c.model,
                "temperature": c.temperature,
                "is_default": c.is_default,
                "models_cache": c.models_cache,
            }
            for c in ai_cfgs
        ],
        "chat_messages": [
            {"role": m.role, "content": m.content}
            for m in chat_msgs
        ],
        "chat_state": {
            "thinking": chat_state.thinking if chat_state else False,
        },
    }
    return payload


@router.post("/import")
def import_data(payload: dict, db: Session = Depends(get_db)):
    from models import AIConfig, CalendarEvent, ChatMessage, ChatState, KanbanColumn, TaskNote

    try:
        db.query(ChatMessage).delete()
        db.query(ChatState).delete()
        db.query(AIConfig).delete()
        db.query(CalendarEvent).delete()
        db.query(KanbanColumn).delete()
        db.query(TaskNote).delete()
        db.query(Subtask).delete()
        db.query(Task).delete()
        db.query(Project).delete()
        db.query(Label).delete()
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(500, "清理旧数据失败")

    label_map: dict[str, Label] = {}
    for ld in payload.get("labels", []):
        lbl = Label(name=ld["name"], color=ld.get("color", "#909399"))
        db.add(lbl)
        label_map[ld["name"]] = lbl
    db.flush()

    def _d(v):
        if not v:
            return None
        try:
            return date.fromisoformat(v)
        except (ValueError, TypeError):
            return None

    project_map: dict[int, int] = {}
    for pd in payload.get("projects", []):
        p = Project(
            name=pd["name"],
            description=pd.get("description", ""),
            status=pd.get("status", "active"),
            color=pd.get("color", "#409EFF"),
            start_date=_d(pd.get("start_date")),
            end_date=_d(pd.get("end_date")),
        )
        db.add(p)
        db.flush()
        project_map[pd["id"]] = p.id

    task_map: dict[int, int] = {}
    for td in payload.get("tasks", []):
        t = Task(
            project_id=project_map.get(td["project_id"]),
            title=td["title"],
            description=td.get("description", ""),
            status=td.get("status", "backlog"),
            priority=td.get("priority", "medium"),
            start_date=_d(td.get("start_date")),
            due_date=_d(td.get("due_date")),
            progress=td.get("progress", 0),
            is_milestone=td.get("is_milestone", False),
            assignee=td.get("assignee"),
        )
        db.add(t)
        db.flush()
        task_map[td.get("id", t.id)] = t.id

    for sd in payload.get("subtasks", []):
        db.add(
            Subtask(
                task_id=task_map.get(sd["task_id"]),
                title=sd["title"],
                done=sd.get("done", False),
                order=sd.get("order", 0),
            )
        )

    for nd in payload.get("task_notes", []):
        tid = task_map.get(nd["task_id"])
        if tid is not None:
            db.add(TaskNote(task_id=tid, content=nd.get("content", "")))

    for cd in payload.get("kanban_columns", []):
        pid = project_map.get(cd["project_id"])
        if pid is not None:
            db.add(
                KanbanColumn(
                    project_id=pid,
                    name=cd["name"],
                    status=cd["status"],
                    order=cd.get("order", 0),
                    wip_limit=cd.get("wip_limit"),
                )
            )

    for ed in payload.get("calendar_events", []):
        db.add(
            CalendarEvent(
                date=_d(ed.get("date")),
                title=ed.get("title", ""),
                color=ed.get("color", "#E8A33D"),
            )
        )

    for ac in payload.get("ai_configs", []):
        db.add(
            AIConfig(
                name=ac["name"],
                base_url=ac["base_url"],
                api_key=ac.get("api_key", ""),
                model=ac.get("model", ""),
                temperature=ac.get("temperature", 70),
                is_default=ac.get("is_default", False),
                models_cache=ac.get("models_cache"),
            )
        )

    for cm in payload.get("chat_messages", []):
        db.add(ChatMessage(role=cm["role"], content=cm.get("content", "")))

    cs = payload.get("chat_state") or {}
    st = db.query(ChatState).first()
    if not st:
        st = ChatState(id=1)
        db.add(st)
    st.thinking = bool(cs.get("thinking", False))

    db.commit()
    return {"imported": len(payload.get("tasks", [])), "ok": True}
