
from datetime import date, datetime

from sqlalchemy.orm import Session

from database import SessionLocal
from models import Project, Subtask, Task, TaskNote

# ---------------- Tool Schemas ----------------
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "列出所有项目及其进度统计（任务数、完成数、逾期数、进度百分比）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_project",
            "description": "创建新项目",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "项目名称"},
                    "description": {"type": "string"},
                    "color": {"type": "string", "description": "主题色 Hex，如 #409EFF"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "查询任务列表，可按项目、状态、优先级筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "项目名称（模糊匹配）"},
                    "status": {"type": "string", "description": "backlog/in_progress/done 等"},
                    "priority": {"type": "string", "description": "low/medium/high/urgent"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "在指定项目中创建任务",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "项目名称"},
                    "title": {"type": "string", "description": "任务标题"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "description": "backlog/in_progress/done 等"},
                    "priority": {"type": "string", "description": "low/medium/high/urgent"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "due_date": {"type": "string", "description": "YYYY-MM-DD，截止日期"},
                },
                "required": ["project_name", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "更新任务属性（状态、优先级、进度、日期、标题等）",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                    "priority": {"type": "string"},
                    "progress": {"type": "integer", "description": "0-100"},
                    "start_date": {"type": "string"},
                    "due_date": {"type": "string"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_task",
            "description": "在看板中移动任务到指定状态列",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "to_status": {"type": "string"},
                },
                "required": ["task_id", "to_status"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "删除任务",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_subtask",
            "description": "给任务添加子任务（checklist 项），完成子任务会自动累计任务进度",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "title": {"type": "string"},
                },
                "required": ["task_id", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_subtask",
            "description": "将子任务标记为完成（会触发父任务进度自动重算）",
            "parameters": {
                "type": "object",
                "properties": {"subtask_id": {"type": "integer"}},
                "required": ["subtask_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_project_progress",
            "description": "获取项目进度统计（任务数、完成数、逾期数、进度百分比）",
            "parameters": {
                "type": "object",
                "properties": {"project_name": {"type": "string"}},
                "required": ["project_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_task_detail",
            "description": "获取任务完整详情（含子任务列表、进度、日期、优先级、里程碑标记）",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_subtasks",
            "description": "列出任务的所有子任务（checklist 项）及完成状态",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_subtask",
            "description": "更新子任务（标记完成/未完成，或修改标题）",
            "parameters": {
                "type": "object",
                "properties": {
                    "subtask_id": {"type": "integer"},
                    "done": {"type": "boolean", "description": "true=完成 false=取消完成"},
                    "title": {"type": "string"},
                },
                "required": ["subtask_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_subtask",
            "description": "删除任务的某个子任务",
            "parameters": {
                "type": "object",
                "properties": {"subtask_id": {"type": "integer"}},
                "required": ["subtask_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_note",
            "description": "读取任务的 Markdown 笔记内容（每个任务有一篇笔记）",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "保存/覆盖任务的 Markdown 笔记内容（支持 Markdown 语法，如 # 标题、- 列表、**加粗**）",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer"},
                    "content": {"type": "string", "description": "Markdown 格式的笔记全文"},
                },
                "required": ["task_id", "content"],
            },
        },
    },
]

def _find_project(db: Session, name: str) -> Project | None:
    return (
        db.query(Project)
        .filter(Project.name.ilike(f"%{name}%"))
        .order_by(Project.created_at.desc())
        .first()
    )


def _find_task(db: Session, task_id: int) -> Task | None:
    return db.get(Task, task_id)


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def _task_summary(t: Task) -> dict:
    return {
        "id": t.id,
        "title": t.title,
        "status": t.status,
        "priority": t.priority,
        "progress": t.progress,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "project_id": t.project_id,
        "is_milestone": t.is_milestone,
    }


def execute_tool(name: str, args: dict) -> str:
    db = SessionLocal()
    try:
        if name == "list_projects":
            projects = db.query(Project).all()
            lines = []
            for p in projects:
                total = len(p.tasks)
                done = sum(1 for t in p.tasks if t.status == "done")
                progress = round(done / total * 100) if total else 0
                lines.append(
                    f"#{p.id} {p.name} [{p.status}] 进度{progress}% ({done}/{total})"
                )
            return "项目列表：\n" + ("\n".join(lines) if lines else "(暂无项目)")

        if name == "create_project":
            start = _parse_date(args.get("start_date"))
            end = _parse_date(args.get("end_date"))
            if start and end and start > end:
                return f"错误：开始日期 {start} 不能晚于结束日期 {end}"
            p = Project(name=args["name"], description=args.get("description", ""))
            if args.get("color"):
                p.color = args["color"]
            p.start_date = start
            p.end_date = end
            db.add(p)
            db.flush()
            from models import KanbanColumn

            for i, (cn, cs) in enumerate(
                [("待办", "backlog"), ("进行中", "in_progress"), ("已完成", "done")]
            ):
                db.add(KanbanColumn(project_id=p.id, name=cn, status=cs, order=i))
            db.commit()
            return f"已创建项目 #{p.id} {p.name}"

        if name == "list_tasks":
            q = db.query(Task)
            proj_name = args.get("project_name")
            if proj_name:
                proj = _find_project(db, proj_name)
                if not proj:
                    return f"未找到项目「{proj_name}」"
                q = q.filter(Task.project_id == proj.id)
            if args.get("status"):
                q = q.filter(Task.status == args["status"])
            if args.get("priority"):
                q = q.filter(Task.priority == args["priority"])
            tasks = q.order_by(Task.created_at.desc()).limit(50).all()
            if not tasks:
                return "(没有符合条件的任务)"
            return "\n".join(
                f"#{t.id} [{t.status}/{t.priority}] {t.title} (进度{t.progress}%)"
                for t in tasks
            )

        if name == "create_task":
            proj = _find_project(db, args["project_name"])
            if not proj:
                return f"错误：未找到项目「{args['project_name']}」。可先用 list_projects 查看现有项目。"
            t_start = _parse_date(args.get("start_date"))
            t_due = _parse_date(args.get("due_date"))
            if t_start and t_due and t_start > t_due:
                return f"错误：开始日期 {t_start} 不能晚于截止日期 {t_due}"
            t = Task(
                project_id=proj.id,
                title=args["title"],
                description=args.get("description", ""),
                status=args.get("status", "backlog"),
                priority=args.get("priority", "medium"),
                start_date=t_start,
                due_date=t_due,
            )
            db.add(t)
            db.commit()
            return f"已创建任务 #{t.id}「{t.title}」（项目：{proj.name}）"

        if name == "update_task":
            t = _find_task(db, args["task_id"])
            if not t:
                return f"错误：任务 #{args['task_id']} 不存在"
            for key in ("title", "description", "status", "priority", "progress"):
                if key in args and args[key] is not None:
                    setattr(t, key, args[key])
            for key in ("start_date", "due_date"):
                if key in args and args[key]:
                    setattr(t, key, _parse_date(args[key]))
            db.commit()
            return f"已更新任务 #{t.id}「{t.title}」"

        if name == "move_task":
            t = _find_task(db, args["task_id"])
            if not t:
                return f"错误：任务 #{args['task_id']} 不存在"
            t.status = args["to_status"]
            db.commit()
            return f"已将任务 #{t.id}「{t.title}」移动到 {args['to_status']}"

        if name == "delete_task":
            t = _find_task(db, args["task_id"])
            if not t:
                return f"错误：任务 #{args['task_id']} 不存在"
            title = t.title
            db.delete(t)
            db.commit()
            return f"已删除任务 #{args['task_id']}「{title}」"

        if name == "add_subtask":
            t = _find_task(db, args["task_id"])
            if not t:
                return f"错误：任务 #{args['task_id']} 不存在"
            st = Subtask(task_id=t.id, title=args["title"])
            db.add(st)
            db.commit()
            return f"已为任务 #{t.id}「{t.title}」添加子任务「{args['title']}」"

        if name == "complete_subtask":
            st = db.get(Subtask, args["subtask_id"])
            if not st:
                return f"错误：子任务 #{args['subtask_id']} 不存在"
            st.done = True
            db.commit()
            t = db.get(Task, st.task_id)
            if t:
                total = len(t.subtasks)
                done = sum(1 for s in t.subtasks if s.done)
                t.progress = round(done / total * 100) if total else t.progress
                db.commit()
                return f"已完成子任务「{st.title}」，任务「{t.title}」进度更新为 {t.progress}%"
            return f"已完成子任务「{st.title}」"

        if name == "get_task_detail":
            t = _find_task(db, args["task_id"])
            if not t:
                return f"错误：任务 #{args['task_id']} 不存在"
            proj = db.get(Project, t.project_id)
            subs = [
                f"- [{('x' if s.done else ' ')}] #{s.id} {s.title}"
                for s in t.subtasks
            ]
            return (
                f"任务 #{t.id}「{t.title}」\n"
                f"项目：{proj.name if proj else t.project_id}\n"
                f"状态：{t.status} | 优先级：{t.priority} | 进度：{t.progress}%\n"
                f"日期：{t.start_date or '—'} ~ {t.due_date or '—'}\n"
                f"里程碑：{'是' if t.is_milestone else '否'}\n"
                f"描述：{t.description or '(空)'}\n"
                + (f"子任务：\n" + "\n".join(subs) if subs else "子任务：无")
            )

        if name == "list_subtasks":
            t = _find_task(db, args["task_id"])
            if not t:
                return f"错误：任务 #{args['task_id']} 不存在"
            if not t.subtasks:
                return f"任务「{t.title}」没有子任务"
            return "\n".join(
                f"#{s.id} [{'✅' if s.done else '⬜'}] {s.title}"
                for s in t.subtasks
            )

        if name == "update_subtask":
            st = db.get(Subtask, args["subtask_id"])
            if not st:
                return f"错误：子任务 #{args['subtask_id']} 不存在"
            if "done" in args:
                st.done = bool(args["done"])
            if "title" in args and args["title"]:
                st.title = args["title"]
            db.commit()
            t = db.get(Task, st.task_id)
            if t and t.subtasks:
                total = len(t.subtasks)
                done = sum(1 for s in t.subtasks if s.done)
                t.progress = round(done / total * 100)
                if done == total:
                    t.status = "done"
                elif done == 0:
                    t.status = "backlog"
                else:
                    t.status = "in_progress"
                db.commit()
                return (
                    f"已更新子任务 #{st.id}「{st.title}」"
                    f"（{'完成' if st.done else '未完成'}），"
                    f"任务「{t.title}」进度 {t.progress}%，状态自动归类为 {t.status}"
                )
            return f"已更新子任务 #{st.id}「{st.title}」（{'完成' if st.done else '未完成'}）"

        if name == "delete_subtask":
            st = db.get(Subtask, args["subtask_id"])
            if not st:
                return f"错误：子任务 #{args['subtask_id']} 不存在"
            title = st.title
            task_id = st.task_id
            db.delete(st)
            db.commit()
            t = db.get(Task, task_id)
            if t and t.subtasks:
                total = len(t.subtasks)
                done = sum(1 for s in t.subtasks if s.done)
                t.progress = round(done / total * 100)
                if done == total:
                    t.status = "done"
                elif done == 0:
                    t.status = "backlog"
                else:
                    t.status = "in_progress"
                db.commit()
            return f"已删除子任务「{title}」"

        if name == "get_note":
            t = _find_task(db, args["task_id"])
            if not t:
                return f"错误：任务 #{args['task_id']} 不存在"
            note = db.query(TaskNote).filter(TaskNote.task_id == t.id).first()
            if not note or not note.content.strip():
                return f"任务「{t.title}」还没有笔记（空）"
            return f"任务「{t.title}」的笔记内容：\n---\n{note.content}\n---"

        if name == "save_note":
            t = _find_task(db, args["task_id"])
            if not t:
                return f"错误：任务 #{args['task_id']} 不存在"
            content = args.get("content", "")
            note = db.query(TaskNote).filter(TaskNote.task_id == t.id).first()
            if note:
                note.content = content
                note.updated_at = datetime.now()
            else:
                note = TaskNote(task_id=t.id, content=content)
                db.add(note)
            db.commit()
            return f"已保存任务「{t.title}」的笔记（{len(content)} 字符）"

        if name == "get_project_progress":
            proj = _find_project(db, args["project_name"])
            if not proj:
                return f"未找到项目「{args['project_name']}」"
            total = len(proj.tasks)
            done = sum(1 for t in proj.tasks if t.status == "done")
            overdue = sum(
                1
                for t in proj.tasks
                if t.status != "done" and t.due_date and t.due_date < date.today()
            )
            progress = round(done / total * 100) if total else 0
            return (
                f"项目「{proj.name}」：共 {total} 个任务，完成 {done} 个，"
                f"进度 {progress}%，逾期 {overdue} 个"
            )

        return f"未知工具：{name}"
    finally:
        db.close()
