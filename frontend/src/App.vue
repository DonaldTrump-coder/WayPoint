<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AIChatPanel from './components/AIChatPanel.vue'

const route = useRoute()
const router = useRouter()
const aiOpen = ref(false)

onMounted(() => {
  window.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key.toLowerCase() === 'k') {
      e.preventDefault()
      aiOpen.value = !aiOpen.value
    }
  })
})

const goHome = () => router.push('/')

const onDrawerOpen = () => {
  window.dispatchEvent(new CustomEvent('wp:data-changed'))
}
</script>

<template>
  <div class="wp-shell">
    <header class="wp-navbar">
      <div class="wp-logo" @click="goHome">
        <img src="/icon.png" alt="Waypoint" class="logo-mark" />
        <span>Waypoint</span>
      </div>

      <el-breadcrumb separator="/" style="margin-left: 8px">
        <el-breadcrumb-item v-if="route.name === 'project'">项目</el-breadcrumb-item>
        <el-breadcrumb-item v-if="route.name === 'notes'">笔记</el-breadcrumb-item>
        <el-breadcrumb-item v-if="route.name === 'settings'">设置</el-breadcrumb-item>
        <el-breadcrumb-item v-if="route.name === 'ai-settings'">AI 提供商</el-breadcrumb-item>
      </el-breadcrumb>

      <div style="flex: 1"></div>

      <el-tooltip content="笔记" placement="bottom">
        <el-button
          :class="{ 'is-active': route.name === 'notes' }"
          circle
          @click="router.push('/notes')"
        >
          <i class="fas fa-book-open"></i>
        </el-button>
      </el-tooltip>
      <el-tooltip content="AI Copilot (Ctrl+K)" placement="bottom">
        <el-button :class="{ 'is-active': aiOpen }" circle @click="aiOpen = !aiOpen">
          <i class="fas fa-robot"></i>
        </el-button>
      </el-tooltip>
      <el-tooltip content="设置" placement="bottom">
        <el-button circle @click="router.push('/settings')">
          <i class="fas fa-cog"></i>
        </el-button>
      </el-tooltip>
    </header>

    <main class="wp-main">
      <router-view />
    </main>

    <!-- AI 侧边栏：不销毁组件（保留思考开关/聊天记录）；每次打开时触发
         wp:data-changed 让面板重新检测提供商（配置后打开也能立即刷新） -->
    <el-drawer
      v-model="aiOpen"
      title="Waypoint Copilot"
      direction="rtl"
      size="380px"
      :with-header="true"
      @open="onDrawerOpen"
    >
      <AIChatPanel />
    </el-drawer>
  </div>
</template>

<style scoped>
.wp-shell { min-height: 100vh; display: flex; flex-direction: column; }
.wp-main { flex: 1; }
</style>
