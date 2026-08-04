<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { agentTools, listProviders, selectProviderModel, notifyDataChanged, getChatHistory, addChatHistory, clearChatHistory, getChatState, setChatState, agentChatStream } from '../api'

const messages = ref([])
const input = ref('')
const sending = ref(false)
const tools = ref([])
const hasProvider = ref(false)
const providerCheckDone = ref(false)
const scrollRef = ref(null)

const thinking = ref(false)

const onThinkingChange = (val) => {
  setChatState(!!val).catch(() => {  })
}

const chatVisible = ref(false)

const providers = ref([])
const currentModel = ref('')
const switchingModel = ref(false)

const modelGroups = computed(() =>
  providers.value.map(p => ({
    label: p.name,
    options: (p.models_cache?.length ? p.models_cache : (p.model ? [p.model] : [])),
  })).filter(g => g.options.length)
)

const selectedModelKey = computed(() => {
  const def = providers.value.find(p => p.is_default)
  return def ? `${def.name}:${def.model || ''}` : ''
})

const switchModel = async (key) => {
  if (!key) return
  const idx = key.lastIndexOf(':')
  const pname = key.slice(0, idx)
  const model = key.slice(idx + 1)
  const prov = providers.value.find(p => p.name === pname)
  if (!prov || !model || switchingModel.value) return
  switchingModel.value = true
  try {
    const updated = await selectProviderModel(prov.id, model)
    currentModel.value = updated.model
    providers.value = await listProviders()
    ElMessage.success(`已切换：${updated.name} / ${updated.model}`)
    notifyDataChanged()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '切换模型失败')
  } finally {
    switchingModel.value = false
  }
}

const clearChat = async () => {
  try {
    await clearChatHistory()
  } catch {  }
  messages.value = []
  messages.value.push({
    role: 'assistant',
    content: hasProvider.value
      ? '👋 聊天记录已清空。我是 Waypoint Copilot，可以用自然语言管理你的项目、任务和笔记。'
      : '👋 聊天记录已清空。我是 Waypoint Copilot，但还没有配置 AI 提供商。请先到 设置 → AI 提供商 添加并设为默认。',
  })
  ElMessage.success('聊天记录已清空')
}

const scrollToBottom = async () => {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}

const init = async () => {
  try {
    tools.value = await agentTools()
    providers.value = await listProviders()
    hasProvider.value = providers.value.length > 0
    const def = providers.value.find(p => p.is_default)
    currentModel.value = def?.model || ''
  } catch {  }
  providerCheckDone.value = true

  try {
    const state = await getChatState()
    thinking.value = !!state.thinking
  } catch {  }

  try {
    const history = await getChatHistory()
    if (history.length) {
      messages.value = history.map(m => ({ role: m.role, content: m.content }))
    }
  } catch {  }

  if (!messages.value.length) {
    messages.value.push({
      role: 'assistant',
      content: hasProvider.value
        ? '👋 我是 Waypoint Copilot。可以用自然语言管理你的项目，例如：\n\n• "帮我建一个任务，下周五截止"\n• "把所有进行中的任务列出来"\n• "给某个任务写一篇笔记总结进展"\n\n试试吧！'
        : '👋 我是 Waypoint Copilot，但还没有配置 AI 提供商。请先到 设置 → AI 提供商 添加并设为默认。',
    })
  }
}

const send = async () => {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''

  messages.value.push({ role: 'user', content: text })
  addChatHistory('user', text).catch(() => {})
  sending.value = true

  const bubble = { role: 'assistant', content: '', streaming: true }
  messages.value.push(bubble)
  scrollToBottom()

  const history = messages.value
    .filter(m => m.role !== 'tool')
    .slice(-20)
    .map(m => ({ role: m.role, content: m.content }))

  let usedTools = false
  let finalContent = ''
  await agentChatStream(history, thinking.value, async (evt) => {
    if (evt.type === 'delta') {
      bubble.content += evt.content
      finalContent += evt.content
      scrollToBottom()
    } else if (evt.type === 'tool') {
      usedTools = true
      notifyDataChanged()
    } else if (evt.type === 'error') {
      bubble.content = '❌ ' + evt.content
      bubble.error = true
      finalContent = bubble.content
    } else if (evt.type === 'end' || evt.type === 'done') {
    }
  })
  bubble.streaming = false
  if (finalContent && !finalContent.startsWith('❌')) {
    addChatHistory('assistant', finalContent).catch(() => {})
  }
  if (usedTools) notifyDataChanged()
  sending.value = false
  scrollToBottom()
}

const quickActions = [
  { label: '列出所有项目', prompt: '列出所有项目及其进度' },
  { label: '创建任务', prompt: '帮我创建一个任务（请告诉我项目名和任务内容）' },
  { label: '查看逾期', prompt: '有哪些逾期任务？' },
]

const applyQuick = (p) => { input.value = p }

const refreshProvider = async () => {
  try {
    providers.value = await listProviders()
    hasProvider.value = providers.value.length > 0
    const def = providers.value.find(p => p.is_default)
    currentModel.value = def?.model || ''
  } catch {  }
}

