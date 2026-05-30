<template>
  <div class="settings-page">
    <h1>{{ $t('settings.title') }}</h1>
    <p class="subtitle">{{ $t('settings.subtitle') }}</p>

    <!-- 添加/编辑表单 -->
    <div class="panel form-panel">
      <h3>{{ editing ? $t('settings.editModel') : $t('settings.addModel') }}</h3>
      <div class="form-grid">
        <div class="form-group">
          <label>{{ $t('settings.preset') }}</label>
          <select v-model="formPreset" @change="applyPreset">
            <option value="">{{ $t('settings.custom') }}</option>
            <option v-for="p in presets" :key="p.name" :value="p.name">{{ p.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ $t('settings.name') }}</label>
          <input v-model="form.name" :placeholder="$t('settings.namePlaceholder')" />
        </div>
        <div class="form-group">
          <label>{{ $t('settings.type') }}</label>
          <select v-model="form.provider_type">
            <option value="openai">OpenAI</option>
            <option value="deepseek">DeepSeek</option>
            <option value="qwen">通义千问</option>
            <option value="mimo">MiMo</option>
            <option value="custom">{{ $t('settings.custom') }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>{{ $t('settings.baseUrl') }}</label>
          <input v-model="form.base_url" placeholder="https://api.example.com/v1" />
        </div>
        <div class="form-group">
          <label>{{ $t('settings.apiKey') }}</label>
          <input v-model="form.api_key" type="password" :placeholder="editing ? $t('settings.apiKeyKeep') : 'sk-...'" />
        </div>
        <div class="form-group">
          <label>{{ $t('settings.modelName') }}</label>
          <div class="model-input-row">
            <input v-model="form.model_name" placeholder="deepseek-chat" class="model-input" />
            <button class="secondary fetch-btn" @click="fetchModels" :disabled="fetchingModels"
              :title="$t('settings.fetchModels')">
              {{ fetchingModels ? '...' : $t('settings.fetchModels') }}
            </button>
          </div>
          <!-- 获取到的模型列表 -->
          <div v-if="availableModels.length" class="model-picker">
            <div class="model-picker-label">{{ $t('settings.selectFromList') }}</div>
            <select v-model="form.model_name" class="model-select">
              <option v-for="m in availableModels" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>
          <div v-if="fetchError" class="error">{{ fetchError }}</div>
        </div>
      </div>
      <div class="form-actions">
        <label class="checkbox-label">
          <input type="checkbox" v-model="form.is_default" /> {{ $t('settings.setDefault') }}
        </label>
        <div class="btn-group">
          <button @click="save" :disabled="saving">{{ saving ? '...' : $t('common.save') }}</button>
          <button class="secondary" v-if="editing" @click="cancelEdit">{{ $t('common.cancel') }}</button>
        </div>
      </div>
      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <!-- 模型列表 -->
    <div class="models-list">
      <div v-for="p in providers" :key="p.id" class="panel model-card" :class="{ active: p.is_default }">
        <div class="model-header">
          <div>
            <h3>{{ p.name }}</h3>
            <span class="tag">{{ p.provider_type }}</span>
            <span v-if="p.is_default" class="default-badge">{{ $t('settings.default') }}</span>
          </div>
          <div class="model-actions">
            <button class="secondary" @click="testConn(p.id)" :disabled="testingId === p.id">
              {{ testingId === p.id ? '...' : $t('settings.test') }}
            </button>
            <button class="secondary" @click="editProvider(p)">{{ $t('settings.edit') }}</button>
            <button class="secondary" @click="setDefault(p.id)" v-if="!p.is_default">{{ $t('settings.setDefault') }}</button>
            <button class="danger-btn" @click="remove(p.id)">{{ $t('settings.delete') }}</button>
          </div>
        </div>
        <div class="model-details">
          <span><b>{{ $t('settings.model') }}:</b> {{ p.model_name }}</span>
          <span><b>URL:</b> {{ p.base_url }}</span>
          <span><b>{{ $t('settings.key') }}:</b> {{ p.api_key }}</span>
        </div>
        <div v-if="testResults[p.id]" class="test-result" :class="testResults[p.id].ok ? 'ok' : 'fail'">
          {{ testResults[p.id].ok ? '✓' : '✗' }} {{ testResults[p.id].message }}
        </div>
      </div>
      <div v-if="!providers.length" class="empty">{{ $t('settings.noModels') }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '../api/client.js'

const { t } = useI18n()
const providers = ref([])
const presets = ref([])
const editing = ref(false)
const editingId = ref(null)
const saving = ref(false)
const error = ref('')
const testingId = ref(null)
const testResults = reactive({})
const formPreset = ref('')
const availableModels = ref([])
const fetchingModels = ref(false)
const fetchError = ref('')

const form = reactive({
  name: '', provider_type: 'openai', base_url: '', api_key: '', model_name: '', is_default: false,
})

onMounted(async () => {
  await Promise.all([loadProviders(), loadPresets()])
})

async function loadProviders() {
  try { const { data } = await api.get('/models'); providers.value = data.providers || [] } catch {}
}

async function loadPresets() {
  try { const { data } = await api.get('/models/presets'); presets.value = data.presets || [] } catch {}
}

function applyPreset() {
  const p = presets.value.find(x => x.name === formPreset.value)
  if (p) {
    form.name = p.name; form.provider_type = p.provider_type
    form.base_url = p.base_url; form.model_name = p.model_name
    form.api_key = ''; availableModels.value = []; fetchError.value = ''
  }
}

function resetForm() {
  form.name = ''; form.provider_type = 'openai'; form.base_url = ''
  form.api_key = ''; form.model_name = ''; form.is_default = false
  formPreset.value = ''; editing.value = false; editingId.value = null
  error.value = ''; availableModels.value = []; fetchError.value = ''
}

function editProvider(p) {
  editing.value = true; editingId.value = p.id
  form.name = p.name; form.provider_type = p.provider_type
  form.base_url = p.base_url; form.model_name = p.model_name
  form.is_default = !!p.is_default; form.api_key = ''
  availableModels.value = []; fetchError.value = ''
}

function cancelEdit() { resetForm() }

async function save() {
  error.value = ''
  if (!form.name || !form.base_url || !form.model_name) {
    error.value = t('settings.fillRequired'); return
  }
  if (!editing.value && !form.api_key) {
    error.value = t('settings.apiKeyRequired'); return
  }
  saving.value = true
  try {
    if (editing.value) {
      await api.put(`/models/${editingId.value}`, { ...form })
    } else {
      await api.post('/models', { ...form })
    }
    resetForm(); await loadProviders()
  } catch (e) { error.value = e.response?.data?.detail || t('login.failed') }
  finally { saving.value = false }
}

async function remove(id) {
  await api.delete(`/models/${id}`)
  await loadProviders()
}

async function setDefault(id) {
  await api.post(`/models/${id}/default`)
  await loadProviders()
}

async function testConn(id) {
  testingId.value = id; testResults[id] = null
  try { const { data } = await api.post(`/models/${id}/test`); testResults[id] = data }
  catch (e) { testResults[id] = { ok: false, message: e.response?.data?.detail || 'Error' } }
  finally { testingId.value = null }
}

async function fetchModels() {
  fetchError.value = ''
  availableModels.value = []

  if (!form.base_url) {
    fetchError.value = t('settings.saveFirst'); return
  }
  if (!form.api_key && !editing.value) {
    fetchError.value = t('settings.apiKeyRequired'); return
  }

  // 编辑模式下如果没填新的 key，需要先保存再用已保存的 key 获取
  if (editing.value && !form.api_key && editingId.value) {
    fetchingModels.value = true
    try {
      const { data } = await api.get(`/models/${editingId.value}/models`)
      availableModels.value = data.models || []
      if (!availableModels.value.length) fetchError.value = t('settings.noModelsFetched')
    } catch (e) { fetchError.value = e.response?.data?.detail || t('settings.fetchFailed') }
    finally { fetchingModels.value = false }
    return
  }

  // 直接通过 API Key + URL 获取模型列表（无需先保存）
  const apiKey = form.api_key
  if (!apiKey) {
    fetchError.value = t('settings.apiKeyRequired'); return
  }

  fetchingModels.value = true
  try {
    const { data } = await api.post('/models/fetch-available', {
      base_url: form.base_url,
      api_key: apiKey,
    })
    availableModels.value = data.models || []
    if (!availableModels.value.length) fetchError.value = t('settings.noModelsFetched')
  } catch (e) { fetchError.value = e.response?.data?.detail || t('settings.fetchFailed') }
  finally { fetchingModels.value = false }
}
</script>

<style scoped>
.settings-page { display: flex; flex-direction: column; gap: 20px; }
h1 { font-size: 28px; }
.subtitle { color: var(--muted); margin-bottom: 8px; }
.form-panel { display: flex; flex-direction: column; gap: 16px; }
h3 { font-size: 18px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 13px; color: var(--muted); }
.model-input-row { display: flex; gap: 8px; }
.model-input { flex: 1; }
.fetch-btn { white-space: nowrap; font-size: 13px; padding: 8px 14px; }
.model-picker { margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }
.model-picker-label { font-size: 12px; color: var(--accent-2); }
.model-select { width: 100%; }
.form-actions { display: flex; justify-content: space-between; align-items: center; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; }
.btn-group { display: flex; gap: 8px; }
.error { color: var(--danger); font-size: 13px; }
.models-list { display: flex; flex-direction: column; gap: 12px; }
.model-card { display: flex; flex-direction: column; gap: 10px; }
.model-card.active { border-color: var(--accent); }
.model-header { display: flex; justify-content: space-between; align-items: flex-start; }
.model-header h3 { margin: 0; font-size: 16px; display: inline; }
.default-badge { font-size: 11px; background: rgba(242,157,56,0.2); color: var(--accent); padding: 2px 8px; border-radius: 999px; margin-left: 8px; }
.model-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.model-details { display: flex; gap: 20px; font-size: 13px; color: var(--muted); flex-wrap: wrap; }
.danger-btn { background: var(--card-inner); color: var(--danger); border: 1px solid var(--border); }
.danger-btn:hover { border-color: var(--danger); }
.test-result { font-size: 13px; padding: 6px 10px; border-radius: 8px; }
.test-result.ok { background: rgba(121,194,208,0.15); color: var(--success); }
.test-result.fail { background: rgba(237,89,96,0.15); color: var(--danger); }
.empty { color: var(--muted); text-align: center; padding: 40px; }
</style>
