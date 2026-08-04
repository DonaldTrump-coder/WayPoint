
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import KanbanColumn, Project, STATUSES, Task
from schemas import ProjectCreate, ProjectOut, ProjectStats, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

DEFAULT_COLUMNS = [
    ("待办", "backlog"),
    ("进行中", "in_progress"),
    ("已完成", "done"),
]


def _compute_stats(db: Session, project_id: int) -> ProjectStats:
    total = db.query(func.count(Task.id)).filter(Task.project_id == project_id).scalar() or 0
    done = (
        db.query(func.count(Task.id))
        .filter(Task.project_id == project_id, Task.status == "done")
        .scalar()
        or 0
    )
    overdue = (
        db.query(func.count(Task.id))
        .filter(
            Task.project_id == project_id,
            Task.status != "done",
            Task.due_date.isnot(None),
            Task.due_date < date.today(),
        )
        .scalar()
        or 0
    )
    progress = round(done / total * 100) if total else 0
    return ProjectStats(
        total_tasks=total, done_tasks=done, overdue_tasks=overdue, progress=progress
    )


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    for p in projects:
        p.stats = _compute_stats(db, p.id)
    return projects


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**payload.model_dump())
    db.add(project)
    db.flush()
    for i, (name, status) in enumerate(DEFAULT_COLUMNS):
        db.add(
            KanbanColumn(project_id=project.id, name=name, status=status, order=i)
        )
    db.commit()
    db.refresh(project)
    project.stats = _compute_stats(db, project.id)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    project.stats = _compute_stats(db, project_id)
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    data = payload.model_dump(exclude_unset=True)
    if "start_date" in data or "end_date" in data:
        bounds = (
            db.query(
                func.min(Task.start_date),
                func.max(func.coalesce(Task.due_date, Task.start_date)),
            )
            .filter(Task.project_id == project_id)
            .one()
        )
        min_start, max_end = bounds
        new_start = data.get("start_date", project.start_date)
        new_end = data.get("end_date", project.end_date)
        if min_start and new_start and new_start > min_start:
            raise HTTPException(
                422,
                f"项目开始日期不能晚于最早的任务开始日期（{min_start}），请先调整任务时间",
            )
        if max_end and new_end and new_end < max_end:
            raise HTTPException(
                422,
                f"项目结束日期不能早于最晚的任务截止日期（{max_end}），请先调整任务时间",
            )
    for k, v in data.items():
        setattr(project, k, v)
    db.commit()
    db.refresh(project)
    project.stats = _compute_stats(db, project_id)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    db.delete(project)
    db.commit()


@router.get("/{project_id}/stats", response_model=ProjectStats)
def project_stats(project_id: int, db: Session = Depends(get_db)):
    if not db.get(Project, project_id):
        raise HTTPException(404, "项目不存在")
    return _compute_stats(db, project_id)
