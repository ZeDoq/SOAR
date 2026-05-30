<template>
  <div class="step-detail-viewer">
    <div class="viewer-toolbar">
      <button class="toolbar-btn" @click="$emit('download')" title="Download">
        <i class="fas fa-download"></i> {{ $t('report.download') || 'Download' }}
      </button>
      <button class="toolbar-btn" @click="toggleRaw" title="Raw JSON">
        <i class="fas fa-code"></i> {{ showRaw ? 'FORMATTED' : 'RAW' }}
      </button>
    </div>

    <!-- Formatted View -->
    <div v-if="!showRaw" class="formatted-view">
      <div v-for="(item, i) in formattedItems" :key="i" class="detail-row">
        <span class="detail-key">{{ item.key }}</span>
        <span class="detail-value" :class="item.cls">{{ item.value }}</span>
      </div>
    </div>

    <!-- Raw JSON View -->
    <pre v-else class="raw-json">{{ rawText }}</pre>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ detail: { type: [Object, String, Array], default: null } })
defineEmits(['download'])

const showRaw = ref(false)

function toggleRaw() { showRaw.value = !showRaw.value }

const rawText = computed(() => {
  if (typeof props.detail === 'string') return props.detail
  return JSON.stringify(props.detail, null, 2)
})

const formattedItems = computed(() => {
  if (!props.detail) return []
  if (typeof props.detail === 'string') {
    return [{ key: 'INFO', value: props.detail, cls: '' }]
  }
  if (Array.isArray(props.detail)) {
    return props.detail.map((item, i) => ({
      key: `[${i}]`,
      value: typeof item === 'object' ? JSON.stringify(item) : String(item),
      cls: '',
    }))
  }
  return flattenObject(props.detail)
})

function flattenObject(obj, prefix = '') {
  const items = []
  for (const [key, val] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    if (val === null || val === undefined) {
      items.push({ key: formatKey(fullKey), value: '—', cls: 'muted' })
    } else if (typeof val === 'object' && !Array.isArray(val)) {
      items.push(...flattenObject(val, fullKey))
    } else if (Array.isArray(val)) {
      if (val.length === 0) {
        items.push({ key: formatKey(fullKey), value: '[]', cls: 'muted' })
      } else if (val.every(v => typeof v !== 'object')) {
        items.push({ key: formatKey(fullKey), value: val.join(', '), cls: '' })
      } else {
        val.forEach((v, i) => {
          if (typeof v === 'object') {
            items.push({ key: `${formatKey(fullKey)}[${i}]`, value: '', cls: 'section' })
            items.push(...flattenObject(v))
          } else {
            items.push({ key: `${formatKey(fullKey)}[${i}]`, value: String(v), cls: '' })
          }
        })
      }
    } else if (typeof val === 'boolean') {
      items.push({ key: formatKey(fullKey), value: val ? 'YES' : 'NO', cls: val ? 'positive' : 'negative' })
    } else if (typeof val === 'number') {
      items.push({ key: formatKey(fullKey), value: String(val), cls: 'number' })
    } else {
      const strVal = String(val)
      items.push({ key: formatKey(fullKey), value: strVal, cls: classifyValue(key, strVal) })
    }
  }
  return items
}

function formatKey(key) {
  return key.replace(/_/g, ' ').replace(/\./g, ' › ').toUpperCase()
}

function classifyValue(key, val) {
  const kl = key.toLowerCase()
  const vl = val.toLowerCase()
  if (kl.includes('reputation') || kl.includes('status') || kl.includes('action')) {
    if (vl.includes('malicious') || vl.includes('block')) return 'negative'
    if (vl.includes('benign') || vl.includes('monitor')) return 'positive'
    if (vl.includes('suspicious')) return 'warning'
  }
  if (kl.includes('score') || kl.includes('signal') || kl.includes('confidence')) {
    return 'number'
  }
  return ''
}
</script>

<style scoped>
.step-detail-viewer {
  margin-top: 10px;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow: hidden;
}

.viewer-toolbar {
  display: flex;
  gap: 6px;
  padding: 6px 10px;
  background: var(--card-inner);
  border-bottom: 1px solid var(--border);
}

.toolbar-btn {
  font-size: 10px; padding: 3px 8px;
  border-color: var(--border); color: var(--muted);
  display: flex; align-items: center; gap: 4px;
}
.toolbar-btn:hover { border-color: var(--neon); color: var(--neon); }

.formatted-view {
  padding: 10px 12px;
  max-height: 400px;
  overflow-y: auto;
  background: var(--card-inner);
}

.detail-row {
  display: flex;
  gap: 12px;
  padding: 4px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
  font-size: 12px;
  line-height: 1.6;
}

.detail-key {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.08em;
  min-width: 140px;
  flex-shrink: 0;
  padding-top: 1px;
}

.detail-value {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text);
  word-break: break-all;
}

.detail-value.muted { color: var(--muted); }
.detail-value.positive { color: var(--success); }
.detail-value.negative { color: var(--danger); }
.detail-value.warning { color: var(--warning); }
.detail-value.number { color: var(--neon-cyan); font-weight: 600; }
.detail-value.section {
  color: var(--neon);
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 0.08em;
  padding-top: 6px;
}

.raw-json {
  padding: 12px;
  margin: 0;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted);
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
  background: var(--card-inner);
}
</style>