onMounted(() => {
  window.addEventListener('wp:data-changed', refreshProvider)
  init()
})
onBeforeUnmount(() => {
  window.removeEventListener('wp:data-changed', refreshProvider)
})
</script>

<template>
  <div class="chat-panel">
    <div v-if="providerCheckDone && hasProvider" class="tools-banner">
      <div class="tools-top">
        <div class="tools-title"><i class="fas fa-wrench"></i> 可用工具：{{ tools.length }} 个</div>
        <div style="flex: 1"></div>
        <el-switch v-model="thinking" size="small" active-text="思考" inactive-text="" style="margin-right: 10px" @change="onThinkingChange" />
        <el-button text size="small" @click="clearChat" title="清空聊天记录（含传给 LLM 的历史）">
          <i class="fas fa-eraser" style="margin-right: 4px"></i>清空
        </el-button>
      </div>
      <div class="model-select-row">
        <span class="model-select-label"><i class="fas fa-microchip"></i> 模型</span>
        <el-select
          :model-value="selectedModelKey"
          size="small"
          style="flex: 1"
          placeholder="选择模型"
          :loading="switchingModel"
          @change="switchModel"
        >
          <el-option-group v-for="g in modelGroups" :key="g.label" :label="g.label">
            <el-option v-for="m in g.options" :key="g.label + ':' + m" :label="m" :value="g.label + ':' + m" />
          </el-option-group>
        </el-select>
      </div>
      <div class="tools-list">
        <el-tag v-for="t in tools" :key="t" size="small" effect="plain" round>{{ t }}</el-tag>
      </div>
    </div>
    <el-alert
      v-else-if="providerCheckDone"
      class="no-provider-alert"
      type="warning"
      :closable="false"
      title="未配置 AI 提供商"
      description="请到 设置 → AI 提供商 添加并设为默认后使用。"
      show-icon
    />

    <div ref="scrollRef" class="chat-messages">
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="msg"
        :class="[m.role, { error: m.error }]"
      >
        <div class="msg-avatar">
          <i :class="m.role === 'user' ? 'fas fa-user' : 'fas fa-robot'"></i>
        </div>
        <div class="msg-body">
          <div class="msg-content" :class="{ streaming: m.streaming }">{{ m.content }}<span v-if="m.streaming" class="stream-cursor"></span></div>
        </div>
      </div>

      <div v-if="sending" class="msg assistant">
        <div class="msg-avatar"><i class="fas fa-robot"></i></div>
        <div class="msg-body">
          <div class="typing"><span></span><span></span><span></span></div>
        </div>
      </div>
    </div>

    <div class="quick-row" v-if="hasProvider">
      <el-button v-for="q in quickActions" :key="q.label" size="small" round @click="applyQuick(q.prompt)">
        {{ q.label }}
      </el-button>
    </div>

    <div class="chat-input">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        resize="none"
        placeholder="输入指令，Enter 发送…"
        :disabled="sending || !hasProvider"
        @keydown.enter.exact.prevent="send"
      />
      <el-button type="primary" circle :loading="sending" :disabled="!hasProvider" @click="send">
        <i class="fas fa-paper-plane"></i>
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.chat-panel { display: flex; flex-direction: column; height: 100%; }
.tools-banner { padding-bottom: 10px; border-bottom: 1px solid #f0f2f5; margin-bottom: 10px; }
.tools-top { display: flex; align-items: center; margin-bottom: 6px; }
.tools-title { font-size: 12px; color: #909399; }
.model-select-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.model-select-label { font-size: 12px; color: #606266; white-space: nowrap; }
.model-select-label i { color: #409EFF; margin-right: 3px; }
.no-provider-alert { margin-bottom: 14px; }
.tools-list { display: flex; flex-wrap: wrap; gap: 4px; }

.chat-messages { flex: 1; overflow-y: auto; padding-right: 4px; }
.msg { display: flex; gap: 8px; margin-bottom: 14px; }
.msg-avatar {
  width: 30px; height: 30px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; color: #fff;
}
.msg.user .msg-avatar { background: #409EFF; }
.msg.assistant .msg-avatar { background: #67c23a; }
.msg-body { flex: 1; min-width: 0; }
.msg-content {
  background: #f5f7fa; border-radius: 8px; padding: 8px 12px;
  font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word;
}
.msg.user .msg-content { background: #ecf5ff; }
.msg.error .msg-content { color: #f56c6c; }
.stream-cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  margin-left: 2px;
  vertical-align: -2px;
  background: #409EFF;
  animation: stream-blink 0.8s infinite;
}
@keyframes stream-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.typing { display: flex; gap: 4px; padding: 4px 2px; }
.typing span {
  width: 6px; height: 6px; border-radius: 50%; background: #c0c4cc;
  animation: blink 1.2s infinite;
}
.typing span:nth-child(2) { animation-delay: 0.2s; }
.typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.2; } 40% { opacity: 1; } }

.quick-row { display: flex; gap: 6px; flex-wrap: wrap; padding: 8px 0; }
.chat-input { display: flex; gap: 8px; align-items: flex-end; }
.chat-input .el-textarea { flex: 1; }
</style>
