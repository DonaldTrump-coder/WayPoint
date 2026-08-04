<div align="center">

[![English](https://img.shields.io/badge/English-ffffff?style=for-the-badge&logo=googletranslate&logoColor=16324F)](https://github.com/DonaldTrump-coder/WayPoint/blob/main/README.md)
![中文](https://img.shields.io/badge/%E4%B8%AD%E6%96%87-16324F?style=for-the-badge&logo=googletranslate&logoColor=white)

<img src="icon.png" alt="WayPoint" width="96" style="border-radius: 20px" />

# 🧭 WayPoint

**本地个人项目管理 · 看板流转 · 甘特时间线 · AI Copilot 自然语言操控**

</div>

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3-42b883?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)

[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Element Plus](https://img.shields.io/badge/Element%20Plus-409EFF?style=for-the-badge&logo=element&logoColor=white)](https://element-plus.org/)
[![Frappe Gantt](https://img.shields.io/badge/FrappeGantt-1.2.2-67c23a?style=for-the-badge)](https://frappe.io/gantt)
[![Local First](https://img.shields.io/badge/Local%20First-%E2%9C%93%20%E6%97%A0%E4%BA%91%E4%BE%9D%E8%B5%96-16324F?style=for-the-badge)](https://github.com/DonaldTrump-coder/WayPoint)

[![Author](https://img.shields.io/badge/Author-Haojun%20Tang-16324F?style=for-the-badge&logo=github&logoColor=white)](https://donaldtrump-coder.github.io/)
[![Stars](https://img.shields.io/github/stars/DonaldTrump-coder/WayPoint?style=for-the-badge&logo=github&logoColor=white&color=ffd700)](https://github.com/DonaldTrump-coder/WayPoint)
[![License](https://img.shields.io/badge/License-MIT-4caf50?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](https://opensource.org/license/mit)

**数据 100% 保存在本地 SQLite** · 无账号 · 无云依赖 · 无隐私顾虑

</div>

---

**WayPoint** 是运行在你本机的一套项目管理系统：**看板**管任务流转、**甘特图**管时间线、**AI Copilot** 用自然语言操控一切。项目是一次航程，任务是航线上的航路点——进度条就是航行到达的位置。

- 💻 **纯本地运行**：SQLite 单文件数据库，拷贝即迁移，卸载/升级不丢数据
- 🤖 **AI 加持**：接入你自己的 API Key（DeepSeek / OpenAI / GLM / Ollama 均可），自然语言建任务、改状态、写笔记
- 🔒 **隐私安全**：数据不出本机，AI 配置（含 Key）仅存本地数据库

## ✨ 功能特性

| 模块 | 能力 |
|---|---|
| 📊 仪表盘 | 项目卡片墙：环形进度、任务统计、逾期徽标、一键新建；全部项目 / 航行中（未归档）统计 |
| 📋 看板 | 跨列拖拽、WIP 计数、子任务 checklist、任务卡片右键「打开笔记」 |
| 📈 甘特图 | 任务条拖拽改期（含拉伸柄）、进度拖动、里程碑菱形标记、日/周/月视图、新建任务/里程碑 |
| 📝 笔记系统 | 每个任务关联一篇 Markdown 笔记：左侧文件夹树、中间编辑器（工具栏：标题/加粗/列表/代码块等）、右侧 GitHub 风格渲染；看板/甘特右键直达 |
| 🗓 日历 | 任务截止/项目结束自动聚合 + 手动事件；当天摘要 |
| 🤖 AI Copilot | 自然语言建任务/改状态/查进度/写笔记（16 个工具），仅展示最终回答；思考开关、聊天记录持久化、按提供商分组的模型切换 |
| ⚙️ 多提供商 | OpenAI / DeepSeek / Moonshot / Ollama 预设 + 自定义；测试连接、一键拉取模型列表（永久缓存）、聊天面板内直接切换模型 |
| 💾 数据安全 | SQLite 单文件 + 启动自动备份（保留 30 份）+ JSON 导出/导入 + 删除任务/项目级联删除笔记 |

**进度机制**：任务挂子任务（checklist），勾选完成自动累计进度并自动归类状态（全完成=已完成 / 全未完成=待办 / 部分=进行中）；无子任务可手动调。甘特条与看板卡片同步显示。

## 🚀 从源代码运行

### 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| **Python** | 3.10+ | 后端 FastAPI + SQLite |
| **Node.js** | 18+ | 前端构建（Vite）；构建完成后运行阶段不再需要 |
| **npm** | 随 Node.js | 前端依赖安装 |

### Windows

**一键启动**（自动建 venv、装依赖、构建前端、启动服务）：

```bat
双击 start.bat
```

**手动启动**（分步，便于理解）：

```bat
:: 1. 创建虚拟环境并安装后端依赖
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

:: 2. 安装前端依赖并构建（产物输出到 frontend/dist）
cd frontend
npm install          :: 自动执行 postinstall：给 frappe-gantt 打拖动补丁
npm run build
cd ..

:: 3. 启动服务（默认 http://localhost:8600）
.venv\Scripts\python.exe app.py
```

### Linux / macOS

```bash
# 一键启动
chmod +x start.sh && ./start.sh

# 或手动（等价于上方 Windows 分步，注意 venv 路径为 .venv/bin）
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
.venv/bin/python app.py
```

### 开发模式（前端热更新）

```bash
# 终端 1：后端 API（:8600，托管已构建的 dist）
.venv/Scripts/python.exe app.py

# 终端 2：Vite 开发服务器（:5173，/api 代理到 8600，改前端即时生效）
cd frontend && npm run dev
```

启动后浏览器打开 **http://localhost:8600**（生产/一键模式）或 **http://localhost:5173**（开发模式）。

> ⚠️ **注意**：开发模式下若改了 `node_modules/frappe-gantt` 的补丁，需重新 `npm run postinstall` 并 `rm -rf node_modules/.vite` 清缓存后重启 dev server。

### 自定义端口

```bash
WAYPOINT_PORT=8700 python app.py    # 后端与前端托管改到 :8700
```

## 📦 打包发布

把 WayPoint 打成单文件 exe 和 Windows 安装包（数据与程序分离：程序装到安装目录，数据存**安装目录下 `data\` 子目录**——装到哪数据就在哪，不写 C 盘/APPDATA；升级/卸载不丢数据）。

### 前置条件

- 已按上方「从源代码运行」完成 `pip install -r requirements.txt` 和 `cd frontend && npm install && npm run build`（dist 是打包素材）
- PyInstaller：`.venv/Scripts/pip install pyinstaller`

### 1. 打包单文件 exe

```bash
# 在项目根目录（F:\Projects\WayPoints）
.venv/Scripts/pyinstaller.exe --noconfirm packaging/waypoint.spec
```

产物：`dist\Waypoint.exe`（约 32MB，单文件）

行为：双击启动 → 弹出黑色命令行窗口（提示访问地址 + 数据目录）→ 自动在浏览器打开 http://localhost:8600；**关闭黑框即停止服务**。

### 2. 构建 Windows 安装包

```bash
# ① 首次需准备 Inno Setup 6 编译器（或自行安装官方版）
#    下载: https://jrsoftware.org/download.php/is.exe（官方下载器）
#    静默安装到项目内: innosetup-6.x.exe /VERYSILENT /NORESTART /DIR="F:\Projects\WayPoints\packaging\tools\inno"
# ② 中文语言文件（官方包不带，需补）：
#    下载 https://raw.githubusercontent.com/jrsoftware/issrc/main/Files/Languages/ChineseSimplified.isl
#    放到 packaging\tools\inno\Languages\ 目录
# ③ 编译：
"F:/Projects/WayPoints/packaging/tools/inno/ISCC.exe" packaging/installer.iss
```

产物：`dist\Waypoint-Setup-1.0.0.exe`（约 31MB）

安装包特性：
- **中文向导**（可选安装路径，默认 `C:\Program Files\Waypoint`）
- 开始菜单含程序 + 「使用说明」（README-Waypoint.txt）
- **数据保护**：数据存 `%APPDATA%\Waypoint`，与程序分离；卸载时弹窗询问是否删除数据，**默认保留**
- 卸载前自动结束运行中的 WayPoint 进程

### 数据目录解析规则（打包/安装后）

| 来源 | 位置 |
|---|---|
| `WAYPOINT_DATA_DIR` 环境变量 | 指定目录（最高优先） |
| 打包版（exe） | **exe 所在目录的 `data\` 子目录**（装到哪数据就在哪，不写 C 盘/APPDATA） |
| 源码运行（开发） | 项目根目录（首次启动自动把旧库迁移到目标位置） |

> 打包改造的关键：`database.py` 的 `_resolve_data_dir()` 解析数据目录；`app.py` 的 `DIST_DIR` 在 PyInstaller 下从 `sys._MEIPASS` 读取打包的前端资源。exe/安装包构建的完整配置在 `packaging/`（waypoint.spec / installer.iss / icon.ico）。

## 🎯 使用指南

### 1. 配置 AI Copilot（可选但推荐）

1. 右上角 ⚙️ → **AI 提供商**
2. 选择预设（DeepSeek / OpenAI / Ollama…）自动填入 Base URL 和推荐模型，或填自定义 Base URL + API Key
3. **模型**：下拉选择预设/已缓存模型，或直接输入；保存后点卡片上 **「拉取模型」** 自动获取该服务全部模型（永久保存，重启不丢）
4. 点击 **「测试连接」** 验证连通性
5. 第一个添加的自动成为默认

**聊天时切换模型**：打开 AI 面板（机器人图标或 Ctrl+K），顶部 **「🖥 模型」** 下拉按提供商分组显示所有已缓存模型，选择即切换（自动设为默认，下一次对话立即生效）。

### 2. 创建项目与任务

- 首页点「+」新建项目（名称、描述、主题色）
- 进入项目 → 看板 → 各列底部「添加任务」
- 点任务卡片编辑：描述、优先级、起止日期、里程碑开关、子任务 checklist

### 3. 拖拽与进度

- **看板**：拖卡片跨列移动（状态自动变更）
- **甘特图**：拖任务条两端拉伸柄改日期；拖条内进度块调进度；工具栏可新建任务/里程碑；任务条右键「打开笔记」
- **子任务**：勾选 ✓ 自动累计任务进度并归类状态

### 4. 笔记系统

- 顶部书图标进入 **航路图 → 笔记**
- 左侧项目可折叠（点击项目名收起/展开任务列表），有笔记的任务带绿点
- 中间编辑：工具栏插入标题/粗体/列表/代码块等，Ctrl+S 或停顿自动保存
- 右侧实时预览（GitHub 风格渲染：引用、代码块、表格、任务列表）
- 看板/甘特任务右键 → **打开笔记** 直接跳转到该任务笔记

### 5. AI Copilot 示例

```
"在 GSSA 项目里建一个任务「完成实验章节」，下周五截止，优先级高"
"把所有进行中的任务列出来"
"把任务 #3 移到已完成"
"给任务 #5 写一篇笔记，总结本周进展"
"GSSA 项目进度怎么样？"
```

- 面板只显示最终回答（工具调用在后台执行，不展示原始过程）
- **思考** 开关：开启后模型先分析再调用工具
- **清空** 按钮：彻底清空聊天记录（内存 + 数据库），下次打开从头开始
- 聊天记录自动持久化：关闭面板/刷新页面后再次打开，历史消息与思考开关状态都会恢复

### 6. 归档

- 项目详情页右上角 **「归档」**：项目从「航行中」统计移除，但仍在「全部项目」与卡片墙（带「已归档」标签）
- 归档项目点 **「恢复航行」** 回到活跃

### 7. 数据备份

- 设置 → **导出备份**：下载完整 JSON
- **导入恢复**：清空后重建（导入前会警告）
- 每次启动自动备份数据库到 `backups/`（保留最近 30 份）

## 🗂 项目结构

```
WayPoints/
├── app.py              # FastAPI 入口（API + 前端静态托管 + 启动自动备份）
├── database.py         # SQLite 连接 / 建表 / 轻量列迁移
├── models.py           # ORM: Project / Task / Subtask / TaskNote / KanbanColumn / Label / AIConfig / CalendarEvent / ChatMessage / ChatState
├── schemas.py          # Pydantic 请求/响应模型
├── routers/            # projects / tasks / kanban / settings / agent / calendar / notes
├── agent/              # tools.py(16 个工具) + client.py(function calling 循环 + system prompt)
├── frontend/           # Vue3 + Vite + Element Plus
│   ├── scripts/        # patch-frappe-gantt.cjs（npm postinstall 自动打拖动补丁）
│   └── src/
│       ├── views/      # Dashboard / ProjectDetail / Kanban / Gantt / Notes / Settings / AISettings
│       └── components/ # TaskDialog / AIChatPanel / MdRenderer / TaskContextMenu / CalendarPanel / RouteOverview
├── start.bat           # Windows 一键启动
├── start.sh            # Linux/macOS 一键启动
├── requirements.txt    # Python 依赖
├── packaging/          # 打包发布：waypoint.spec(PyInstaller) / installer.iss(Inno Setup) / README-Waypoint.txt / icon.ico
├── dist/               # 打包产物：Waypoint.exe + Waypoint-Setup-*.exe
└── waypoint.db         # 数据文件（首次运行自动生成；打包版存 exe 旁 data\ 目录）
```

## 🔧 API 速览

| 前缀 | 说明 |
|---|---|
| `/api/projects` | 项目 CRUD + 统计 + 归档状态 |
| `/api/projects/{id}/tasks` | 任务 CRUD + 筛选 |
| `/api/tasks/{id}/move` | 看板移动 |
| `/api/tasks/{id}/subtasks` | 子任务（进度自动重算 + 状态自动归类） |
| `/api/projects/{id}/columns` | 看板列定义 |
| `/api/notes` | 笔记 tree / 读取 / 保存（一任务一笔记） |
| `/api/calendar` | 日历事件（自动聚合 + 手动 CRUD）+ 当天摘要 |
| `/api/ai/providers` | AI 提供商 CRUD + 测试连接 + 拉取模型 + 切换模型（`/select`） |
| `/api/agent/chat` | AI 对话（function calling，16 个工具） |
| `/api/agent/history` | 聊天记录持久化（读/追加/清空） |
| `/api/agent/state` | 面板状态（思考开关等） |
| `/api/export` `/api/import` | 数据备份/恢复 |

交互式文档：启动后访问 `http://localhost:8600/docs`

## ✅ 测试

回归脚本已随 v1.0.0 移除——它们会清空项目与 AI 提供商配置（误跑会丢失数据），对使用者不友好。功能验证改为开发期的 ad-hoc 验证（`/api/health` 健康检查 + 接口直测）。

```bash
# 快速自检
curl http://127.0.0.1:8600/api/health    # → {"status":"ok"}
```

## ⚠️ 常见问题

- **端口被占用**：`WAYPOINT_PORT=8700 python app.py` 自定义端口
- **改前端代码**：开发模式用 `npm run dev`；改完构建 `npm run build`
- **Ollama 本地模型**：Base URL 填 `http://localhost:11434/v1`，API Key 可留空
- **换机器迁移**：拷贝整个目录（含 `waypoint.db`），或导出 JSON 后导入

## 📄 许可证

[MIT](LICENSE)
