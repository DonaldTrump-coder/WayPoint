import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export const listProjects = () => http.get('/projects').then(r => r.data)
export const createProject = (data) => http.post('/projects', data).then(r => r.data)
export const getProject = (id) => http.get(`/projects/${id}`).then(r => r.data)
export const updateProject = (id, data) => http.patch(`/projects/${id}`, data).then(r => r.data)
export const deleteProject = (id) => http.delete(`/projects/${id}`)
export const getProjectStats = (id) => http.get(`/projects/${id}/stats`).then(r => r.data)

export const listTasks = (pid, params = {}) => http.get(`/projects/${pid}/tasks`, { params }).then(r => r.data)
export const createTask = (pid, data) => http.post(`/projects/${pid}/tasks`, data).then(r => r.data)
export const getTask = (id) => http.get(`/tasks/${id}`).then(r => r.data)
export const updateTask = (id, data) => http.patch(`/tasks/${id}`, data).then(r => r.data)
export const deleteTask = (id) => http.delete(`/tasks/${id}`)
export const moveTask = (id, data) => http.post(`/tasks/${id}/move`, data).then(r => r.data)
export const adjustProgress = (id, delta) => http.post(`/tasks/${id}/progress`, { delta }).then(r => r.data)

export const createSubtask = (taskId, title) => http.post(`/tasks/${taskId}/subtasks`, { title }).then(r => r.data)
export const updateSubtask = (id, data) => http.patch(`/subtasks/${id}`, data).then(r => r.data)
export const deleteSubtask = (id) => http.delete(`/subtasks/${id}`)

export const listColumns = (pid) => http.get(`/projects/${pid}/columns`).then(r => r.data)
export const createColumn = (pid, data) => http.post(`/projects/${pid}/columns`, data).then(r => r.data)
export const updateColumn = (id, data) => http.patch(`/kanban/columns/${id}`, data).then(r => r.data)
export const deleteColumn = (id) => http.delete(`/kanban/columns/${id}`)
export const reorderColumns = (pid, column_ids) => http.post(`/projects/${pid}/columns/reorder`, { column_ids })

// ---------- AI ----------
export const listProviders = () => http.get('/ai/providers').then(r => r.data)
export const createProvider = (data) => http.post('/ai/providers', data).then(r => r.data)
export const updateProvider = (id, data) => http.patch(`/ai/providers/${id}`, data).then(r => r.data)
export const deleteProvider = (id) => http.delete(`/ai/providers/${id}`)
export const setDefaultProvider = (id) => http.post(`/ai/providers/${id}/default`)
export const selectProviderModel = (providerId, model) => http.post('/ai/providers/select', { provider_id: providerId, model }).then(r => r.data)
export const testProvider = (id) => http.post(`/ai/providers/${id}/test`).then(r => r.data)
export const fetchProviderModels = (id) => http.post(`/ai/providers/${id}/models`).then(r => r.data)
export const listPresets = () => http.get('/ai/presets').then(r => r.data)
export const agentChat = (messages, thinking = false) => http.post('/agent/chat', { messages, thinking }).then(r => r.data)

export const agentChatStream = async (messages, thinking, onEvent) => {
  try {
    const res = await fetch('/api/agent/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages, thinking }),
    })
    if (!res.ok) {
      let detail = '流式请求失败'
      try { detail = (await res.json())?.detail || detail } catch { /* ignore */ }
      throw new Error(detail)
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      let idx
      while ((idx = buf.indexOf('\n\n')) >= 0) {
        const raw = buf.slice(0, idx)
        buf = buf.slice(idx + 2)
        const line = raw.split('\n').find(l => l.startsWith('data: '))
        if (!line) continue
        try {
          onEvent(JSON.parse(line.slice(6)))
        } catch {  }
      }
    }
  } catch (e) {
    onEvent({ type: 'error', content: e.message })
  }
}
export const agentTools = () => http.get('/agent/tools').then(r => r.data)
export const getChatHistory = () => http.get('/agent/history').then(r => r.data)
export const addChatHistory = (role, content) => http.post('/agent/history', { role, content }).then(r => r.data)
export const clearChatHistory = () => http.delete('/agent/history')
export const getChatState = () => http.get('/agent/state').then(r => r.data)
export const setChatState = (thinking) => http.post('/agent/state', { thinking }).then(r => r.data)

export const exportData = () => http.get('/export').then(r => r.data)
export const importData = (data) => http.post('/import', data).then(r => r.data)

export const listCalendarEvents = (start, end) => http.get('/calendar/events', { params: { start, end } }).then(r => r.data)
export const todaySummary = () => http.get('/calendar/today').then(r => r.data)
export const createCalendarEvent = (data) => http.post('/calendar/events', data).then(r => r.data)
export const deleteCalendarEvent = (id) => http.delete(`/calendar/events/${id}`)

export const listNotesTree = () => http.get('/notes/tree').then(r => r.data)
export const getTaskNote = (taskId) => http.get(`/notes/${taskId}`).then(r => r.data)
export const saveTaskNote = (taskId, content) => http.put(`/notes/${taskId}`, { content }).then(r => r.data)

export const notifyDataChanged = () => {
  window.dispatchEvent(new CustomEvent('wp:data-changed'))
}

export default http
