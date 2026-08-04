<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage } from 'element-plus'
import Gantt from 'frappe-gantt'
import '../../node_modules/frappe-gantt/dist/frappe-gantt.css'
import { listTasks, updateTask, getTask, notifyDataChanged } from '../api'
import TaskDialog from '../components/TaskDialog.vue'
import TaskContextMenu from '../components/TaskContextMenu.vue'

try {
  const patchedSrc = Gantt.toString ? String(Gantt) : ''
  if (patchedSrc.includes('offsetX') && !patchedSrc.includes('(l.clientX)-e')) {
    console.warn('[GanttView] frappe-gantt 未应用 clientX 拖动补丁（node_modules 可能被重置），'
      + '请运行: cd frontend && npm run postinstall')
  }
} catch (e) {  }

const props = defineProps({
  project: Object,
})
const emit = defineEmits(['changed'])

const container = ref(null)
const loading = ref(false)
let gantt = null
const viewMode = ref('Day')

const ctxVisible = ref(false)
const ctxX = ref(0)
const ctxY = ref(0)
const ctxTask = ref(null)

const tasksRef = ref([])

const dialogVisible = ref(false)
const editingTask = ref(null)

const pendingDateChanges = new Map()
let commitTimer = null

const load = async () => {
  loading.value = true
  try {
    const tasks = await listTasks(props.project.id)
    renderGantt(tasks)
  } catch (e) {
    ElMessage.error('加载甘特图失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

const renderGantt = (tasks) => {
  if (!container.value) return
  container.value.innerHTML = ''
  tasksRef.value = tasks

  const rows = tasks
    .filter(t => t.start_date || t.due_date)
    .map(t => ({
      id: String(t.id),
      name: t.title,
      start: t.start_date || t.due_date,
      end: t.due_date || t.start_date,
      progress: t.progress,
      custom_class: t.is_milestone ? 'wp-milestone' : 'wp-task',
    }))

  if (!rows.length) {
    container.value.innerHTML = '<div class="gantt-empty">没有带日期的任务，请先为任务设置起止日期。</div>'
    return
  }

  rows.sort((a, b) => (a.start < b.start ? -1 : 1))

  gantt = new Gantt(container.value, rows, {
    view_mode: viewMode.value,
    language: 'zh',
    on_click: (task) => {
      const real = tasksRef.value.find(t => String(t.id) === task.id)
      if (real) openEdit(real)
    },
    on_date_change: (task, start, end) => {
      const fmt = (d) => d.toISOString().slice(0, 10)
      const local = tasksRef.value.find(t => String(t.id) === task.id)
      if (local) {
        local.start_date = fmt(start)
        local.due_date = fmt(end)
      }
      pendingDateChanges.set(task.id, { start, end })
      if (commitTimer) clearTimeout(commitTimer)
      commitTimer = setTimeout(commitDates, 500)
      dragging = true
      draggedTaskId = String(task.id)
      startScrollLoop()
    },
    on_progress_change: (task, progress) => {
      const local = tasksRef.value.find(t => String(t.id) === task.id)
      if (local) local.progress = Math.round(progress)
      updateTask(Number(task.id), { progress: Math.round(progress) })
        .then(() => emit('changed'))
        .catch(e => ElMessage.error(e.response?.data?.detail || '进度更新失败'))
    },
  })

  const style = document.createElement('style')
  style.textContent = `
    .gantt .bar-wrapper .bar { fill: ${props.project.color}; }
    .gantt .bar-wrapper:hover .bar { fill: ${props.project.color}; opacity: 0.85; }
    .gantt .bar-wrapper.inactive .bar { fill: #c0c4cc; }
    .wp-milestone .bar { fill: #f56c6c !important; }
    .gantt .bar-progress { fill: rgba(0,0,0,0.25); }
    .gantt-container { overflow-x: auto; }
  `
  document.head.appendChild(style)
  gantt._styleEl = style
  bindMouseup()
  bindDragTracking()
  bindBarContextMenu()
}


let dragging = false
let draggedTaskId = null
let scrollRafId = null

// finaldx = (lastClientX - startClientX) + (scrollLeft - startScrollLeft)）
let dragStart = null    // { clientX, scrollLeft, ox, owidth, mode }
let lastClientX = null
let lastClientXPrev = null
let lastMouseDir = 0
let dragTrackBound = false

const bindDragTracking = () => {
  if (dragTrackBound || !gantt) return
  document.addEventListener('mousedown', (e) => {
    const wrap = e.target.closest('.bar-wrapper')
    if (!wrap || !gantt) return
    const barEl = wrap.querySelector('.bar')
    if (!barEl) return
    const cls = e.target.getAttribute('class') || ''
    const mode = (cls.includes('handle') && cls.includes('right')) ? 'resize-right'
      : (cls.includes('handle') && cls.includes('left')) ? 'resize-left'
      : 'move'
    dragStart = {
      clientX: e.clientX,
      scrollLeft: gantt.$container.scrollLeft,
      ox: parseFloat(barEl.getAttribute('x')) || 0,
      owidth: parseFloat(barEl.getAttribute('width')) || 0,
      mode,
    }
    lastClientX = e.clientX
    lastClientXPrev = e.clientX
    lastMouseDir = 0
  })
  document.addEventListener('mousemove', (e) => {
    lastClientXPrev = lastClientX
    lastClientX = e.clientX
    if (lastClientXPrev !== null) {
      const d = lastClientX - lastClientXPrev
      if (d > 2) lastMouseDir = 1
      else if (d < -2) lastMouseDir = -1
    }
  }, true)
  dragTrackBound = true
}

let ctxBound = false
const bindBarContextMenu = () => {
  if (ctxBound || !gantt) return
  gantt.$container.addEventListener('contextmenu', (e) => {
    const wrap = e.target.closest('.bar-wrapper')
    if (!wrap) return
    e.preventDefault()
    const id = wrap.getAttribute('data-id')
    const real = tasksRef.value.find(t => String(t.id) === id)
    if (!real) return
    ctxTask.value = real
    ctxX.value = e.clientX
    ctxY.value = e.clientY
    ctxVisible.value = true
  })
  ctxBound = true
}

const startScrollLoop = () => {
  if (scrollRafId) return
  const loop = () => {
    if (!dragging || !gantt) {
      scrollRafId = null
      return
    }
    scrollStep()
    scrollRafId = requestAnimationFrame(loop)
  }
  scrollRafId = requestAnimationFrame(loop)
}

const stopScrollLoop = () => {
  dragging = false
  if (scrollRafId) {
    cancelAnimationFrame(scrollRafId)
    scrollRafId = null
  }
  dragStart = null
  lastClientX = null
}
let mouseupBound = false
const bindMouseup = () => {
  if (mouseupBound) return
  document.addEventListener('mouseup', stopScrollLoop)
  mouseupBound = true
}

const SCROLL_STEP_PX = 14

const scrollStep = () => {
  if (!gantt || !draggedTaskId) return
  const c = gantt.$container
  if (!c) return
  const edgePx = 120
  const bar = gantt.bars.find(b => String(b.task.id) === draggedTaskId)
  if (!bar || !bar.$bar) return
  const barLeft = bar.$bar.getX()
  const barRight = barLeft + bar.$bar.getWidth()
  const viewLeft = c.scrollLeft
  const viewRight = c.scrollLeft + c.clientWidth

  if (barRight > viewRight - edgePx && lastMouseDir !== -1) {
    const maxScroll = c.scrollWidth - c.clientWidth
    if (c.scrollLeft >= maxScroll - SCROLL_STEP_PX) {
      extendEndIfNeeded()
    }
    c.scrollLeft = Math.min(c.scrollWidth - c.clientWidth, c.scrollLeft + SCROLL_STEP_PX)
  }
  else if (barLeft < viewLeft + edgePx && lastMouseDir !== 1) {
    c.scrollLeft = Math.max(0, c.scrollLeft - SCROLL_STEP_PX)
  }

  syncDraggedBar()
}

const syncDraggedBar = () => {
  if (!dragStart || lastClientX === null) return
  const bar = gantt.bars.find(b => String(b.task.id) === draggedTaskId)
  if (!bar || !bar.$bar) return
  const c = gantt.$container
  const rawFinaldx = (lastClientX - dragStart.clientX) + (c.scrollLeft - dragStart.scrollLeft)
  if (dragStart.mode === 'resize-right') {
    bar.update_bar_position({ width: Math.max(0, dragStart.owidth + rawFinaldx) })
  } else if (dragStart.mode === 'resize-left') {
    bar.update_bar_position({ x: dragStart.ox + rawFinaldx, width: Math.max(0, dragStart.owidth - rawFinaldx) })
  } else {
    bar.update_bar_position({ x: dragStart.ox + rawFinaldx })
  }
}

let lastExtendAt = 0
const EXTEND_COOLDOWN_MS = 400
const extendEndIfNeeded = () => {
  const now = Date.now()
  if (now - lastExtendAt < EXTEND_COOLDOWN_MS) return
  lastExtendAt = now
  const units = gantt.config.extend_by_units || 10
  const unit = gantt.config.unit  // 'day' | 'week' | 'month' | 'year'
  const n = units * 3
  const newEnd = new Date(gantt.gantt_end)
  if (unit === 'month') newEnd.setMonth(newEnd.getMonth() + n)
  else if (unit === 'year') newEnd.setFullYear(newEnd.getFullYear() + n)
  else if (unit === 'week') newEnd.setDate(newEnd.getDate() + 7 * n)
  else newEnd.setDate(newEnd.getDate() + n)
  gantt.gantt_end = newEnd
  gantt.setup_date_values()
  const colW = gantt.config.column_width
  const newW = gantt.dates.length * colW
  gantt.$svg.querySelector('.grid-background')?.setAttribute('width', newW)
  gantt.$svg.querySelectorAll('.grid-row').forEach(r => r.setAttribute('width', newW))
  if (gantt.$svg.getAttribute('width') < newW) gantt.$svg.setAttribute('width', newW)
  if (gantt.$header) gantt.$header.style.width = newW + 'px'
  gantt.get_dates_to_draw().forEach((d) => {
    const key = d.formatted_date || String(d.x)
    if (gantt.$lower_header.querySelector(`.date_${key.replace(/ /g, '_')}`)) return
    if (d.lower_text) {
      const el = gantt.create_el({ left: d.x, top: d.lower_y, classes: `lower-text date_${key.replace(/ /g, '_')}`, append_to: gantt.$lower_header })
      el.innerText = d.lower_text
    }
    if (d.upper_text) {
      const el = gantt.create_el({ left: d.x, top: d.upper_y, classes: 'upper-text', append_to: gantt.$upper_header })
      el.innerText = d.upper_text
    }
  })
  gantt.upperTexts = Array.from(gantt.$container.querySelectorAll('.upper-text'))
  gantt.lowerTexts = Array.from(gantt.$container.querySelectorAll('.lower-text'))
}

const commitDates = async () => {
  dragging = false
  if (scrollRafId) {
    cancelAnimationFrame(scrollRafId)
    scrollRafId = null
  }
  const changes = [...pendingDateChanges.entries()]
  pendingDateChanges.clear()
  for (const [id, { start, end }] of changes) {
    const fmt = (d) => d.toISOString().slice(0, 10)
    try {
      await updateTask(Number(id), {
        start_date: fmt(start),
        due_date: fmt(end),
      })
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '日期更新失败')
    }
  }
  if (changes.length) {
    ElMessage.success('日期已更新')
    emit('changed')
    notifyDataChanged()
  }
}

const openEdit = (task) => {
  editingTask.value = task
  dialogVisible.value = true
}

const openCreate = (isMilestone = false) => {
  editingTask.value = null
  newIsMilestone.value = isMilestone
  dialogVisible.value = true
}
const newIsMilestone = ref(false)

const changeView = (mode) => {
  viewMode.value = mode
  if (gantt) gantt.change_view_mode(mode)
}

onMounted(load)
onBeforeUnmount(() => {
  if (commitTimer) clearTimeout(commitTimer)
  dragging = false
  if (scrollRafId) {
    cancelAnimationFrame(scrollRafId)
    scrollRafId = null
  }
  if (mouseupBound) {
    document.removeEventListener('mouseup', stopScrollLoop)
    mouseupBound = false
  }
  if (gantt?._styleEl) gantt._styleEl.remove()
})
</script>

<template>
  <div v-loading="loading">
    <div class="gantt-toolbar">
      <el-radio-group :model-value="viewMode" size="small" @change="changeView">
        <el-radio-button value="Day">日</el-radio-button>
        <el-radio-button value="Week">周</el-radio-button>
        <el-radio-button value="Month">月</el-radio-button>
      </el-radio-group>
      <div style="flex: 1"></div>
      <el-button size="small" type="primary" @click="openCreate(false)">
        <i class="fas fa-plus" style="margin-right: 4px"></i>新建任务
      </el-button>
      <el-button size="small" type="danger" @click="openCreate(true)">
        <i class="fas fa-flag" style="margin-right: 4px"></i>新建里程碑
      </el-button>
      <el-button size="small" @click="load"><i class="fas fa-sync-alt" style="margin-right: 4px"></i>刷新</el-button>
    </div>

    <div ref="container" class="gantt-wrap" style="background: #fff; border-radius: 8px; padding: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06)"></div>

    <div class="gantt-legend">
      <span><span class="legend-dot" style="background: #409EFF"></span> 普通任务</span>
      <span><span class="legend-dot" style="background: #f56c6c"></span> 里程碑</span>
      <span style="color: #909399">· 拖拽任务条调整日期 · 拖动进度块调整进度 · 点击任务条查看详情</span>
    </div>

    <TaskDialog
      v-model:visible="dialogVisible"
      :project="project"
      :task="editingTask"
      :default-milestone="newIsMilestone"
      @saved="load"
      @deleted="load"
    />

    <TaskContextMenu
      v-model:visible="ctxVisible"
      :x="ctxX"
      :y="ctxY"
      :task="ctxTask"
      :project="project"
      @edit-task="openEdit"
    />
  </div>
</template>

<style scoped>
.gantt-toolbar { display: flex; align-items: center; margin-bottom: 12px; gap: 12px; }
.gantt-container :deep(.gantt) { font-size: 13px; }
.gantt-legend {
  display: flex; align-items: center; gap: 16px;
  margin-top: 10px; font-size: 12px; color: #606266;
}
.legend-dot { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
</style>
