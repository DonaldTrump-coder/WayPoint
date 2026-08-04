<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listNotesTree, getTaskNote, saveTaskNote } from '../api'
import MdRenderer from '../components/MdRenderer.vue'

const route = useRoute()
const router = useRouter()

const tree = ref([])
const loading = ref(false)
const editorRef = ref(null)

const currentTask = ref(null)      // { id, title, projectId, projectName }
const content = ref('')
const savedAt = ref(null)
const saving = ref(false)
const dirty = ref(false)

let saveTimer = null
let lastSavedContent = ''

const loadTree = async () => {
  loading.value = true
  try {
    tree.value = await listNotesTree()
    tree.value.forEach(p => {
      if (p._expanded === undefined) p._expanded = true
    })
  } catch (e) {
    ElMessage.error('加载笔记树失败')
  } finally {
    loading.value = false
  }
}

const toggleProject = (p) => {
  p._expanded = !p._expanded
}

const selectTask = async (task, project) => {
  if (dirty.value && currentTask.value) {
    await doSave()
  }
  currentTask.value = { id: task.id, title: task.title, projectId: project.id, projectName: project.name }
  loading.value = true
  try {
    const note = await getTaskNote(task.id)
    content.value = note.content || ''
    lastSavedContent = content.value
    savedAt.value = note.updated_at
    dirty.value = false
    await nextTick()
    editorRef.value?.focus()
  } catch (e) {
    ElMessage.error('加载笔记失败')
  } finally {
    loading.value = false
  }
}

const jumpToTask = async (taskId) => {
  for (const p of tree.value) {
    const t = p.tasks.find(t => t.id === Number(taskId))
    if (t) { await selectTask(t, p); return }
  }
  await loadTree()
  for (const p of tree.value) {
    const t = p.tasks.find(t => t.id === Number(taskId))
    if (t) { await selectTask(t, p); return }
  }
  ElMessage.warning('未找到该任务')
}

const doSave = async () => {
  if (!currentTask.value) return
  saving.value = true
  try {
    const note = await saveTaskNote(currentTask.value.id, content.value)
    lastSavedContent = content.value
    savedAt.value = note.updated_at
    dirty.value = false
  } catch (e) {
    ElMessage.error('保存笔记失败')
  } finally {
    saving.value = false
  }
}

const scheduleSave = () => {
  dirty.value = true
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(doSave, 1500)
}

const saveNow = () => {
  if (saveTimer) clearTimeout(saveTimer)
  doSave()
}

const toolbarActions = [
  { label: 'H1', tip: '一级标题', run: () => wrap('# ', '') },
  { label: 'H2', tip: '二级标题', run: () => wrap('## ', '') },
  { label: 'H3', tip: '三级标题', run: () => wrap('### ', '') },
  { label: 'B', tip: '加粗', bold: true, run: () => wrap('**', '**') },
  { label: 'I', tip: '斜体', italic: true, run: () => wrap('*', '*') },
  { label: 'S', tip: '删除线', strike: true, run: () => wrap('~~', '~~') },
  { label: '`', tip: '行内代码', code: true, run: () => wrap('`', '`') },
  { label: '•', tip: '无序列表', run: () => wrap('- ', '') },
  { label: '1.', tip: '有序列表', run: () => wrap('1. ', '') },
  { label: '❝', tip: '引用', run: () => wrap('> ', '') },
  { label: '▦', tip: '代码块', run: () => wrap('```\n', '\n```') },
  { label: '🔗', tip: '链接', run: () => wrap('[', '](https://)') },
]

const wrap = (before, after) => {
  const el = editorRef.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  const sel = content.value.slice(start, end)
  const replacement = before + sel + after
  content.value = content.value.slice(0, start) + replacement + content.value.slice(end)
  nextTick(() => {
    el.focus()
    el.selectionStart = el.selectionEnd = start + before.length
  })
  dirty.value = true
  scheduleSave()
}

const onKeydown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    saveNow()
  }
}

const fmtTime = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(async () => {
  await loadTree()
  const q = route.query.task
  if (q) await jumpToTask(q)
})

watch(() => route.query.task, async (q) => {
  if (q) await jumpToTask(q)
})
</script>

