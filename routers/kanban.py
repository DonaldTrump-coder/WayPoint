
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import KanbanColumn, Project, Task
from schemas import (
    ColumnReorder,
    KanbanColumnCreate,
    KanbanColumnOut,
    KanbanColumnUpdate,
)

router = APIRouter(tags=["kanban"])


def _get_column_or_404(db: Session, col_id: int) -> KanbanColumn:
    col = db.get(KanbanColumn, col_id)
    if not col:
        raise HTTPException(404, "列不存在")
    return col


@router.get("/projects/{project_id}/columns", response_model=list[KanbanColumnOut])
def list_columns(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    columns = (
        db.query(KanbanColumn)
        .filter(KanbanColumn.project_id == project_id)
        .order_by(KanbanColumn.order)
        .all()
    )
    tasks = (
        db.query(Task)
        .options(joinedload(Task.subtasks), joinedload(Task.labels))
        .filter(Task.project_id == project_id)
        .order_by(Task.kanban_order, Task.created_at)
        .all()
    )
    by_status: dict[str, list[Task]] = {}
    for t in tasks:
        by_status.setdefault(t.status, []).append(t)
    for col in columns:
        col._tasks = by_status.get(col.status, [])
    return _serialize(columns)


def _serialize(columns: list[KanbanColumn]) -> list[dict]:
    out = []
    for col in columns:
        d = {
            "id": col.id,
            "project_id": col.project_id,
            "name": col.name,
            "status": col.status,
            "order": col.order,
            "wip_limit": col.wip_limit,
        }
        tasks = getattr(col, "_tasks", [])
        d["tasks"] = [
            {
                "id": t.id,
                "project_id": t.project_id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "start_date": t.start_date.isoformat() if t.start_date else None,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "progress": t.progress,
                "is_milestone": t.is_milestone,
                "kanban_order": t.kanban_order,
                "assignee": t.assignee,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
                "subtasks": [
                    {
                        "id": s.id,
                        "task_id": s.task_id,
                        "title": s.title,
                        "done": s.done,
                        "order": s.order,
                    }
                    for s in t.subtasks
                ],
                "labels": [
                    {"id": l.id, "name": l.name, "color": l.color} for l in t.labels
                ],
            }
            for t in tasks
        ]
        out.append(d)
    return out


@router.post("/projects/{project_id}/columns", response_model=KanbanColumnOut, status_code=201)
def create_column(
    project_id: int, payload: KanbanColumnCreate, db: Session = Depends(get_db)
):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    max_order = (
        db.query(KanbanColumn)
        .filter(KanbanColumn.project_id == project_id)
        .order_by(KanbanColumn.order.desc())
        .first()
    )
    col = KanbanColumn(
        project_id=project_id, **payload.model_dump(), order=(max_order.order + 1 if max_order else 0)
    )
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.patch("/kanban/columns/{column_id}", response_model=KanbanColumnOut)
def update_column(
    column_id: int, payload: KanbanColumnUpdate, db: Session = Depends(get_db)
):
    col = _get_column_or_404(db, column_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(col, k, v)
    db.commit()
    db.refresh(col)
    return col


@router.delete("/kanban/columns/{column_id}", status_code=204)
def delete_column(column_id: int, db: Session = Depends(get_db)):
    col = _get_column_or_404(db, column_id)
    sibling = (
        db.query(KanbanColumn)
        .filter(
            KanbanColumn.project_id == col.project_id,
            KanbanColumn.id != col.id,
        )
        .order_by(KanbanColumn.order)
        .first()
    )
    if sibling:
        db.query(Task).filter(
            Task.project_id == col.project_id, Task.status == col.status
        ).update({Task.status: sibling.status})
    db.delete(col)
    db.commit()


@router.post("/projects/{project_id}/columns/reorder", status_code=204)
def reorder_columns(
    project_id: int, payload: ColumnReorder, db: Session = Depends(get_db)
):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    for i, cid in enumerate(payload.column_ids):
        col = db.get(KanbanColumn, cid)
        if col and col.project_id == project_id:
            col.order = i
    db.commit()
