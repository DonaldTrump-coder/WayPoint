
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import Project, Subtask, Task, task_labels
from schemas import (
    SubtaskCreate,
    SubtaskOut,
    SubtaskUpdate,
    TaskCreate,
    TaskMove,
    TaskOut,
    TaskProgressDelta,
    TaskUpdate,
)

router = APIRouter(tags=["tasks"])


def _get_task_or_404(db: Session, task_id: int) -> Task:
    task = (
        db.query(Task)
        .options(joinedload(Task.subtasks), joinedload(Task.labels))
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(404, "任务不存在")
    return task


def _recalc_progress(db: Session, task: Task):
    total = len(task.subtasks)
    if not total:
        return
    done = sum(1 for s in task.subtasks if s.done)
    task.progress = round(done / total * 100)
    if done == total:
        task.status = "done"
    elif done == 0:
        task.status = "backlog"
    else:
        task.status = "in_progress"


def _expand_project_to_tasks(db: Session, project_id: int):
    project = db.get(Project, project_id)
    if not project:
        return
    task_bounds = (
        db.query(
            func.min(Task.start_date),
            func.max(
                func.coalesce(Task.due_date, Task.start_date)
            ),
        )
        .filter(Task.project_id == project_id)
        .one()
    )
    min_start, max_end = task_bounds
    changed = False
    if min_start and (project.start_date is None or min_start < project.start_date):
        project.start_date = min_start
        changed = True
    if max_end and (project.end_date is None or max_end > project.end_date):
        project.end_date = max_end
        changed = True
    if changed:
        db.add(project)


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
def list_tasks(
    project_id: int,
    status: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    query = (
        db.query(Task)
        .options(joinedload(Task.subtasks), joinedload(Task.labels))
        .filter(Task.project_id == project_id)
    )
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if q:
        query = query.filter(Task.title.ilike(f"%{q}%"))
    return query.order_by(Task.kanban_order, Task.created_at).all()


@router.post("/projects/{project_id}/tasks", response_model=TaskOut, status_code=201)
def create_task(project_id: int, payload: TaskCreate, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    max_order = (
        db.query(Task)
        .filter(Task.project_id == project_id, Task.status == payload.status)
        .order_by(Task.kanban_order.desc())
        .first()
    )
    task = Task(
        project_id=project_id,
        **payload.model_dump(),
        kanban_order=(max_order.kanban_order + 1 if max_order else 0),
    )
    db.add(task)
    db.commit()
    _expand_project_to_tasks(db, project_id)
    db.commit()
    return _get_task_or_404(db, task.id)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return _get_task_or_404(db, task_id)


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id)
    data = payload.model_dump(exclude_unset=True)
    label_ids = data.pop("label_ids", None)
    for k, v in data.items():
        setattr(task, k, v)
    if label_ids is not None:
        from models import Label

        labels = db.query(Label).filter(Label.id.in_(label_ids)).all()
        task.labels = labels
    db.commit()
    _expand_project_to_tasks(db, task.project_id)
    db.commit()
    return _get_task_or_404(db, task_id)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    db.delete(task)
    db.commit()


@router.post("/tasks/{task_id}/move", response_model=TaskOut)
def move_task(task_id: int, payload: TaskMove, db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id)
    if task.status == payload.to_status:
        task.kanban_order = payload.order
    else:
        task.status = payload.to_status
        max_order = (
            db.query(Task)
            .filter(Task.project_id == task.project_id, Task.status == payload.to_status)
            .order_by(Task.kanban_order.desc())
            .first()
        )
        task.kanban_order = (max_order.kanban_order + 1 if max_order else 0)
    db.commit()
    return _get_task_or_404(db, task_id)


@router.post("/tasks/{task_id}/progress", response_model=TaskOut)
def adjust_progress(task_id: int, payload: TaskProgressDelta, db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id)
    task.progress = max(0, min(100, task.progress + payload.delta))
    db.commit()
    return _get_task_or_404(db, task_id)


@router.post("/tasks/{task_id}/subtasks", response_model=SubtaskOut, status_code=201)
def create_subtask(task_id: int, payload: SubtaskCreate, db: Session = Depends(get_db)):
    task = _get_task_or_404(db, task_id)
    max_order = (
        db.query(Subtask)
        .filter(Subtask.task_id == task_id)
        .order_by(Subtask.order.desc())
        .first()
    )
    st = Subtask(task_id=task_id, **payload.model_dump(), order=(max_order.order + 1 if max_order else 0))
    db.add(st)
    db.commit()
    task = _get_task_or_404(db, task_id)
    _recalc_progress(db, task)
    db.commit()
    db.refresh(st)
    return st


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskOut)
def update_subtask(subtask_id: int, payload: SubtaskUpdate, db: Session = Depends(get_db)):
    st = db.get(Subtask, subtask_id)
    if not st:
        raise HTTPException(404, "子任务不存在")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(st, k, v)
    db.commit()
    if "done" in payload.model_dump(exclude_unset=True):
        task = _get_task_or_404(db, st.task_id)
        _recalc_progress(db, task)
        db.commit()
    db.refresh(st)
    return st


@router.delete("/subtasks/{subtask_id}", status_code=204)
def delete_subtask(subtask_id: int, db: Session = Depends(get_db)):
    st = db.get(Subtask, subtask_id)
    if not st:
        raise HTTPException(404, "子任务不存在")
    task_id = st.task_id
    db.delete(st)
    db.commit()
    task = _get_task_or_404(db, task_id)
    _recalc_progress(db, task)
    db.commit()
