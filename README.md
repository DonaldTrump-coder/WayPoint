<div align="center">

![English](https://img.shields.io/badge/English-16324F?style=for-the-badge&logo=googletranslate&logoColor=white)
[![中文](https://img.shields.io/badge/%E4%B8%AD%E6%96%87-ffffff?style=for-the-badge&logo=googletranslate&logoColor=16324F)](https://github.com/DonaldTrump-coder/WayPoint/blob/main/README.zh-CN.md)

<img src="icon.png" alt="WayPoint" width="96" style="border-radius: 20px" />

# 🧭 WayPoint

**Local-first personal project management · Kanban flow · Gantt timeline · AI Copilot**

</div>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-42b883?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)

[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Element Plus](https://img.shields.io/badge/Element%20Plus-409EFF?style=for-the-badge&logo=element&logoColor=white)](https://element-plus.org/)
[![Frappe Gantt](https://img.shields.io/badge/FrappeGantt-1.2.2-67c23a?style=for-the-badge)](https://frappe.io/gantt)
[![Local First](https://img.shields.io/badge/Local%20First-%E2%9C%93%20No%20Cloud-16324F?style=for-the-badge)](https://github.com/DonaldTrump-coder/WayPoint)

[![Author](https://img.shields.io/badge/Author-Haojun%20Tang-16324F?style=for-the-badge&logo=github&logoColor=white)](https://donaldtrump-coder.github.io/)
[![Stars](https://img.shields.io/github/stars/DonaldTrump-coder/WayPoint?style=for-the-badge&logo=github&logoColor=white&color=ffd700)](https://github.com/DonaldTrump-coder/WayPoint)
[![License](https://img.shields.io/badge/License-MIT-4caf50?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](https://opensource.org/license/mit)

**100% local data (SQLite)** · No account · No cloud · No telemetry

</div>

---

**WayPoint** is a project management system that runs entirely on your machine: a **Kanban board** for task flow, a **Gantt chart** for timelines, and an **AI Copilot** that understands natural language. A project is a voyage, tasks are waypoints along the route — and your progress bar shows how far you've sailed.

- 💻 **Local-first**: single-file SQLite database. Copy the folder and you've migrated; uninstall/upgrade never loses data
- 🤖 **AI-powered**: bring your own API key (DeepSeek / OpenAI / GLM / Ollama), manage tasks, statuses and notes in plain language
- 🔒 **Private**: data never leaves your machine; AI configs (including keys) stay in the local database

## ✨ Features

| Module | Capabilities |
|---|---|
| 📊 Dashboard | Project cards with ring progress, task stats, overdue badges, one-click create; active / archived counts |
| 📋 Kanban | Cross-column drag & drop, WIP limits, subtask checklists, right-click "Open Notes" on cards |
| 📈 Gantt | Draggable task bars (with resize handles), progress dragging, milestone diamonds, day/week/month views, create tasks/milestones inline |
| 📝 Notes | A Markdown note per task: folder tree on the left, editor with toolbar (headings/bold/lists/code blocks) in the middle, GitHub-style preview on the right; right-click from Kanban/Gantt to jump |
| 🗓 Calendar | Auto-aggregated due dates & project end dates + manual events; today summary |
| 🤖 AI Copilot | Natural language for tasks/statuses/progress/notes (16 tools), final answer only; thinking toggle, persistent chat history, per-provider model switcher |
| ⚙️ Multi-provider | Presets for OpenAI / DeepSeek / Moonshot / Ollama + custom; test connection, one-click model list fetch (permanently cached), switch models inside the chat panel |
| 💾 Data safety | Single SQLite file + automatic startup backups (keeps 30) + JSON export/import + cascading note deletion |

**Progress mechanism**: tasks hold subtask checklists; checking items automatically recomputes progress and classifies status (all done = done / none done = backlog / partial = in_progress); tasks without subtasks can be set manually. Gantt bars and Kanban cards stay in sync.

## 🚀 Run from Source

### Requirements

| Dependency | Version | Notes |
|---|---|---|
| **Python** | 3.10+ | Backend FastAPI + SQLite |
| **Node.js** | 18+ | Frontend build (Vite); not needed at runtime after building |
| **npm** | ships with Node.js | Frontend dependency install |

### Windows

**One-click start** (auto creates venv, installs deps, builds frontend, starts server):

```bat
double-click start.bat
```

**Manual start** (step by step):

```bat
:: 1. Create virtual environment and install backend deps
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

:: 2. Install frontend deps and build (output to frontend/dist)
cd frontend
npm install          :: postinstall auto-patches frappe-gantt drag handling
npm run build
cd ..

:: 3. Start server (default http://localhost:8600)
.venv\Scripts\python.exe app.py
```

### Linux / macOS

```bash
# One-click start
chmod +x start.sh && ./start.sh

# Or manual (equivalent to the Windows steps above; venv lives in .venv/bin)
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
.venv/bin/python app.py
```

### Development mode (frontend hot reload)

```bash
# Terminal 1: backend API (:8600, serves built dist)
.venv/Scripts/python.exe app.py

# Terminal 2: Vite dev server (:5173, /api proxied to 8600, hot reload)
cd frontend && npm run dev
```

Open **http://localhost:8600** (production/one-click mode) or **http://localhost:5173** (dev mode).

> ⚠️ **Note**: in dev mode, if you change the `node_modules/frappe-gantt` patch, re-run `npm run postinstall` and `rm -rf node_modules/.vite` to clear the cache, then restart the dev server.

### Custom port

```bash
WAYPOINT_PORT=8700 python app.py    # serve backend + frontend on :8700
```

## 📦 Packaging & Releases

Package WayPoint into a standalone exe and a Windows installer (data lives separately from the program: install directory for the app, **`data\` subfolder next to the exe** for data — data stays where you install, never touches C: / APPDATA; survives upgrade/uninstall).

### Prerequisites

- Follow "Run from Source" above: `pip install -r requirements.txt` and `cd frontend && npm install && npm run build` (dist is the packaging input)
- PyInstaller: `.venv/Scripts/pip install pyinstaller`

### 1. Build the standalone exe (one-dir)

```bash
.venv/Scripts/pyinstaller.exe --noconfirm packaging/waypoint.spec
```

Output: `dist\Waypoint\` (launcher `Waypoint.exe` + `_internal\` with all dependencies, ~56MB expanded)

Behavior: double-click → console window opens (shows URL + data dir) → browser opens http://localhost:8600 automatically; **closing the console stops the server**.

### 2. Build the Windows installer

```bash
# ① Get Inno Setup 6 (https://jrsoftware.org/download.php/is.exe)
#    silent install into project: innosetup-6.x.exe /VERYSILENT /NORESTART /DIR="F:\Projects\WayPoints\packaging\tools\inno"
# ② Chinese language file (not bundled): download
#    https://raw.githubusercontent.com/jrsoftware/issrc/main/Files/Languages/ChineseSimplified.isl
#    into packaging\tools\inno\Languages\
# ③ Compile:
"F:/Projects/WayPoints/packaging/tools/inno/ISCC.exe" packaging/installer.iss
```

Output: `dist\Waypoint-Setup-1.0.0.exe` (~30MB)

Installer features:
- **Chinese wizard** (choose install path; default `C:\Program Files\Waypoint`)
- Start menu entries: app + "使用说明" (README-Waypoint.txt)
- **Data protection**: data lives in `data\` next to the exe; uninstall asks whether to delete data — **kept by default**
- Kills a running WayPoint before uninstalling

### Data directory resolution

| Source | Location |
|---|---|
| `WAYPOINT_DATA_DIR` env var | custom directory (highest priority) |
| Packaged (exe) | **`data\` subfolder next to the exe** (data follows the program) |
| Source run (dev) | project root (legacy db auto-migrated on first start) |

> Key packaging internals: `database.py::_resolve_data_dir()` resolves the data dir; `app.py` reads the bundled frontend from `sys._MEIPASS` under PyInstaller. Full build config lives in `packaging/` (waypoint.spec / installer.iss / icon.ico).

## 🎯 Usage Guide

### 1. Configure the AI Copilot (optional but recommended)

1. Top-right ⚙️ → **AI Providers**
2. Pick a preset (DeepSeek / OpenAI / Ollama…) to auto-fill Base URL and a recommended model, or enter a custom Base URL + API Key
3. **Model**: select from presets/cached models, or type one directly; after saving, click **「Fetch Models」** on the card to pull the provider's full model list (persisted, survives restarts)
4. Click **「Test Connection」** to verify
5. The first provider added becomes the default

**Switch models while chatting**: open the AI panel (robot icon or Ctrl+K), use the **「🖥 Model」** dropdown at the top — it lists all cached models grouped by provider; picking one switches instantly (auto-sets default, next conversation uses it).

### 2. Create projects & tasks

- On the dashboard, click "+" to create a project (name, description, theme color)
- Enter a project → Kanban → "Add task" at the bottom of each column
- Click a task card to edit: description, priority, start/due dates, milestone toggle, subtask checklist

### 3. Drag & drop and progress

- **Kanban**: drag cards across columns (status updates automatically)
- **Gantt**: drag the resize handles on bar ends to change dates; drag the progress block inside the bar; toolbar can create tasks/milestones; right-click a bar → "Open Notes"
- **Subtasks**: checking ✓ auto-accumulates task progress and classifies status

### 4. Notes

- Click the book icon in the top bar to enter **Notes**
- Left side: collapsible projects (click the project name to expand/collapse tasks); tasks with notes show a green dot
- Middle: editor with toolbar (headings/bold/lists/code blocks); Ctrl+S or pause to auto-save
- Right: live preview (GitHub-style rendering: quotes, code blocks, tables, task lists)
- Right-click a task in Kanban/Gantt → **Open Notes** jumps straight to its note

### 5. AI Copilot examples

```
"Create a task 'Finish experiment chapter' in the GSSA project, due next Friday, high priority"
"List all in-progress tasks"
"Move task #3 to done"
"Write a note for task #5 summarizing this week's progress"
"How is the GSSA project going?"
```

- The panel shows only the final answer (tool calls run in the background, raw process is not shown)
- **Thinking** toggle: model analyzes first, then calls tools
- **Clear** button: wipes the chat history completely (memory + database), starts fresh next open
- Chat history is persisted automatically: reopen the panel after closing/refreshing and both messages and the thinking toggle are restored

### 6. Archive

- **「Archive」** button on the project detail page: removes the project from the "active" count, but it stays in "All projects" and the card wall (with an "archived" tag)
- Click **「Restore」** to bring it back to active

### 7. Data backup

- Settings → **Export backup**: downloads the full JSON
- **Import restore**: wipes and rebuilds (warns before importing)
- Every startup auto-backs up the database to `backups/` (keeps the last 30)

## 🗂 Project Structure

```
WayPoints/
├── app.py              # FastAPI entry (API + static hosting + startup backup)
├── database.py         # SQLite connection / tables / lightweight column migration
├── models.py           # ORM: Project / Task / Subtask / TaskNote / KanbanColumn / Label / AIConfig / CalendarEvent / ChatMessage / ChatState
├── schemas.py          # Pydantic request/response models
├── routers/            # projects / tasks / kanban / settings / agent / calendar / notes
├── agent/              # tools.py (16 tools) + client.py (function-calling loop + system prompt)
├── frontend/           # Vue3 + Vite + Element Plus
│   ├── scripts/        # patch-frappe-gantt.cjs (auto drag patch via npm postinstall)
│   └── src/
│       ├── views/      # Dashboard / ProjectDetail / Kanban / Gantt / Notes / Settings / AISettings
│       └── components/ # TaskDialog / AIChatPanel / MdRenderer / TaskContextMenu / CalendarPanel / RouteOverview
├── start.bat           # Windows one-click start
├── start.sh            # Linux/macOS one-click start
├── requirements.txt    # Python dependencies
├── packaging/          # Packaging: waypoint.spec (PyInstaller) / installer.iss (Inno Setup) / README-Waypoint.txt / icon.ico
├── dist/               # Build outputs: Waypoint/ + Waypoint-Setup-*.exe
└── waypoint.db         # Data file (auto-created on first run; packaged builds use data\ next to the exe)
```

## 🔧 API Overview

| Prefix | Description |
|---|---|
| `/api/projects` | Project CRUD + stats + archive status |
| `/api/projects/{id}/tasks` | Task CRUD + filters |
| `/api/tasks/{id}/move` | Kanban moves |
| `/api/tasks/{id}/subtasks` | Subtasks (auto progress + status classification) |
| `/api/projects/{id}/columns` | Kanban column definitions |
| `/api/notes` | Notes tree / read / save (one note per task) |
| `/api/calendar` | Calendar events (auto-aggregated + manual CRUD) + today summary |
| `/api/ai/providers` | AI provider CRUD + test connection + fetch models + switch model (`/select`) |
| `/api/agent/chat` | AI conversation (function calling, 16 tools) |
| `/api/agent/history` | Persistent chat history (read / append / clear) |
| `/api/agent/state` | Panel state (thinking toggle, etc.) |
| `/api/export` `/api/import` | Data backup / restore |

Interactive docs: visit `http://localhost:8600/docs` after startup.

## ✅ Testing

Regression scripts were removed in v1.0.0 — they wiped projects and AI provider configs (running them by accident loses data), which is unfriendly for users. Functional verification now relies on ad-hoc checks during development (`/api/health` + direct API calls).

```bash
# Quick self-check
curl http://127.0.0.1:8600/api/health    # → {"status":"ok"}
```

## ⚠️ FAQ

- **Port already in use**: `WAYPOINT_PORT=8700 python app.py` for a custom port
- **Changing frontend code**: use `npm run dev` in dev mode; run `npm run build` when done
- **Ollama local models**: Base URL `http://localhost:11434/v1`, API Key can be left empty
- **Migrating to another machine**: copy the whole directory (including `waypoint.db`), or export JSON and import it

## 📄 License

MIT
