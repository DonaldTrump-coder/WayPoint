# 🧭 Waypoint — 使用说明

> 本地个人项目跟进管理系统。项目是航程，任务是航路点。

## 快速开始

1. **安装**：运行 `Waypoint-Setup-1.0.0.exe`，**选择安装路径**（如 `D:\Waypoint`，默认 `C:\Program Files\Waypoint`，可改为任意盘符）
2. **启动**：安装完成后勾选「运行 Waypoint」，或从桌面/开始菜单打开
3. **使用**：程序自动打开黑色命令行窗口（显示访问地址），并自动在浏览器打开 **http://localhost:8600**

> ⚠️ 黑色窗口不要关闭！它是服务窗口——关闭即停止 Waypoint。最小化即可。

## 📁 数据存储位置（重要）

| 项目 | 位置 |
|---|---|
| 数据库（项目/任务/笔记/AI 配置/聊天记录） | **安装目录下 `data\waypoint.db`** |
| 自动备份（最近 30 份，每次启动时生成） | **安装目录下 `data\backups\`** |
| 程序文件 | 安装目录 |

**数据跟着程序走**：装到哪个目录，数据就存在那个目录的 `data\` 子目录——**不会写入 C 盘系统区或 %APPDATA%**。

- 换位置：把整个安装目录（含 `data\`）拷到新位置即可，双击新位置的 Waypoint.exe 直接使用
- 卸载：会弹窗询问「是否删除数据文件」——**默认保留**，勾选才删除 `data\` 目录
- 升级：覆盖安装（选同一目录），数据自动保留

> 数据目录也可用环境变量 `WAYPOINT_DATA_DIR` 指定（最高优先）。

## 功能速览

- **📊 航路总览**：所有项目进度一览（项目=航程，进度条=航行位置）
- **📌 看板**：任务流转（待办 → 进行中 → 已完成），拖拽卡片改状态
- **📈 甘特图**：任务时间线，拖拽调整起止日期，日/周/月视图
- **🗒 笔记**：每个任务可写 Markdown 笔记（GitHub 风格渲染）
- **📅 日历**：任务截止日期与重要日子
- **🤖 AI Copilot**：设置页配置 API Key 后，用自然语言管理项目（如「帮我建一个任务，下周五截止」）
- **🚩 归档**：完成的项目可归档，保留在「全部项目」中

## 🤖 AI 配置（可选）

设置 → AI 提供商 → 添加：
- **名称**：任意（如 DeepSeek / GLM）
- **Base URL**：服务商 API 地址
- **API Key**：你的密钥（只存本地数据库，不联网上传）
- **模型**：保存后可点「拉取模型」获取该服务商全部模型，聊天面板可直接切换

## 端口冲突

默认端口 8600 被占用时，可设置环境变量 `WAYPOINT_PORT` 指定其他端口（如 8700），再启动 Waypoint.exe。

## 常见问题

**Q: 双击 Waypoint.exe 没反应？**
A: 检查是否已有一个实例在运行（同一端口只能启动一个）。任务管理器结束 Waypoint.exe 后重试。

**Q: 换电脑/备份数据？**
A: 拷贝整个安装目录（含 `data\`）到新电脑相同位置即可。

**Q: 卸载后重装，数据还在吗？**
A: 在。数据存安装目录的 `data\`，只要卸载时没勾选「删除数据文件」就保留。

**Q: 第一次安装，之前有旧数据怎么办？**
A: 把旧的 `waypoint.db` 放到 `Waypoint.exe` 旁边，首次启动会自动迁移到 `data\`。

---

## 🔧 打包发布（开发者）

### 打包单文件 exe

```bash
cd F:\Projects\WayPoints
.venv/Scripts/pyinstaller.exe --noconfirm packaging/waypoint.spec
# 产物: dist\Waypoint.exe（约 32MB）
```

### 构建 Windows 安装包

```bash
# ① Inno Setup 6（官网下载或已装）
# ② 中文语言文件放入 packaging\tools\inno\Languages\ChineseSimplified.isl
"F:/Projects/WayPoints/packaging/tools/inno/ISCC.exe" packaging/installer.iss
# 产物: dist\Waypoint-Setup-1.0.0.exe（约 31MB）
```

安装包特性：中文向导（可选安装路径）、数据存安装目录 `data\`（不写 C 盘）、卸载询问是否删数据（默认保留）、卸载前自动结束运行中的进程。

### 数据目录解析规则

| 来源 | 位置 |
|---|---|
| `WAYPOINT_DATA_DIR` 环境变量 | 指定目录（最高优先） |
| 打包版（exe） | exe 所在目录的 `data\` 子目录 |
| 源码运行（开发） | 项目根目录 |

### 从源代码运行

见项目根目录 `README.md`（环境要求、npm 构建、uvicorn 启动）。
