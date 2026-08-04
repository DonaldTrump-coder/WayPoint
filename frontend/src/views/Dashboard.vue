<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listProjects, createProject, deleteProject } from '../api'
import RouteOverview from '../components/RouteOverview.vue'
import CalendarPanel from '../components/CalendarPanel.vue'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const newProject = ref({ name: '', description: '', color: '#16324F', start_date: null, end_date: null })

const overdueCount = computed(() =>
  projects.value.reduce((sum, p) => sum + (p.stats?.overdue_tasks || 0), 0)
)
const activeCount = computed(() => projects.value.filter(p => p.status === 'active').length)
const totalTasks = computed(() =>
  projects.value.reduce((sum, p) => sum + (p.stats?.total_tasks || 0), 0)
)

const load = async () => {
  loading.value = true
  try {
    projects.value = await listProjects()
  } catch (e) {
    ElMessage.error('加载项目失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  newProject.value = { name: '', description: '', color: '#16324F', start_date: null, end_date: null }
  dialogVisible.value = true
}

const submitCreate = async () => {
  if (!newProject.value.name.trim()) {
    ElMessage.warning('请输入项目名称')
    return
  }
  try {
    const payload = {
      name: newProject.value.name,
      description: newProject.value.description,
      color: newProject.value.color,
      start_date: newProject.value.dates?.[0] || null,
      end_date: newProject.value.dates?.[1] || null,
    }
    await createProject(payload)
    ElMessage.success('项目创建成功')
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建失败')
  }
}

const confirmDelete = async (p) => {
  try {
    await deleteProject(p.id)
    ElMessage.success(`已删除「${p.name}」`)
    load()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const openProject = (id) => router.push(`/project/${id}`)

const featuredProjects = computed(() => {
  const actives = projects.value.filter(p => p.status === 'active')
  const pool = actives.length ? actives : projects.value
  return [...pool].sort((a, b) => (b.stats?.progress || 0) - (a.stats?.progress || 0))
})

onMounted(load)
</script>

<template>
  <div class="page">
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-inner">
            <div class="stat-ico navy"><i class="fas fa-ship"></i></div>
            <div>
              <div class="stat-num num">{{ activeCount }}</div>
              <div class="stat-label">航行中项目</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-inner">
            <div class="stat-ico teal"><i class="fas fa-layer-group"></i></div>
            <div>
              <div class="stat-num num">{{ projects.length }}</div>
              <div class="stat-label">全部项目</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-inner">
            <div class="stat-ico amber"><i class="fas fa-clipboard-list"></i></div>
            <div>
              <div class="stat-num num">{{ totalTasks }}</div>
              <div class="stat-label">任务总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card" style="cursor: pointer" @click="openCreate">
          <div class="stat-inner">
            <div class="stat-ico coral"><i class="fas fa-compass"></i></div>
            <div>
              <div class="stat-num num" style="color: var(--wp-coral)">启航</div>
              <div class="stat-label">新建项目</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="overview-row">
      <div class="overview-left">
        <RouteOverview :projects="featuredProjects" :total="projects.length" />
      </div>
      <div class="overview-right">
        <CalendarPanel />
      </div>
    </div>

    <div v-loading="loading">
      <el-empty v-if="!projects.length && !loading" description="还没有项目，点击「启航」开始你的航程">
        <el-button type="primary" @click="openCreate">新建项目</el-button>
      </el-empty>

      <el-row :gutter="16">
        <el-col v-for="p in projects" :key="p.id" :span="8" style="margin-bottom: 16px">
          <el-card shadow="never" class="project-card" @click="openProject(p.id)">
            <div class="project-head">
              <span class="project-dot" :style="{ background: p.color }"></span>
              <span class="project-name">{{ p.name }}</span>
              <el-tag v-if="p.status === 'archived'" size="small" type="info">已归档</el-tag>
            </div>
            <div class="project-desc">{{ p.description || '暂无描述' }}</div>
            <div class="project-meta">
              <span><i class="far fa-calendar-alt"></i> {{ p.start_date || '—' }} ~ {{ p.end_date || '—' }}</span>
            </div>
            <div class="project-progress">
              <el-progress
                :percentage="p.stats?.progress || 0"
                :color="p.color"
                :stroke-width="8"
              />
              <span class="progress-text num">{{ p.stats?.done_tasks || 0 }}/{{ p.stats?.total_tasks || 0 }} 任务</span>
            </div>
            <div class="project-foot">
              <el-tag
                v-if="p.stats?.overdue_tasks"
                size="small"
                type="danger"
                effect="light"
              >{{ p.stats.overdue_tasks }} 个逾期</el-tag>
              <el-button
                size="small"
                type="danger"
                text
                class="delete-btn"
                @click.stop="confirmDelete(p)"
              >
                <i class="far fa-trash-alt"></i>
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="dialogVisible" title="新建项目" width="480px">
      <el-form label-width="80px">
        <el-form-item label="项目名称">
          <el-input v-model="newProject.name" placeholder="例如：GSSA 三维重建" maxlength="100" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="newProject.description" type="textarea" :rows="2" placeholder="项目简介（可选）" />
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="newProject.dates"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="主题色">
          <el-color-picker v-model="newProject.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.overview-row {
  display: flex;
  gap: 16px;
  align-items: stretch;   
  margin-bottom: 20px;
}
.overview-left {
  flex: 1;
  min-width: 0;           
  display: flex;
}
.overview-left :deep(.route-section) {
  flex: 1;
  height: 560px;          
  min-height: 0;
  overflow: hidden;       
  margin-bottom: 0;       
}
.overview-right {
  width: 420px;
  flex-shrink: 0;
}
@media (max-width: 1200px) {
  .overview-row { flex-direction: column; }
  .overview-left { display: block; }
  .overview-left :deep(.route-section) { overflow-y: visible; }
  .overview-right { width: 100%; }
}

</style>
