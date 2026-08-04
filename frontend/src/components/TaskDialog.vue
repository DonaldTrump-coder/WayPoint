<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  createTask, updateTask, deleteTask,
  createSubtask, updateSubtask, deleteSubtask,
  adjustProgress, notifyDataChanged,
} from '../api'

const props = defineProps({
  visible: Boolean,
  project: Object,
  task: Object,
  defaultStatus: String,
  defaultMilestone: Boolean,
})

const emit = defineEmits(['update:visible', 'saved', 'deleted'])

const form = ref({})
const saving = ref(false)

const dialogVisible = computed({
  get: () => props.visible,
  set: (v) => emit('update:visible', v),
})

const isEdit = computed(() => !!props.task)

const statusOptions = computed(() => {
  const cols = props.project?.columns || []
  if (cols.length) return cols.map(c => ({ value: c.status, label: c.name }))
  return [
    { value: 'backlog', label: '待办' },
    { value: 'in_progress', label: '进行中' },
    { value: 'done', label: '已完成' },
  ]
})

const newSubtaskTitle = ref('')
const addingSubtask = ref(false)

watch(
  () => props.visible,
  (v) => {
    if (!v) return
    if (props.task) {
      form.value = JSON.parse(JSON.stringify(props.task))
    } else {
      form.value = {
        title: '',
        description: '',
        status: props.defaultStatus || 'backlog',
        priority: 'medium',
        start_date: null,
        due_date: null,
        is_milestone: !!props.defaultMilestone,
      }
    }
    newSubtaskTitle.value = ''
    addingSubtask.value = false
  }
)

const save = async () => {
  if (!form.value.title?.trim()) {
    ElMessage.warning('请输入任务标题')
    return
  }
  saving.value = true
  try {
    const payload = {
      title: form.value.title,
      description: form.value.description,
      status: form.value.status,
      priority: form.value.priority,
      start_date: form.value.start_date || null,
      due_date: form.value.due_date || null,
      is_milestone: !!form.value.is_milestone,
    }
    if (isEdit.value) {
      await updateTask(props.task.id, payload)
      ElMessage.success('任务已更新')
    } else {
      await createTask(props.project.id, payload)
      ElMessage.success('任务已创建')
    }
    dialogVisible.value = false
    emit('saved')
    notifyDataChanged()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const remove = async () => {
  try {
    await deleteTask(props.task.id)
    ElMessage.success('任务已删除')
    dialogVisible.value = false
    emit('deleted')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const addSubtask = async () => {
  if (!newSubtaskTitle.value.trim()) return
  addingSubtask.value = true
  try {
    await createSubtask(props.task.id, newSubtaskTitle.value.trim())
    newSubtaskTitle.value = ''
    const updated = await import('../api').then(m => m.getTask(props.task.id))
    form.value.subtasks = updated.subtasks
    form.value.progress = updated.progress
    form.value.status = updated.status
    emit('saved')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  } finally {
    addingSubtask.value = false
  }
}

const toggleSubtask = async (st) => {
  try {
    const updated = await updateSubtask(st.id, { done: !st.done })
    st.done = updated.done
    const task = await import('../api').then(m => m.getTask(props.task.id))
    form.value.progress = task.progress
    form.value.status = task.status
    emit('saved')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  }
}

const removeSubtask = async (st) => {
  try {
    await deleteSubtask(st.id)
    form.value.subtasks = form.value.subtasks.filter(s => s.id !== st.id)
    const task = await import('../api').then(m => m.getTask(props.task.id))
    form.value.progress = task.progress
    form.value.status = task.status
    emit('saved')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const bumpProgress = async (delta) => {
  try {
    const task = await adjustProgress(props.task.id, delta)
    form.value.progress = task.progress
    emit('saved')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  }
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="isEdit ? '任务详情' : (form.is_milestone ? '新建里程碑' : '新建任务')"
    width="560px"
    top="6vh"
  >
    <el-form label-width="72px">
      <el-form-item label="标题">
        <el-input v-model="form.title" placeholder="任务标题" maxlength="300" />
      </el-form-item>

      <el-form-item label="类型">
        <el-switch
          v-model="form.is_milestone"
          active-text="里程碑"
          inactive-text="普通任务"
        />
      </el-form-item>

      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="任务详情（可选）" />
      </el-form-item>

      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="状态">
            <el-select v-model="form.status" style="width: 100%">
              <el-option
                v-for="s in statusOptions"
                :key="s.value"
                :label="s.label"
                :value="s.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="优先级">
            <el-select v-model="form.priority" style="width: 100%">
              <el-option label="低" value="low" />
              <el-option label="中" value="medium" />
              <el-option label="高" value="high" />
              <el-option label="紧急" value="urgent" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="开始日期">
            <el-date-picker v-model="form.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="可选" :disabled-date="d => form.due_date ? d.getTime() > new Date(form.due_date).getTime() : false" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="截止日期">
            <el-date-picker v-model="form.due_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="可选" :disabled-date="d => form.start_date ? d.getTime() < new Date(form.start_date).getTime() : false" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item v-if="isEdit" label="子任务">
        <div style="width: 100%">
          <div v-for="st in form.subtasks" :key="st.id" class="subtask-row">
            <el-checkbox :model-value="st.done" @change="toggleSubtask(st)">
              <span :class="{ 'st-done': st.done }">{{ st.title }}</span>
            </el-checkbox>
            <el-button text type="danger" size="small" @click="removeSubtask(st)">
              <i class="far fa-trash-alt"></i>
            </el-button>
          </div>
          <div class="subtask-add">
            <el-input
              v-model="newSubtaskTitle"
              size="small"
              placeholder="输入子任务，回车添加"
              style="flex: 1"
              @keyup.enter="addSubtask"
            />
            <el-button size="small" :loading="addingSubtask" @click="addSubtask">添加</el-button>
          </div>
          <div class="subtask-hint">
            勾选子任务自动累计任务进度（当前 {{ form.progress }}%）
          </div>
        </div>
      </el-form-item>

      <el-form-item v-if="isEdit && !form.subtasks?.length" label="进度">
        <div class="progress-row">
          <el-button size="small" @click="bumpProgress(-10)">-10</el-button>
          <el-progress :percentage="form.progress" style="flex: 1" :stroke-width="10" />
          <el-button size="small" @click="bumpProgress(10)">+10</el-button>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button v-if="isEdit" type="danger" text @click="remove">删除任务</el-button>
      <div style="flex: 1"></div>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.subtask-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2px 0;
}
.st-done { text-decoration: line-through; color: #c0c4cc; }
.subtask-add { display: flex; gap: 8px; margin-top: 8px; }
.subtask-hint { color: #c0c4cc; font-size: 12px; margin-top: 6px; }
.progress-row { display: flex; align-items: center; gap: 10px; width: 100%; }
</style>
