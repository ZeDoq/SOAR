<template>
  <div class="detail-page">
    <div class="detail-header">
      <h1>{{ $t('alerts.investigation') }}</h1>
      <div class="actions">
        <select v-model="mode">
          <option value="classic">{{ $t('alerts.classic') }}</option>
          <option value="adaptive">{{ $t('alerts.adaptive') }}</option>
        </select>
        <button @click="runPlaybook" :disabled="running" class="run-btn">
          <i :class="running ? 'fas fa-spinner fa-spin' : 'fas fa-play'"></i>
          {{ running ? $t('alerts.running') : $t('alerts.runPlaybook') }}
        </button>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="error" class="error-banner">
      <i class="fas fa-exclamation-triangle"></i> {{ error }}
      <button class="error-close" @click="error = ''">×</button>
    </div>

    <!-- Run success feedback -->
    <div v-if="lastRunId" class="success-banner">
      <i class="fas fa-check-circle"></i>
      {{ $t('alerts.runStarted') || 'Playbook started' }} — Run #{{ lastRunId }}
      <RouterLink :to="`/runs/${lastRunId}`" class="banner-link">
        {{ $t('alerts.viewDetail') }} →
      </RouterLink>
    </div>

    <div class="workbench-grid" v-if="alert">
      <!-- Alert Info -->
      <div class="panel">
        <h3><i class="fas fa-bell" style="color: var(--neon); margin-right: 6px; font-size: 13px"></i> {{ $t('alerts.alertInfo') }}</h3>
        <div class="info-row"><span class="info-label">{{ $t('alerts.ip') }}</span> <span class="mono ip-value">{{ alert.ip }}</span></div>
        <div class="info-row"><span class="info-label">{{ $t('alerts.source') }}</span> {{ alert.source }}</div>
        <div class="info-row"><span class="info-label">{{ $t('alerts.description') }}</span> {{ alert.description }}</div>
        <div class="info-row"><span class="info-label">{{ $t('alerts.time') }}</span> {{ formatTime(alert.observed_at) }}</div>
        <div class="info-row"><span class="info-label">{{ $t('alerts.tags') }}</span>
          <span v-for="t in alert.tags" :key="t" class="tag">{{ t }}</span>
          <span v-if="!alert.tags?.length" class="muted-text">—</span>
        </div>
      </div>

      <!-- Run Status (always visible, shows current state) -->
      <div class="panel run-panel" :class="{ 'has-run': !!currentRunData }">
        <h3>
          <i class="fas fa-play" style="color: var(--neon-cyan); margin-right: 6px; font-size: 13px"></i>
          {{ $t('alerts.latestRun') }}
          <span v-if="currentRunData" :class="['status', currentRunData.status]" style="margin-left: 8px">
            {{ $t('status.' + currentRunData.status) }}
          </span>
          <span v-else class="no-run-badge">{{ $t('alerts.noRunYet') || 'No runs yet' }}</span>
        </h3>

        <template v-if="currentRunData">
          <div class="info-row">
            <span class="info-label">{{ $t('runs.riskScore') }}</span>
            <span :class="riskClass(currentRunData.risk_score)" class="risk-value">
              {{ currentRunData.risk_score ?? '-' }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">{{ $t('table.action') }}</span>
            {{ currentRunData.decision?.action ? $t('actions.' + currentRunData.decision.action) : '-' }}
          </div>
          <div class="steps-mini">
            <div v-for="step in currentStepsData" :key="step.id" class="step-pill" :class="step.status">
              {{ $t('stepsShort.' + step.name) }}
            </div>
          </div>
          <RouterLink :to="`/runs/${currentRunData.id}`" class="see-detail">
            <i class="fas fa-arrow-right"></i> {{ $t('alerts.viewDetail') }}
          </RouterLink>
        </template>

        <div v-else class="no-run-hint">
          {{ $t('alerts.clickRun') || 'Click "Run Playbook" to execute security response' }}
        </div>
      </div>

      <!-- Knowledge Base -->
      <div class="panel">
        <h3><i class="fas fa-book" style="color: var(--neon-amber); margin-right: 6px; font-size: 13px"></i> {{ $t('alerts.kbMatches') }}</h3>
        <div v-if="kbResults.length">
          <div v-for="r in kbResults" :key="r.id" class="kb-item">
            <span class="mono">[{{ r.id }}]</span> {{ r.name }} <span class="tag">{{ r.tactic }}</span>
          </div>
        </div>
        <div v-else class="empty">{{ $t('alerts.noMatches') }}</div>
      </div>

      <!-- Related Graph -->
      <div class="panel">
        <h3><i class="fas fa-diagram-project" style="color: var(--neon-purple, #d500f9); margin-right: 6px; font-size: 13px"></i> {{ $t('alerts.relatedGraph') }}</h3>
        <div v-if="graphRelated.length" class="related-list">
          <div v-for="r in graphRelated" :key="r.node_id" class="related-item">
            <span class="tag">{{ r.node_type }}</span> {{ r.node_id }}
          </div>
        </div>
        <div v-else class="empty">{{ $t('alerts.noGraphData') }}</div>
      </div>
    </div>
    <div v-else-if="alertsStore.loading" class="loading"><div class="spinner"></div></div>
    <div v-else class="empty-state">
      <i class="fas fa-exclamation-circle" style="font-size: 24px; margin-bottom: 12px; display: block;"></i>
      {{ $t('alerts.notFound') }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useAlertsStore } from '../stores/alerts.js'
import { useRunsStore } from '../stores/runs.js'
import api from '../api/client.js'

// Accept alertId as prop for embedding in WorkbenchView
const props = defineProps({
  alertId: { type: [Number, String], default: null },
})

const route = useRoute()
const alertsStore = useAlertsStore()
const runsStore = useRunsStore()
const mode = ref('adaptive')
const running = ref(false)
const error = ref('')
const lastRunId = ref(null)
const kbResults = ref([])
const graphRelated = ref([])
const alert = ref(null)

// Compute the effective alert ID (prop or route param)
const effectiveId = computed(() => props.alertId || route.params.id)

// Track run data locally so we always have it even if store is overwritten
const currentRunData = ref(null)
const currentStepsData = ref([])

// Watch for store changes (from polling)
watch(() => runsStore.currentRun, (newRun) => {
  if (newRun) {
    currentRunData.value = { ...newRun }
    currentStepsData.value = [...runsStore.currentSteps]
  }
}, { deep: true })

onMounted(async () => {
  const id = effectiveId.value
  if (!id) return

  // Load alert
  await alertsStore.fetchAlert(id)
  alert.value = alertsStore.currentAlert

  if (!alert.value) return

  // Load KB and graph
  loadKB(alert.value)
  loadRelated(id)

  // Load runs list first, then find existing run
  await runsStore.fetchRuns()
  const existingRun = runsStore.runs.find(r => r.alert_id === parseInt(id))
  if (existingRun) {
    await runsStore.fetchRunDetail(existingRun.id)
    currentRunData.value = { ...runsStore.currentRun }
    currentStepsData.value = [...runsStore.currentSteps]
    // Start polling if still running
    if (existingRun.status === 'running' || existingRun.status === 'queued') {
      runsStore.startPolling(existingRun.id)
    }
  }
})

onUnmounted(() => runsStore.stopPolling())

async function loadKB(a) {
  try {
    const { data } = await api.get('/knowledge/search', {
      params: { q: `${a.description} ${(a.tags || []).join(' ')}` }
    })
    kbResults.value = data.results || []
  } catch { kbResults.value = [] }
}

async function loadRelated(id) {
  try {
    const { data } = await api.get(`/graph/related/alert/${id}`)
    graphRelated.value = data.related || []
  } catch { graphRelated.value = [] }
}

async function runPlaybook() {
  const id = effectiveId.value
  if (!id) return

  running.value = true
  error.value = ''
  lastRunId.value = null

  try {
    const run = await runsStore.startRun(parseInt(id), mode.value)
    lastRunId.value = run.id

    // Immediately fetch the run detail to show the "queued" state
    await runsStore.fetchRunDetail(run.id)
    currentRunData.value = { ...runsStore.currentRun }
    currentStepsData.value = [...runsStore.currentSteps]

    // Start polling for progress
    runsStore.startPolling(run.id)

    // Also refresh the runs list
    await runsStore.fetchRuns()
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || 'Failed to start playbook'
  } finally {
    running.value = false
  }
}

function riskClass(s) {
  if (s >= 70) return 'risk-high'
  if (s >= 40) return 'risk-mid'
  return 'risk-low'
}

function formatTime(t) {
  if (!t) return '—'
  return new Date(t).toLocaleString()
}
</script>

<style scoped>
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.actions { display: flex; gap: 10px; }

.run-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(255, 23, 68, 0.08);
  border: 1px solid rgba(255, 23, 68, 0.3);
  border-radius: var(--radius);
  color: var(--danger);
  font-size: 13px;
  margin-bottom: 12px;
}

