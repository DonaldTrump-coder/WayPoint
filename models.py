
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base

STATUSES = ["backlog", "todo", "in_progress", "review", "done"]
PRIORITIES = ["low", "medium", "high", "urgent"]

task_labels = Table(
    "task_labels",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="active")  # active / archived
    color = Column(String(20), default="#409EFF")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    columns = relationship(
        "KanbanColumn",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="KanbanColumn.order",
    )


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    project_id = Column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="backlog", index=True)
    priority = Column(String(10), default="medium")
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    progress = Column(Integer, default=0)  # 0-100
    is_milestone = Column(Boolean, default=False)
    kanban_order = Column(Integer, default=0)
    assignee = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("Project", back_populates="tasks")
    subtasks = relationship(
        "Subtask",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="Subtask.order",
    )
    note = relationship(
        "TaskNote",
        back_populates="task",
        cascade="all, delete-orphan",
        uselist=False,
    )
    labels = relationship("Label", secondary=task_labels, back_populates="tasks")


class Subtask(Base):

    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(300), nullable=False)
    done = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    task = relationship("Task", back_populates="subtasks")


class TaskNote(Base):

    __tablename__ = "task_notes"

    id = Column(Integer, primary_key=True)
    task_id = Column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True)
    content = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    task = relationship("Task", back_populates="note")


class KanbanColumn(Base):

    __tablename__ = "kanban_columns"

    id = Column(Integer, primary_key=True)
    project_id = Column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False)
    order = Column(Integer, default=0)
    wip_limit = Column(Integer, nullable=True)

    project = relationship("Project", back_populates="columns")


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), default="#909399")

    tasks = relationship("Task", secondary=task_labels, back_populates="labels")


class AIConfig(Base):

    __tablename__ = "ai_configs"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    base_url = Column(String(300), nullable=False)
    api_key = Column(String(300), default="")
    model = Column(String(100), default="")
    temperature = Column(Integer, default=70)
    is_default = Column(Boolean, default=False)
    models_cache = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.now)


class CalendarEvent(Base):

    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    color = Column(String(20), default="#E8A33D")
    created_at = Column(DateTime, default=datetime.now)


class ChatMessage(Base):

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    role = Column(String(20), nullable=False)  # user / assistant
    content = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)


class ChatState(Base):

    __tablename__ = "chat_state"

    id = Column(Integer, primary_key=True)
    thinking = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.now)
