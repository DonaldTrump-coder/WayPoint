<script setup>
import { ref, onMounted, computed } from 'vue'
import draggable from 'vuedraggable'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listColumns, createColumn, updateColumn, deleteColumn, reorderColumns,
  moveTask, deleteTask,
} from '../api'
import TaskDialog from '../components/TaskDialog.vue'
import TaskContextMenu from '../components/TaskContextMenu.vue'

const props = defineProps({
  project: Object,
})
const emit = defineEmits(['changed'])

const columns = ref([])
const loading = ref(false)

const dialogVisible = ref(false)
const editingTask = ref(null)
const defaultStatus = ref('backlog')

const ctxVisible = ref(false)
const ctxX = ref(0)
const ctxY = ref(0)
const ctxTask = ref(null)

const onTaskContextMenu = (e, task) => {
  e.preventDefault()
  ctxTask.value = task
  ctxX.value = e.clientX
  ctxY.value = e.clientY
  ctxVisible.value = true
}

const dragOptions = {
  animation: 150,
  ghostClass: 'wp-ghost',
}

const openCreate = (status) => {
  editingTask.value = null
  defaultStatus.value = status
  dialogVisible.value = true
}

const openEdit = (task) => {
  editingTask.value = task
  dialogVisible.value = true
}

const load = async () => {
  loading.value = true
  try {
    columns.value = await listColumns(props.project.id)
  } catch (e) {
    ElMessage.error('加载看板失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

const onDrop = async (evt) => {
  const toEl = evt.to
  if (!toEl) return
  const taskId = evt.item?.dataset?.taskId
  const toStatus = toEl.getAttribute('data-status')
  if (!taskId || !toStatus) return
  try {
    await moveTask(taskId, { to_status: toStatus, order: 0 })
    ElMessage.success(`已移动到「${toEl.getAttribute('data-colname')}」`)
    emit('changed')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '移动失败')
    load()
  }
}

const addColumnVisible = ref(false)
const newColumn = ref({ name: '', status: '' })

const submitAddColumn = async () => {
  if (!newColumn.value.name.trim() || !newColumn.value.status.trim()) {
    ElMessage.warning('请填写列名和状态值')
    return
  }
  try {
    await createColumn(props.project.id, newColumn.value)
    ElMessage.success('列已添加')
    addColumnVisible.value = false
    newColumn.value = { name: '', status: '' }
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  }
}

const editColumn = async (col) => {
  try {
    const { value } = await ElMessageBox.prompt('修改列名', '编辑列', {
      inputValue: col.name,
      confirmButtonText: '保存',
      cancelButtonText: '取消',
    })
    if (value && value !== col.name) {
      await updateColumn(col.id, { name: value })
      ElMessage.success('列名已更新')
      load()
    }
  } catch {  }
}

const removeColumn = async (col) => {
  try {
    await ElMessageBox.confirm(
      `删除列「${col.name}」？该列任务将并入第一列。`,
      '删除列',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await deleteColumn(col.id)
    ElMessage.success('列已删除')
    load()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

const priorityColor = (p) => ({
  low: '#909399', medium: '#409EFF', high: '#e6a23c', urgent: '#f56c6c',
}[p] || '#909399')

const priorityLabel = (p) => ({ low: '低', medium: '中', high: '高', urgent: '紧急' }[p] || p)

const isOverdue = (t) =>
  t.due_date && t.status !== 'done' && new Date(t.due_date) < new Date(new Date().toDateString())

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="kanban-toolbar">
      <div style="flex: 1"></div>
      <el-button size="small" @click="addColumnVisible = true">
        <i class="fas fa-plus" style="margin-right: 4px"></i>添加列
      </el-button>
    </div>

    <div class="kanban-board">
      <draggable
        v-model="columns"
        group="wp-columns"
        item-key="id"
        :animation="150"
        class="kanban-cols"
        :component-data="{ name: 'div' }"
      >
        <template #item="{ element: col }">
          <div class="kanban-col">
            <div class="col-header">
              <span class="col-dot" :style="{ background: props.project.color }"></span>
              <span class="col-name">{{ col.name }}</span>
              <el-tag size="small" type="info" effect="plain" round>{{ col.tasks?.length || 0 }}</el-tag>
              <div style="flex: 1"></div>
              <el-dropdown trigger="click" @command="(cmd) => cmd === 'edit' ? editColumn(col) : removeColumn(col)">
                <el-button text size="small"><i class="fas fa-ellipsis-v"></i></el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit"><i class="fas fa-pen" style="margin-right: 4px"></i>编辑列名</el-dropdown-item>
                    <el-dropdown-item command="delete" divided><i class="fas fa-trash" style="margin-right: 4px; color: #f56c6c"></i>删除列</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <draggable
              :list="col.tasks"
              group="wp-tasks"
              item-key="id"
              v-bind="dragOptions"
              :data-status="col.status"
              :data-colname="col.name"
              class="col-tasks"
              @add="onDrop($event)"
              @update="onDrop($event)"
            >
              <template #item="{ element: task }">
                <div class="task-card wp-card-hover" :data-task-id="task.id" @click="openEdit(task)" @contextmenu="onTaskContextMenu($event, task)">
                  <div class="task-title">{{ task.title }}</div>
                  <div v-if="task.description" class="task-desc">{{ task.description }}</div>
                  <div class="task-meta">
                    <span class="prio" :style="{ color: priorityColor(task.priority) }">
                      {{ priorityLabel(task.priority) }}
                    </span>
                    <span v-if="task.due_date" class="due" :class="{ overdue: isOverdue(task) }">
                      <i class="far fa-calendar-alt"></i> {{ task.due_date }}
                    </span>
                    <span v-if="task.subtasks?.length" class="subcount">
                      <i class="far fa-list-check"></i>
                      {{ task.subtasks.filter(s => s.done).length }}/{{ task.subtasks.length }}
                    </span>
                  </div>
                  <el-progress
                    v-if="task.progress > 0"
                    :percentage="task.progress"
                    :stroke-width="5"
                    :color="props.project.color"
                    style="margin-top: 6px"
                  />
                </div>
              </template>
            </draggable>

            <div class="col-footer" @click="openCreate(col.status)">
              <i class="fas fa-plus"></i> 添加任务
            </div>
          </div>
        </template>
      </draggable>

      <div class="col-hint">
        <i class="fas fa-grip-vertical"></i> 拖动列头可调整列顺序
      </div>
    </div>

    <el-dialog v-model="addColumnVisible" title="添加列" width="400px">
      <el-form label-width="70px">
        <el-form-item label="列名">
          <el-input v-model="newColumn.name" placeholder="例如：评审中" />
        </el-form-item>
        <el-form-item label="状态值">
          <el-input v-model="newColumn.status" placeholder="英文状态值，如 review" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addColumnVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAddColumn">添加</el-button>
      </template>
    </el-dialog>

    <TaskDialog
      v-model:visible="dialogVisible"
      :project="project"
      :task="editingTask"
      :default-status="defaultStatus"
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
.kanban-toolbar { display: flex; margin-bottom: 12px; }
.kanban-board { display: flex; align-items: flex-start; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.kanban-cols { display: flex; gap: 12px; align-items: flex-start; }

.kanban-col {
  width: 280px;
  min-width: 280px;
  background: #f0f2f5;
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 220px);
}

.col-header { display: flex; align-items: center; gap: 6px; padding: 2px 4px 8px; }
.col-dot { width: 8px; height: 8px; border-radius: 50%; }
.col-name { font-weight: 600; font-size: 14px; }

.col-tasks { min-height: 40px; flex: 1; overflow-y: auto; }
.wp-ghost { opacity: 0.4; }

.task-card {
  background: #fff;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
  cursor: pointer;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
.task-title { font-size: 14px; font-weight: 500; word-break: break-all; }
.task-desc { color: #909399; font-size: 12px; margin-top: 4px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.task-meta { display: flex; align-items: center; gap: 8px; margin-top: 6px; font-size: 12px; flex-wrap: wrap; }
.prio { font-weight: 600; }
.due { color: #909399; }
.due.overdue { color: #f56c6c; font-weight: 600; }
.subcount { color: #909399; }

.col-footer {
  margin-top: 8px;
  padding: 6px;
  text-align: center;
  color: #909399;
  font-size: 13px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}
.col-footer:hover { background: #e4e7ed; color: #606266; }

.col-hint {
  align-self: center;
  color: #c0c4cc;
  font-size: 12px;
  white-space: nowrap;
  padding: 0 8px;
}
</style>
