
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Task, TaskNote

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteIn(BaseModel):
    content: str = ""


class NoteOut(BaseModel):
    task_id: int
    content: str
    updated_at: str | None = None


class NoteTaskNode(BaseModel):

    id: int
    title: str
    has_note: bool
    note_updated_at: str | None = None


class NoteProjectNode(BaseModel):

    id: int
    name: str
    tasks: list[NoteTaskNode]


@router.get("/tree", response_model=list[NoteProjectNode])
def note_tree(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.id).all()
    out = []
    for p in projects:
        tasks = (
            db.query(Task)
            .outerjoin(TaskNote)
            .filter(Task.project_id == p.id)
            .order_by(Task.kanban_order, Task.id)
            .all()
        )
        out.append(
            NoteProjectNode(
                id=p.id,
                name=p.name,
                tasks=[
                    NoteTaskNode(
                        id=t.id,
                        title=t.title,
                        has_note=t.note is not None and bool(t.note.content.strip()),
                        note_updated_at=t.note.updated_at.isoformat() if t.note else None,
                    )
                    for t in tasks
                ],
            )
        )
    return out


@router.get("/{task_id}", response_model=NoteOut)
def get_note(task_id: int, db: Session = Depends(get_db)):
    if not db.get(Task, task_id):
        raise HTTPException(404, "任务不存在")
    note = db.query(TaskNote).filter(TaskNote.task_id == task_id).first()
    return NoteOut(
        task_id=task_id,
        content=note.content if note else "",
        updated_at=note.updated_at.isoformat() if note else None,
    )


@router.put("/{task_id}", response_model=NoteOut)
def save_note(task_id: int, payload: NoteIn, db: Session = Depends(get_db)):
    if not db.get(Task, task_id):
        raise HTTPException(404, "任务不存在")
    note = db.query(TaskNote).filter(TaskNote.task_id == task_id).first()
    if note:
        note.content = payload.content
        note.updated_at = datetime.now()
    else:
        note = TaskNote(task_id=task_id, content=payload.content)
        db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut(
        task_id=task_id,
        content=note.content,
        updated_at=note.updated_at.isoformat(),
    )
