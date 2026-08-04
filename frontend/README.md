# Waypoint 前端

Vue 3（`<script setup>`）+ Vite + Element Plus + frappe-gantt 构建。

- 完整运行说明见项目根目录 [README.md](../README.md)
- 开发：`npm run dev`（:5173，/api 代理到 8600）
- 构建：`npm run build`（产物输出到 `dist/`，由后端静态托管）
- `npm install` 后自动执行 `scripts/patch-frappe-gantt.cjs`（给 frappe-gantt 打拖动方向/拉伸柄补丁，改该脚本后需重新 postinstall + 清 `.vite` 缓存再构建）