<template>
  <div class="notes-page">
    <aside class="notes-side">
      <div class="side-header">
        <i class="fas fa-folder-open" style="margin-right: 6px"></i> 笔记库
        <el-button text size="small" style="margin-left: auto" @click="loadTree"><i class="fas fa-sync-alt"></i></el-button>
      </div>
      <div class="side-body" v-loading="loading">
        <template v-if="tree.length">
          <div v-for="p in tree" :key="p.id" class="tree-project">
            <div class="project-name" @click="toggleProject(p)">
              <i class="fas" :class="p._expanded ? 'fa-chevron-down' : 'fa-chevron-right'" style="margin-right: 4px; font-size: 11px; color: #909399"></i>
              <i class="fas" :class="p._expanded ? 'fa-folder-open' : 'fa-folder'" style="margin-right: 6px; color: #e6a23c"></i>
              <span class="project-label">{{ p.name }}</span>
              <span class="task-count">{{ p.tasks.length }}</span>
            </div>
            <div v-show="p._expanded">
              <div
                v-for="t in p.tasks"
                :key="t.id"
                class="tree-task"
                :class="{ active: currentTask && currentTask.id === t.id }"
                @click="selectTask(t, p)"
              >
                <i class="fas" :class="t.has_note ? 'fa-file-alt' : 'fa-file'" style="margin-right: 6px"
                   :style="{ color: t.has_note ? '#409eff' : '#c0c4cc' }"></i>
                <span class="task-title">{{ t.title }}</span>
                <span v-if="t.has_note" class="note-dot" title="已有笔记"></span>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="side-empty">暂无项目</div>
      </div>
    </aside>

    <section class="notes-editor">
      <div class="editor-header">
        <span class="editor-title">
          <i class="fas fa-file-alt" style="margin-right: 6px; color: #409eff"></i>
          {{ currentTask ? `${currentTask.projectName} / ${currentTask.title}` : '选择左侧任务查看笔记' }}
        </span>
        <span v-if="savedAt" class="saved-at">上次保存 {{ fmtTime(savedAt) }}</span>
        <span v-if="dirty" class="dirty-badge">未保存</span>
      </div>
      <div class="md-toolbar" v-if="currentTask">
        <el-tooltip v-for="a in toolbarActions" :key="a.label" :content="a.tip" placement="top">
          <button
            class="tool-btn"
            :class="{ 'tool-bold': a.bold, 'tool-italic': a.italic, 'tool-strike': a.strike, 'tool-code': a.code }"
            @mousedown.prevent
            @click="a.run"
          >{{ a.label }}</button>
        </el-tooltip>
        <div style="flex: 1"></div>
        <el-button size="small" type="primary" :loading="saving" @click="saveNow">
          <i class="fas fa-save" style="margin-right: 4px"></i>保存
        </el-button>
      </div>
      <textarea
        v-if="currentTask"
        ref="editorRef"
        v-model="content"
        class="md-editor"
        placeholder="在这里撰写 Markdown 笔记…（Ctrl+S 保存，输入停止后自动保存）"
        @input="scheduleSave"
        @keydown="onKeydown"
      ></textarea>
      <div v-else class="editor-placeholder">
        <i class="fas fa-book-open" style="font-size: 42px; color: #dcdfe6; margin-bottom: 12px"></i>
        <div>从左侧选择一个任务开始撰写笔记</div>
      </div>
    </section>

    <section class="notes-preview">
      <div class="preview-header">
        <i class="fas fa-eye" style="margin-right: 6px"></i> 预览
      </div>
      <div class="preview-body">
        <MdRenderer v-if="currentTask" :content="content" />
        <div v-else class="preview-empty">预览区</div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.notes-page {
  display: flex;
  height: calc(100vh - 64px);
  padding: 12px;
  gap: 12px;
  box-sizing: border-box;
}

.notes-side {
  width: 260px;
  min-width: 220px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.side-header {
  display: flex;
  align-items: center;
  padding: 12px 14px;
  font-weight: 600;
  border-bottom: 1px solid #f0f2f5;
  font-size: 14px;
}
.side-body { flex: 1; overflow-y: auto; padding: 10px 8px; }
.tree-project { margin-bottom: 14px; }
.project-name {
  display: flex;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  padding: 5px 8px;
  margin-bottom: 2px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
  user-select: none;
}
.project-name:hover { background: #f5f7fa; }
.project-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.task-count {
  background: #f0f2f5;
  color: #909399;
  font-size: 11px;
  border-radius: 8px;
  padding: 0 6px;
  line-height: 16px;
  flex-shrink: 0;
}
.tree-task {
  display: flex;
  align-items: center;
  padding: 6px 8px 6px 20px;
  font-size: 13px;
  color: #303133;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}
.tree-task:hover { background: #f5f7fa; }
.tree-task.active { background: #ecf5ff; color: #409eff; }
.task-title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.note-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #67c23a; flex-shrink: 0;
}
.side-empty { color: #c0c4cc; text-align: center; padding: 30px 0; font-size: 13px; }

.notes-editor {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 300px;
}
.editor-header {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid #f0f2f5;
  gap: 10px;
}
.editor-title { font-weight: 600; font-size: 13.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.saved-at { color: #909399; font-size: 12px; }
.dirty-badge { color: #e6a23c; font-size: 12px; }
.md-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f2f5;
  flex-wrap: wrap;
}
.tool-btn {
  min-width: 30px;
  height: 28px;
  padding: 0 8px;
  border: 1px solid #dcdfe6;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  color: #606266;
  transition: all 0.15s;
}
.tool-btn:hover { border-color: #409eff; color: #409eff; }
.tool-bold { font-weight: 700; }
.tool-italic { font-style: italic; }
.tool-strike { text-decoration: line-through; }
.tool-code { font-family: Consolas, monospace; }
.md-editor {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  padding: 16px;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.7;
  color: #303133;
  background: #fafbfc;
}
.editor-placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 14px;
}

.notes-preview {
  width: 42%;
  min-width: 320px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.preview-header {
  padding: 10px 14px;
  font-weight: 600;
  font-size: 13.5px;
  border-bottom: 1px solid #f0f2f5;
  color: #606266;
}
.preview-body { flex: 1; overflow-y: auto; padding: 16px 20px; }
.preview-empty { color: #c0c4cc; text-align: center; padding: 40px 0; }
</style>
