<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  projects: { type: Array, default: () => [] },
  total: { type: Number, default: 0 },
})

const router = useRouter()

const openProject = (id) => router.push(`/project/${id}`)

const fillStyle = (p) => {
  const pct = p.stats?.progress || 0
  return {
    width: pct + '%',
    background: `linear-gradient(90deg, ${p.color || '#409EFF'}, var(--wp-amber))`,
  }
}

const markerStyle = (p) => ({
  left: (p.stats?.progress || 0) + '%',
})
</script>

<template>
  <div class="route-section">
    <div class="route-head">
      <i class="fas fa-map-location-dot" style="color: var(--wp-teal)"></i>
      航路总览
      <span class="sub">— 项目进度</span>
    </div>

    <el-empty
      v-if="!projects.length"
      description="还没有项目，点击右上角「新建项目」启航"
      :image-size="72"
    />

    <div class="route-list">
      <div v-for="p in projects" :key="p.id" class="route-row" @click="openProject(p.id)">
        <div class="route-name">
          <span class="dot" :style="{ background: p.color }"></span>
          <span class="num">{{ p.name }}</span>
        </div>

        <div class="route-track">
          <div class="route-fill" :style="fillStyle(p)"></div>
          <div class="route-start" :style="{ background: p.color }"></div>
          <div class="route-marker" :style="markerStyle(p)"></div>
          <div class="route-goal" :class="{ reached: (p.stats?.progress || 0) >= 100 }"></div>
        </div>

        <div class="route-meta">
          <div class="route-pct num">{{ p.stats?.progress || 0 }}%</div>
          <div class="route-count num">{{ p.stats?.done_tasks || 0 }}/{{ p.stats?.total_tasks || 0 }} 任务</div>
        </div>

        <i class="fas fa-chevron-right route-arrow"></i>
      </div>
    </div>
  </div>
</template>

<style scoped>
.route-section {
  display: flex;
  flex-direction: column;
}
.route-head { flex-shrink: 0; }
.route-list {
  flex: 1;
  min-height: 0;          
  overflow-y: auto;
  margin-top: 2px;
}
.route-list::-webkit-scrollbar { width: 6px; }
.route-list::-webkit-scrollbar-thumb { background: #d3d7de; border-radius: 3px; }
</style>
