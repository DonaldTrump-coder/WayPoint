
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import CalendarEvent, Project, Task
from schemas import CalendarEventCreate, CalendarEventOut, CalendarDaySummary

router = APIRouter(prefix="/calendar", tags=["calendar"])

TASK_DUE_COLOR = "#E8A33D"
PROJECT_END_COLOR = "#D96C4F"


def _aggregate(db: Session, start: date, end: date) -> list[CalendarEventOut]:
    events: list[CalendarEventOut] = []

    manual = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.date >= start, CalendarEvent.date <= end)
        .order_by(CalendarEvent.date)
        .all()
    )
    for m in manual:
        events.append(
            CalendarEventOut(
                id=f"m{m.id}", date=m.date, title=m.title, color=m.color,
                kind="manual", deletable=True,
            )
        )

    tasks = (
        db.query(Task, Project.name)
        .join(Project, Task.project_id == Project.id)
        .filter(Task.due_date.isnot(None), Task.due_date >= start, Task.due_date <= end)
        .order_by(Task.due_date)
        .all()
    )
    for t, pname in tasks:
        events.append(
            CalendarEventOut(
                id=f"t{t.id}", date=t.due_date, title=f"任务截止：{t.title}",
                color=TASK_DUE_COLOR, kind="task_due", project_name=pname,
            )
        )

    projects = (
        db.query(Project)
        .filter(Project.end_date.isnot(None), Project.end_date >= start, Project.end_date <= end)
        .order_by(Project.end_date)
        .all()
    )
    for p in projects:
        events.append(
            CalendarEventOut(
                id=f"p{p.id}", date=p.end_date, title=f"项目结束：{p.name}",
                color=PROJECT_END_COLOR, kind="project_end", project_name=p.name,
            )
        )

    return events


@router.get("/events", response_model=list[CalendarEventOut])
def list_events(
    start: date, end: date, db: Session = Depends(get_db)
):
    if end < start:
        raise HTTPException(400, "end 必须不早于 start")
    return _aggregate(db, start, end)


@router.get("/today", response_model=CalendarDaySummary)
def today_summary(db: Session = Depends(get_db)):
    today = date.today()
    events = _aggregate(db, today, today)
    return CalendarDaySummary(
        date=today,
        event_count=len(events),
        has_important=len(events) > 0,
        events=events,
    )


@router.post("/events", response_model=CalendarEventOut, status_code=201)
def create_event(payload: CalendarEventCreate, db: Session = Depends(get_db)):
    ev = CalendarEvent(**payload.model_dump())
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return CalendarEventOut(
        id=f"m{ev.id}", date=ev.date, title=ev.title,
        color=ev.color, kind="manual", deletable=True,
    )


@router.delete("/events/{event_id}", status_code=204)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.get(CalendarEvent, event_id)
    if not ev:
        raise HTTPException(404, "事件不存在")
    db.delete(ev)
    db.commit()
