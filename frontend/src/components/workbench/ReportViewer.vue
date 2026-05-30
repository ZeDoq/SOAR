<template>
  <div class="report-panel ai-panel panel">
    <div class="report-header">
      <span class="report-badge">INCIDENT REPORT</span>
      <div class="report-actions">
        <button class="action-btn" @click="copyReport" :title="$t('report.copy')">
          <i :class="copied ? 'fas fa-check' : 'fas fa-copy'"></i>
          {{ copied ? $t('report.copied') : $t('report.copy') }}
        </button>
        <button class="action-btn" @click="downloadReport" :title="$t('report.download')">
          <i class="fas fa-download"></i>
          {{ $t('report.download') }}
        </button>
      </div>
    </div>
    <div class="report-content" v-html="renderedHtml"></div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  content: { type: String, default: '' },
  runId: { type: [Number, String], default: 'unknown' },
})
const copied = ref(false)

const renderedHtml = computed(() => {
  if (!props.content) return ''
  return marked(props.content, { breaks: true })
})

async function copyReport() {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {}
}

function downloadReport() {
  const blob = new Blob([props.content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `soar-report-run${props.runId}.md`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.report-panel { display: flex; flex-direction: column; gap: 12px; }
.report-header { display: flex; justify-content: space-between; align-items: center; }
.report-actions { display: flex; gap: 6px; }
.report-badge {
  font-family: var(--font-mono); font-size: 11px; font-weight: 700;
  letter-spacing: 0.15em; color: var(--neon);
  background: var(--neon-subtle); padding: 3px 10px;
  border: 1px solid var(--neon-border); border-radius: 3px;
}
.action-btn {
  font-size: 11px; padding: 4px 10px;
  border-color: var(--border); color: var(--muted);
  display: flex; align-items: center; gap: 5px;
}
.action-btn:hover { border-color: var(--neon); color: var(--neon); }
.report-content {
  font-size: 14px; line-height: 1.7;
  padding: 16px; background: var(--card-inner);
  border-radius: var(--radius); border: 1px solid var(--border);
  max-height: 600px; overflow-y: auto;
}
</style>