.error-close {
  margin-left: auto;
  background: transparent;
  border: none;
  color: var(--danger);
  font-size: 16px;
  cursor: pointer;
  padding: 0 4px;
}

.success-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(0, 230, 118, 0.06);
  border: 1px solid rgba(0, 230, 118, 0.2);
  border-radius: var(--radius);
  color: var(--success);
  font-size: 13px;
  margin-bottom: 12px;
}

.banner-link {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 12px;
}

.workbench-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

h3 {
  margin-bottom: 12px;
  font-size: 14px;
  display: flex;
  align-items: center;
}

.info-row {
  margin-bottom: 8px;
  font-size: 13px;
  display: flex;
  gap: 8px;
}

.info-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  min-width: 60px;
  padding-top: 2px;
}

.ip-value {
  color: var(--neon-cyan);
  font-weight: 600;
  font-size: 14px;
}

.muted-text { color: var(--muted); }

.run-panel.has-run {
  border-color: var(--neon-border);
}

.no-run-badge {
  font-size: 10px;
  color: var(--muted);
  font-weight: normal;
  font-family: var(--font-mono);
  margin-left: 8px;
}

.risk-value {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 800;
}

.steps-mini {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0;
}

.step-pill {
  font-size: 10px;
  padding: 2px 10px;
  border-radius: 2px;
  font-family: var(--font-mono);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.step-pill.completed {
  background: rgba(0, 230, 118, 0.1);
  color: var(--success);
  border: 1px solid rgba(0, 230, 118, 0.2);
}

.step-pill.skipped {
  background: rgba(74, 94, 111, 0.1);
  color: var(--muted);
  border: 1px solid rgba(74, 94, 111, 0.2);
}

.step-pill.running {
  background: rgba(255, 179, 0, 0.1);
  color: var(--warning);
  border: 1px solid rgba(255, 179, 0, 0.2);
  animation: neonPulse 2s ease-in-out infinite;
}

.step-pill.failed {
  background: rgba(255, 23, 68, 0.1);
  color: var(--danger);
  border: 1px solid rgba(255, 23, 68, 0.2);
}

.step-pill.queued {
  background: rgba(74, 94, 111, 0.1);
  color: var(--muted);
  border: 1px solid rgba(74, 94, 111, 0.15);
}

.see-detail {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  font-family: var(--font-mono);
}

.no-run-hint {
  font-size: 12px;
  color: var(--muted);
  font-style: italic;
  padding: 8px 0;
}

.kb-item { margin-bottom: 8px; font-size: 13px; }
.related-item { margin-bottom: 6px; font-size: 13px; }

.risk-high { color: var(--danger); font-weight: 600; }
.risk-mid { color: var(--warning); font-weight: 600; }
.risk-low { color: var(--success); }

.loading { display: flex; justify-content: center; padding: 60px; }
.empty { color: var(--muted); font-size: 12px; }
.empty-state { color: var(--muted); text-align: center; padding: 60px; font-size: 14px; }

@media (max-width: 900px) {
  .workbench-grid { grid-template-columns: 1fr; }
}
</style>
