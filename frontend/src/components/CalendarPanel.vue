<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listCalendarEvents, todaySummary, createCalendarEvent, deleteCalendarEvent,
} from '../api'

const currentMonth = ref(new Date())
const events = ref([])
const todayInfo = ref(null)
const selectedDate = ref(null)
const loading = ref(false)

const eventsByDate = computed(() => {
  const map = {}
  for (const ev of events.value) {
    const d = ev.date
    if (!map[d]) map[d] = []
    map[d].push(ev)
  }
  return map
})

const fmtLocal = (d) => {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const monthRange = () => {
  const y = currentMonth.value.getFullYear()
  const m = currentMonth.value.getMonth()
  const start = new Date(y, m, 1)
  const end = new Date(y, m + 1, 0)
  return { start: fmtLocal(start), end: fmtLocal(end) }
}

const load = async () => {
  loading.value = true
  try {
    const { start, end } = monthRange()
    events.value = await listCalendarEvents(start, end)
    todayInfo.value = await todaySummary()
  } catch (e) {
    ElMessage.error('加载日历失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

const currentMonthLabel = computed(() => {
  const y = currentMonth.value.getFullYear()
  const m = currentMonth.value.getMonth() + 1
  return `${y} 年 ${m} 月`
})

const prevMonth = () => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() - 1, 1)
}
const nextMonth = () => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1, 1)
}
const goToday = () => {
  const now = new Date()
  currentMonth.value = new Date(now.getFullYear(), now.getMonth(), 1)
  selectedDate.value = fmtLocal(now)
}

watch(currentMonth, () => {
  load()
})

const onDateClick = (day) => {
  selectedDate.value = day
}

const addVisible = ref(false)
const newEvent = ref({ title: '', color: '#E8A33D' })

const openAdd = () => {
  if (!selectedDate.value) {
    ElMessage.warning('请先点击日历中的某一天')
    return
  }
  newEvent.value = { title: '', color: '#E8A33D' }
  addVisible.value = true
}

const submitAdd = async () => {
  if (!newEvent.value.title.trim()) {
    ElMessage.warning('请输入事项标题')
    return
  }
  try {
    await createCalendarEvent({
      date: selectedDate.value,
      title: newEvent.value.title.trim(),
      color: newEvent.value.color,
    })
    ElMessage.success('已添加到日历')
    addVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  }
}

const confirmDelete = async (ev) => {
  if (!ev.deletable) return
  try {
    await ElMessageBox.confirm(`删除「${ev.title}」？`, '删除事项', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消',
    })
    await deleteCalendarEvent(ev.id.replace('m', ''))
    ElMessage.success('已删除')
    load()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

const isToday = (d) => d === fmtLocal(new Date())
const isSelected = (d) => selectedDate.value === d
const isWeekend = (d) => {
  const dt = new Date(d)
  return dt.getDay() === 0 || dt.getDay() === 6
}

const kindLabel = (k) => ({
  manual: '手动', task_due: '截止', project_end: '结束',
}[k] || k)

const selectedEvents = computed(() => {
  if (!selectedDate.value) return []
  return eventsByDate.value[selectedDate.value] || []
})

const onDataChanged = () => {
  load()
}

onMounted(() => {
  load()
  selectedDate.value = fmtLocal(new Date())
  window.addEventListener('wp:data-changed', onDataChanged)
})

onBeforeUnmount(() => {
  window.removeEventListener('wp:data-changed', onDataChanged)
})
</script>

<template>
  <div class="calendar-panel" v-loading="loading">
    <div class="calendar-head">
      <i class="fas fa-calendar-days" style="color: var(--wp-teal)"></i>
      航程日历
      <span class="sub">— 截止与重要日子</span>
    </div>

    <el-calendar v-model="currentMonth">
      <template #header>
        <div class="cal-header-custom">
          <el-button size="small" text @click="prevMonth">
            <i class="fas fa-chevron-left"></i>
          </el-button>
          <span class="cal-header-title num">{{ currentMonthLabel }}</span>
          <el-button size="small" text @click="nextMonth">
            <i class="fas fa-chevron-right"></i>
          </el-button>
          <el-button size="small" text type="primary" style="margin-left: 4px" @click="goToday">
            今天
          </el-button>
        </div>
      </template>
      <template #date-cell="{ data }">
        <div
          class="cal-day"
          :class="{
            'is-today': isToday(data.day),
            'is-selected': isSelected(data.day),
            'is-weekend': isWeekend(data.day),
          }"
          @click="onDateClick(data.day)"
        >
          <div class="cal-date-num num">{{ data.day.split('-')[2] }}</div>
          <div v-if="eventsByDate[data.day]?.length" class="cal-dots">
            <span
              v-for="ev in eventsByDate[data.day]"
              :key="ev.id"
              class="cal-dot"
              :style="{ background: ev.color }"
              :title="ev.title"
            ></span>
          </div>
        </div>
      </template>
    </el-calendar>

    <div class="today-box" :class="{ important: todayInfo?.has_important }">
      <div class="today-title">
        <i :class="todayInfo?.has_important ? 'fas fa-bell' : 'fas fa-circle-check'"
           :style="{ color: todayInfo?.has_important ? 'var(--wp-coral)' : 'var(--wp-teal)' }"></i>
        {{ todayInfo?.has_important ? `今天有 ${todayInfo.event_count} 件要紧事` : '今天没有安排' }}
      </div>
      <div v-if="todayInfo?.has_important" class="today-list">
        <div v-for="ev in todayInfo.events" :key="ev.id" class="today-item">
          <span class="dot" :style="{ background: ev.color }"></span>
          <span class="txt">{{ ev.title }}</span>
          <el-tag size="small" effect="plain" round>{{ kindLabel(ev.kind) }}</el-tag>
        </div>
      </div>
    </div>

    <div v-if="selectedDate" class="sel-box">
      <div class="sel-head">
        <span><i class="far fa-calendar-check" style="color: var(--wp-navy)"></i> {{ selectedDate }} 的安排</span>
        <el-button size="small" type="primary" text @click="openAdd">
          <i class="fas fa-plus" style="margin-right: 4px"></i>添加
        </el-button>
      </div>
      <div v-if="selectedEvents.length" class="sel-list">
        <div v-for="ev in selectedEvents" :key="ev.id" class="sel-item">
          <span class="dot" :style="{ background: ev.color }"></span>
          <span class="txt">{{ ev.title }}</span>
          <el-tag size="small" effect="plain" round class="kind-tag">{{ kindLabel(ev.kind) }}</el-tag>
          <el-button
            v-if="ev.deletable"
            text type="danger" size="small" class="del-btn"
            @click="confirmDelete(ev)"
          ><i class="far fa-trash-alt"></i></el-button>
        </div>
      </div>
      <div v-else class="sel-empty">这天没有安排，点「添加」记一笔</div>
    </div>

    <el-dialog v-model="addVisible" title="添加重要事项" width="420px">
      <el-form label-width="70px">
        <el-form-item label="日期">
          <el-input :model-value="selectedDate" disabled />
        </el-form-item>
        <el-form-item label="事项">
          <el-input v-model="newEvent.title" placeholder="例如：交实习报告" maxlength="200" />
        </el-form-item>
        <el-form-item label="标记色">
          <el-color-picker v-model="newEvent.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAdd">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.calendar-panel {
  background: var(--wp-card);
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(22, 50, 79, 0.08);
  padding: 18px 22px;
  display: flex;
  flex-direction: column;
  height: 560px;
  box-sizing: border-box;
}
.calendar-head {
  display: flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 700; color: var(--wp-navy);
  margin-bottom: 12px;
  flex-shrink: 0;
}
.calendar-head .sub { font-weight: 400; font-size: 12px; color: var(--wp-mist); }

