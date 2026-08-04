
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _check_date_range(start, end, label: str):
    if start is not None and end is not None and start > end:
        raise ValueError(f"{label}的开始日期不能晚于结束日期（{start} > {end}）")


# ---------- Project ----------
class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    color: str = "#409EFF"
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def _check_dates(self):
        _check_date_range(self.start_date, self.end_date, "项目")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    color: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode="after")
    def _check_dates(self):
        _check_date_range(self.start_date, self.end_date, "项目")
        return self


class ProjectStats(BaseModel):
    total_tasks: int = 0
    done_tasks: int = 0
    overdue_tasks: int = 0
    progress: int = 0


class ProjectOut(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    stats: Optional[ProjectStats] = None


# ---------- Subtask ----------
class SubtaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)


class SubtaskCreate(SubtaskBase):
    pass


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


class SubtaskOut(SubtaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    done: bool
    order: int


# ---------- Task ----------
class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    status: str = "backlog"
    priority: str = "medium"
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    is_milestone: bool = False
    assignee: Optional[str] = None

    @model_validator(mode="after")
    def _check_dates(self):
        _check_date_range(self.start_date, self.due_date, "任务")
        return self


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    is_milestone: Optional[bool] = None
    assignee: Optional[str] = None
    label_ids: Optional[List[int]] = None

    @model_validator(mode="after")
    def _check_dates(self):
        _check_date_range(self.start_date, self.due_date, "任务")
        return self


class TaskMove(BaseModel):
    to_status: str
    order: int = 0


class TaskProgressDelta(BaseModel):
    delta: int = Field(ge=-100, le=100)


class TaskOut(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    progress: int
    kanban_order: int
    created_at: datetime
    updated_at: datetime
    subtasks: List[SubtaskOut] = []
    labels: List["LabelOut"] = []


# ---------- Label ----------
class LabelBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = "#909399"


class LabelCreate(LabelBase):
    pass


class LabelOut(LabelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


# ---------- KanbanColumn ----------
class KanbanColumnBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    status: str
    wip_limit: Optional[int] = Field(default=None, ge=1)


class KanbanColumnCreate(KanbanColumnBase):
    pass


class KanbanColumnUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    wip_limit: Optional[int] = None


class KanbanColumnOut(KanbanColumnBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    order: int
    tasks: List[TaskOut] = []


class ColumnReorder(BaseModel):
    column_ids: List[int]


# ---------- AI Config ----------
class AIConfigBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    base_url: str
    api_key: str = ""
    model: str = ""
    temperature: int = Field(default=70, ge=0, le=100)


class AIConfigCreate(AIConfigBase):
    pass


class AIConfigUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[int] = Field(default=None, ge=0, le=100)


class AIConfigOut(BaseModel):

    id: int
    name: str
    base_url: str
    model: str
    temperature: int
    is_default: bool
    api_key_masked: str
    models_cache: List[str] = []


class AIConfigTestResult(BaseModel):
    ok: bool
    latency_ms: Optional[int] = None
    models: List[str] = []
    error: Optional[str] = None


class AIConfigSelect(BaseModel):

    provider_id: int
    model: str


TaskOut.model_rebuild()


# ---------- Calendar ----------
class CalendarEventCreate(BaseModel):
    date: date
    title: str = Field(min_length=1, max_length=200)
    color: str = "#E8A33D"


class CalendarEventOut(BaseModel):

    id: str
    date: date
    title: str
    color: str
    kind: str  # manual / task_due / project_end
    project_name: str = ""
    deletable: bool = False


class CalendarDaySummary(BaseModel):
    date: date
    event_count: int
    has_important: bool
    events: list[CalendarEventOut] = []
