<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listProviders, createProvider, updateProvider, deleteProvider,
  setDefaultProvider, testProvider, fetchProviderModels, listPresets, notifyDataChanged,
} from '../api'

const providers = ref([])
const presets = ref({})
const loading = ref(false)

const dialogVisible = ref(false)
const saving = ref(false)
const form = ref({ name: '', base_url: '', api_key: '', model: '', temperature: 70 })
const presetName = ref('')

const presetModels = ref([])
const fetchingModels = ref(false)

const testingId = ref(null)
const testResult = ref(null)

const load = async () => {
  loading.value = true
  try {
    providers.value = await listProviders()
    presets.value = await listPresets()
    const all = new Set()
    presets.value && Object.values(presets.value).forEach(p => p.model && all.add(p.model))
    providers.value.forEach(cfg => (cfg.models_cache || []).forEach(m => all.add(m)))
    providers.value.forEach(cfg => cfg.model && all.add(cfg.model))
    presetModels.value = [...all].sort()
  } catch (e) {
    ElMessage.error('加载失败：' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

const applyPreset = (name) => {
  const p = presets.value[name]
  if (!p) return
  presetName.value = name
  form.value.base_url = p.base_url
  form.value.model = p.model
}

const openCreate = () => {
  form.value = { name: '', base_url: '', api_key: '', model: '', temperature: 70 }
  presetName.value = ''
  dialogVisible.value = true
}

const submit = async () => {
  if (!form.value.name.trim() || !form.value.base_url.trim()) {
    ElMessage.warning('请填写名称和 Base URL')
    return
  }
  saving.value = true
  try {
    await createProvider(form.value)
    ElMessage.success('提供商已添加')
    dialogVisible.value = false
    load()
    notifyDataChanged()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

const removeProvider = async (cfg) => {
  try {
    await ElMessageBox.confirm(`删除提供商「${cfg.name}」？`, '删除', {
      type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消',
    })
    await deleteProvider(cfg.id)
    ElMessage.success('已删除')
    load()
    notifyDataChanged()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }
}

const makeDefault = async (cfg) => {
  await setDefaultProvider(cfg.id)
  ElMessage.success(`已将「${cfg.name}」设为默认`)
  load()
  notifyDataChanged()
}

const runTest = async (cfg) => {
  testingId.value = cfg.id
  testResult.value = null
  try {
    const res = await testProvider(cfg.id)
    testResult.value = { cfgId: cfg.id, ...res }
    if (res.ok) {
      ElMessage.success(`连接成功（${res.latency_ms}ms，${res.models.length} 个模型）`)
      load()
    } else {
      ElMessage.error('连接失败：' + (res.error || '未知错误'))
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '测试失败')
  } finally {
    testingId.value = null
  }
}

const runFetchModels = async (cfg) => {
  fetchingModels.value = cfg.id
  try {
    const res = await fetchProviderModels(cfg.id)
    if (res.ok) {
      ElMessage.success(`已拉取 ${res.models.length} 个模型并保存`)
      load()
    } else {
      ElMessage.error('拉取失败：' + (res.error || '未知错误'))
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '拉取失败')
  } finally {
    fetchingModels.value = null
  }
}

const editDialogVisible = ref(false)
const editForm = ref({ id: null, model: '' })
const editCfg = ref(null)
const openEdit = (cfg) => {
  editCfg.value = cfg
  editForm.value = { id: cfg.id, model: cfg.model || '' }
  editDialogVisible.value = true
}
const submitEdit = async () => {
  try {
    await updateProvider(editForm.value.id, { model: editForm.value.model })
    ElMessage.success('已更新')
    editDialogVisible.value = false
    load()
    notifyDataChanged()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '更新失败')
  }
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="ai-header">
      <div>
        <h2 style="margin: 0">AI 提供商配置</h2>
        <p style="color: #909399; font-size: 13px; margin: 6px 0 0">
          配置 Waypoint Copilot 使用的模型服务，支持多个并存、随时切换默认。
          API Key 仅保存在本地数据库，不会外传。
        </p>
      </div>
      <el-button type="primary" @click="openCreate">
        <i class="fas fa-plus" style="margin-right: 4px"></i>添加提供商
      </el-button>
    </div>

    <div v-loading="loading" style="margin-top: 16px">
      <el-empty v-if="!providers.length && !loading" description="还没有配置提供商，点击右上角添加">
        <el-button type="primary" @click="openCreate">添加第一个提供商</el-button>
      </el-empty>

      <el-row :gutter="16">
        <el-col v-for="cfg in providers" :key="cfg.id" :span="12" style="margin-bottom: 16px">
          <el-card shadow="never" class="provider-card" :class="{ 'is-default': cfg.is_default }">
            <div class="provider-head">
              <span class="provider-icon"><i class="fas fa-robot"></i></span>
              <div>
                <div class="provider-name">
                  {{ cfg.name }}
                  <el-tag v-if="cfg.is_default" size="small" type="success" effect="light">默认</el-tag>
                </div>
                <div class="provider-url">{{ cfg.base_url }}</div>
              </div>
              <div style="flex: 1"></div>
              <el-dropdown trigger="click" @command="(cmd) => {
                if (cmd === 'edit') openEdit(cfg)
                else if (cmd === 'default') makeDefault(cfg)
                else if (cmd === 'delete') removeProvider(cfg)
              }">
                <el-button text><i class="fas fa-ellipsis-v"></i></el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="default"><i class="fas fa-star" style="margin-right: 4px"></i>设为默认</el-dropdown-item>
                    <el-dropdown-item command="edit"><i class="fas fa-pen" style="margin-right: 4px"></i>编辑模型</el-dropdown-item>
                    <el-dropdown-item command="delete" divided><i class="fas fa-trash" style="margin-right: 4px; color: #f56c6c"></i>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>

            <div class="provider-body">
              <div class="kv"><span>模型</span><b>{{ cfg.model || '—' }}</b></div>
              <div class="kv"><span>API Key</span><code>{{ cfg.api_key_masked || '未设置' }}</code></div>
              <div class="kv"><span>温度</span><b>{{ cfg.temperature / 100 }}</b></div>
            </div>

            <div class="provider-foot">
              <el-button size="small" :loading="testingId === cfg.id" @click="runTest(cfg)">
                <i class="fas fa-plug" style="margin-right: 4px"></i>测试连接
              </el-button>
              <el-button size="small" :loading="fetchingModels === cfg.id" @click="runFetchModels(cfg)">
                <i class="fas fa-cloud-download-alt" style="margin-right: 4px"></i>拉取模型
              </el-button>
              <div v-if="testResult && testResult.cfgId === cfg.id" class="test-result" :class="{ ok: testResult.ok }">
                <template v-if="testResult.ok">
                  <i class="fas fa-circle-check"></i>
                  {{ testResult.latency_ms }}ms · {{ testResult.models.length }} 模型
                </template>
                <template v-else>
                  <i class="fas fa-circle-xmark"></i> {{ testResult.error }}
                </template>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <el-dialog v-model="dialogVisible" title="添加 AI 提供商" width="520px">
      <el-form label-width="90px">
        <el-form-item label="快捷预设">
          <el-select v-model="presetName" placeholder="选择后自动填入" style="width: 100%" clearable @change="applyPreset">
            <el-option v-for="(v, k) in presets" :key="k" :label="k" :value="k" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="例如：DeepSeek / 本地 Ollama" />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="https://api.deepseek.com/v1" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
        </el-form-item>
        <el-form-item label="模型">
          <el-select
            v-model="form.model"
            placeholder="选择或输入模型名"
            style="width: 100%"
            filterable
            allow-create
            default-first-option
          >
            <el-option v-for="m in presetModels" :key="m" :label="m" :value="m" />
          </el-select>
          <div class="model-hint">
            可从下拉选择预设/已缓存模型，也可直接输入；保存提供商后可点「拉取模型」自动获取该服务全部模型。
          </div>
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="form.temperature" :min="0" :max="100" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" :title="`编辑 ${editCfg?.name || ''} 的模型`" width="420px">
      <el-form label-width="60px">
        <el-form-item label="模型">
          <el-select
            v-model="editForm.model"
            placeholder="选择或输入模型名"
            style="width: 100%"
            filterable
            allow-create
            default-first-option
          >
            <el-option v-for="m in (editCfg?.models_cache?.length ? editCfg.models_cache : presetModels)" :key="m" :label="m" :value="m" />
          </el-select>
          <div class="model-hint">优先使用该提供商已拉取的模型；也可点「拉取模型」更新列表。</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.ai-header { display: flex; justify-content: space-between; align-items: flex-start; }
.provider-card { border: 1px solid #e4e7ed; }
.provider-card.is-default { border-color: #67c23a; }
.provider-head { display: flex; align-items: center; gap: 12px; }
.provider-icon {
  width: 42px; height: 42px; border-radius: 10px;
  background: linear-gradient(135deg, #409EFF, #67c23a);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
}
.provider-name { font-weight: 600; display: flex; align-items: center; gap: 6px; }
.provider-url { color: #909399; font-size: 12px; word-break: break-all; }
.provider-body { margin: 12px 0; }
.kv { display: flex; justify-content: space-between; padding: 3px 0; font-size: 13px; }
.kv span { color: #909399; }
.kv code { background: #f5f7fa; padding: 1px 6px; border-radius: 3px; font-size: 12px; }
.provider-foot { display: flex; align-items: center; gap: 12px; }
.model-hint { color: #c0c4cc; font-size: 12px; line-height: 1.5; margin-top: 4px; }
.test-result { font-size: 12px; }
.test-result.ok { color: #67c23a; }
.test-result:not(.ok) { color: #f56c6c; word-break: break-all; }
</style>