.cal-header-custom {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 0 8px;
  border-bottom: 1px solid var(--wp-line);
}
.cal-header-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--wp-navy);
  min-width: 96px;
  text-align: center;
}

:deep(.el-calendar) {
  --el-calendar-border: var(--wp-line);
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
:deep(.el-calendar__header) { border-bottom: 1px solid var(--wp-line); padding: 6px 4px 8px !important; flex-shrink: 0; }
:deep(.el-calendar__title) { font-size: 14px; font-weight: 600; color: var(--wp-navy); }
:deep(.el-calendar__body) { flex: 1; min-height: 0; overflow: hidden; padding: 2px 2px 0 !important; }
:deep(.el-calendar-table) { height: 100%; table-layout: fixed; }
:deep(.el-calendar-table td) { border-color: var(--wp-line); text-align: center; vertical-align: top; padding: 1px; }
:deep(.el-calendar-table .el-calendar-day) { height: 100% !important; padding: 2px; box-sizing: border-box; }
:deep(.el-calendar-table thead th) { padding: 4px 0 !important; font-size: 12px; color: var(--wp-mist); }

.cal-day {
  height: 100%;
  display: flex; flex-direction: column; align-items: center;
  border-radius: 6px;
  cursor: pointer;
  padding-top: 3px;
  transition: background 0.12s;
}
.cal-day:hover { background: #F0EDE4; }
.cal-date-num { font-size: 12px; color: var(--wp-ink); }
.cal-day.is-weekend .cal-date-num { color: #B8A58A; }
.cal-day.is-today .cal-date-num {
  background: var(--wp-navy); color: #fff;
  border-radius: 50%; width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
}
.cal-day.is-selected { background: #E8EDF2; outline: 1px solid var(--wp-navy); }

.cal-dots { display: flex; gap: 3px; margin-top: 2px; flex-wrap: wrap; justify-content: center; }
.cal-dot { width: 5px; height: 5px; border-radius: 50%; }

.today-box {
  margin-top: 10px;
  border-radius: 8px;
  padding: 8px 12px;
  background: #F4F1E9;
  border: 1px solid var(--wp-line);
  flex-shrink: 0;
  max-height: 84px;
  overflow-y: auto;
}
.today-box.important { background: #FDF0EC; border-color: #F2C9BD; }
.today-title { font-size: 13px; font-weight: 600; color: var(--wp-ink); display: flex; align-items: center; gap: 6px; }
.today-list { margin-top: 6px; }
.today-item { display: flex; align-items: center; gap: 8px; padding: 2px 0; font-size: 12.5px; }
.today-item .txt { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.sel-box {
  margin-top: 10px;
  flex-shrink: 0;
  height: 128px;              
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.sel-head {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 13px; font-weight: 600; color: var(--wp-navy);
  border-bottom: 1px dashed var(--wp-line); padding-bottom: 4px;
  flex-shrink: 0;             
}
.sel-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;           
  margin-top: 4px;
}
.sel-item {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 4px 0;
  font-size: 12.5px;
  line-height: 1.5;
}
.sel-item .dot { margin-top: 4px; }
.sel-item .txt {
  flex: 1;
  min-width: 0;
  word-break: break-word;     
  color: var(--wp-ink);
}
.sel-item .kind-tag { flex-shrink: 0; margin-top: 1px; }
.sel-item .del-btn { flex-shrink: 0; padding: 0 4px; }
.sel-empty { color: var(--wp-mist); font-size: 12px; padding: 6px 0 2px; }

.dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
</style>
