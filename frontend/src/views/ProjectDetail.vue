<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getProject, deleteProject, listColumns, updateProject, notifyDataChanged } from '../api'
import KanbanView from './KanbanView.vue'
import GanttView from './GanttView.vue'

const route = useRoute()
const router = useRouter()
const project = ref(null)
const loading = ref(false)
const activeTab = ref('kanban')

const load = async () => {
  loading.value = true
  try {
    const p = await getProject(route.params.id)
    const cols = await listColumns(route.params.id)
    p.columns = cols
    project.value = p
  } catch (e) {
    ElMessage.error('加载项目失败：' + (e.response?.data?.detail || e.message))
    router.push('/')
  } finally {
    loading.value = false
  }
}

const confirmDelete = async () => {
  try {
    await deleteProject(project.value.id)
    ElMessage.success('项目已删除')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const togglingArchive = ref(false)
const toggleArchive = async () => {
  const isArchiving = project.value.status !== 'archived'
  togglingArchive.value = true
  try {
    await updateProject(project.value.id, { status: isArchiving ? 'archived' : 'active' })
    ElMessage.success(isArchiving ? '项目已归档，将不再计入「航行中项目」' : '项目已恢复航行')
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    togglingArchive.value = false
  }
}

const editVisible = ref(false)
const editForm = ref({})

const openEdit = () => {
  const p = project.value
  editForm.value = {
    name: p.name,
    description: p.description,
    color: p.color,
    dates: p.start_date && p.end_date ? [p.start_date, p.end_date] : null,
  }
  editVisible.value = true
}

const submitEdit = async () => {
  if (!editForm.value.name?.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  try {
    await updateProject(project.value.id, {
      name: editForm.value.name,
      description: editForm.value.description,
      color: editForm.value.color,
      start_date: editForm.value.dates?.[0] || null,
      end_date: editForm.value.dates?.[1] || null,
    })
    ElMessage.success('项目已更新')
    editVisible.value = false
    load()
    notifyDataChanged()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="page" v-loading="loading">
    <template v-if="project">
      <div class="project-header">
        <div class="header-left">
          <span class="dot" :style="{ background: project.color }"></span>
          <h2>{{ project.name }}</h2>
          <el-tag v-if="project.status === 'archived'" size="small" type="info">已归档</el-tag>
          <span class="date-range">
            <i class="far fa-calendar-alt"></i>
            {{ project.start_date || '—' }} ~ {{ project.end_date || '—' }}
          </span>
        </div>
        <div class="header-right">
          <el-button text :loading="togglingArchive" @click="toggleArchive">
            <i class="fas" :class="project.status === 'archived' ? 'fa-ship' : 'fa-archive'" style="margin-right: 4px"></i>
            {{ project.status === 'archived' ? '恢复航行' : '归档' }}
          </el-button>
          <el-button text @click="openEdit">
            <i class="fas fa-pen" style="margin-right: 4px"></i> 编辑
          </el-button>
          <el-button text type="danger" @click="confirmDelete">
            <i class="far fa-trash-alt"></i> 删除项目
          </el-button>
        </div>
      </div>

      <p class="desc">{{ project.description || '暂无描述' }}</p>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="看板" name="kanban">
          <i class="fas fa-columns" style="margin-right: 4px"></i>
        </el-tab-pane>
        <el-tab-pane label="甘特图" name="gantt">
          <i class="fas fa-chart-line" style="margin-right: 4px"></i>
        </el-tab-pane>
      </el-tabs>

      <!-- v-if 而非 v-show：切 tab 时重新挂载，保证从后端拉取最新数据
           （甘特图改期/进度后切回看板，看板必须显示最新任务） -->
      <KanbanView v-if="activeTab === 'kanban'" :project="project" @changed="load" />
      <GanttView v-if="activeTab === 'gantt'" :project="project" @changed="load" />
    </template>

    <el-dialog v-model="editVisible" title="编辑项目" width="480px">
      <el-form label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="editForm.name" maxlength="100" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="editForm.dates"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="主题色">
          <el-color-picker v-model="editForm.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.header-left h2 { margin: 0; font-size: 22px; }
.dot { width: 14px; height: 14px; border-radius: 50%; }
.date-range { color: #909399; font-size: 13px; }
.desc { color: #909399; margin: 8px 0 0; }
</style>
