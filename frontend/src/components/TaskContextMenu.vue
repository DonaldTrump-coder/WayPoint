<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  visible: Boolean,
  x: Number,
  y: Number,
  task: Object,   // { id, title }
  project: Object, // { id, name }
})
const emit = defineEmits(['update:visible', 'close'])

const router = useRouter()

const close = () => emit('update:visible', false)
watch(() => props.visible, (v) => {
  if (v) {
    setTimeout(() => document.addEventListener('click', close), 0)
  } else {
    document.removeEventListener('click', close)
  }
})

const openNote = () => {
  emit('update:visible', false)
  router.push({ path: '/notes', query: { task: props.task.id } })
}

const openEdit = () => {
  emit('update:visible', false)
  emit('close')
  emit('edit-task', props.task)
}
</script>

<template>
  <teleport to="body">
    <div
      v-if="visible"
      class="task-ctx-menu"
      :style="{ left: x + 'px', top: y + 'px' }"
      @click.stop
    >
      <div class="ctx-item" @click="openNote">
        <i class="fas fa-book-open" style="margin-right: 8px; color: #409eff"></i> 打开笔记
      </div>
      <div class="ctx-item" @click="openEdit">
        <i class="fas fa-pen" style="margin-right: 8px; color: #909399"></i> 编辑任务
      </div>
    </div>
  </teleport>
</template>

<style scoped>
.task-ctx-menu {
  position: fixed;
  z-index: 3000;
  min-width: 140px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  padding: 6px;
  font-size: 13px;
}
.ctx-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  color: #303133;
  transition: background 0.12s;
}
.ctx-item:hover { background: #ecf5ff; color: #409eff; }
</style>
