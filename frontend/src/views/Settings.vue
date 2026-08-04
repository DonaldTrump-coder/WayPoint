<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { exportData, importData } from '../api'

const router = useRouter()
const importVisible = ref(false)
const importText = ref('')

const doExport = async () => {
  try {
    const data = await exportData()
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `waypoint-backup-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('备份已导出')
  } catch (e) {
    ElMessage.error('导出失败：' + (e.response?.data?.detail || e.message))
  }
}

const doImport = async () => {
  try {
    const data = JSON.parse(importText.value)
    const res = await importData(data)
    ElMessage.success(`导入成功：${res.imported} 个任务`)
    importVisible.value = false
    importText.value = ''
  } catch (e) {
    ElMessage.error('导入失败：请检查 JSON 格式')
  }
}

const handleFile = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => { importText.value = e.target.result }
  reader.readAsText(file.raw)
  return false
}

onMounted(() => {})
</script>

<template>
  <div class="page">
    <h2 style="margin-top: 0">设置</h2>

    <el-card shadow="never" style="max-width: 640px">
      <template #header>
        <span><i class="fas fa-robot" style="margin-right: 6px; color: var(--wp-accent)"></i>AI 提供商</span>
      </template>
      <p style="color: #909399; font-size: 13px">
        配置 Waypoint Copilot 使用的 AI 提供商与模型，支持多个并存。
      </p>
      <el-button type="primary" @click="router.push('/settings/ai')">
        <i class="fas fa-sliders" style="margin-right: 4px"></i> 前往 AI 提供商配置
      </el-button>
    </el-card>

    <el-card shadow="never" style="max-width: 640px; margin-top: 16px">
      <template #header>
        <span><i class="fas fa-database" style="margin-right: 6px; color: #67c23a"></i>数据备份</span>
      </template>
      <p style="color: #909399; font-size: 13px">
        导出全部数据（项目 / 任务 / 笔记 / AI 模型配置 / 聊天记录 / 看板列 / 日历事件）为 JSON 文件；导入会清空现有数据后重建。
      </p>
      <el-space>
        <el-button @click="doExport"><i class="fas fa-download" style="margin-right: 4px"></i>导出备份</el-button>
        <el-button type="warning" @click="importVisible = true">
          <i class="fas fa-upload" style="margin-right: 4px"></i>导入恢复
        </el-button>
      </el-space>
    </el-card>

    <el-card shadow="never" style="max-width: 640px; margin-top: 16px">
      <template #header>
        <span><i class="fas fa-info-circle" style="margin-right: 6px"></i>关于</span>
      </template>
      <p style="color: #909399; font-size: 13px; line-height: 1.8">
        <b>Waypoint</b> — 本地个人项目跟进管理系统<br />
        数据保存在本机 <code>waypoint.db</code>（SQLite），无任何云端依赖。
      </p>
    </el-card>

    <el-dialog v-model="importVisible" title="导入备份" width="520px">
      <el-upload drag :auto-upload="false" :show-file-list="false" accept=".json" :on-change="handleFile">
        <i class="el-icon-upload" style="font-size: 40px; color: #c0c4cc"></i>
        <div>点击或拖拽 JSON 备份文件到此处</div>
      </el-upload>
      <el-alert
        v-if="importText"
        type="warning"
        title="导入将清空现有全部数据并重建，请确认备份文件正确。"
        style="margin-top: 12px"
      />
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!importText" @click="doImport">确认导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>
