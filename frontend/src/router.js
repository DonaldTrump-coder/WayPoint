import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import ProjectDetail from './views/ProjectDetail.vue'
import Settings from './views/Settings.vue'
import AISettings from './views/AISettings.vue'
import NotesView from './views/NotesView.vue'

const routes = [
  { path: '/', name: 'dashboard', component: Dashboard },
  { path: '/project/:id', name: 'project', component: ProjectDetail, props: true },
  { path: '/notes', name: 'notes', component: NotesView },
  { path: '/settings', name: 'settings', component: Settings },
  { path: '/settings/ai', name: 'ai-settings', component: AISettings },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
