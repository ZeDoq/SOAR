<template>
  <div class="run-detail" v-if="runsStore.currentRun">
    <div class="detail-header">
      <h1>{{ $t('runs.runNumber', { id: runsStore.currentRun.id }) }}</h1>
      <div class="header-actions">
        <span :class="['status', runsStore.currentRun.status]">{{ $t('status.' + runsStore.currentRun.status) }}</span>
        <button class="download-all-btn" @click="downloadAllSteps" title="Download all steps">
          <i class="fas fa-download"></i> ALL
        </button>
      </div>
    </div>

    <div class="detail-meta">
      <div class="meta-item"><span class="meta-label">{{ $t('alerts.ip') }}</span> <span class="mono">{{ runsStore.currentRun.alert_id }}</span></div>
      <div class="meta-item"><span class="meta-label">{{ $t('runs.riskScore') }}</span> <span :class="riskClass(runsStore.currentRun.risk_score)">{{ runsStore.currentRun.risk_score ?? '-' }}</span></div>
      <div class="meta-item"><span class="meta-label">{{ $t('table.action') }}</span> {{ runsStore.currentRun.decision?.action ? $t('actions.' + runsStore.currentRun.decision.action) : '-' }}</div>
      <div v-if="runsStore.currentRun.decision?.template" class="meta-item"><span class="meta-label">{{ $t('table.template') }}</span> {{ $t('template.' + runsStore.currentRun.decision.template, runsStore.currentRun.decision.template) }}</div>
    </div>

    <h2>{{ $t('runs.steps') }}</h2>

    <div class="timeline">
      <div v-for="step in runsStore.currentSteps" :key="step.id" class="step-item">
        <div class="step-line" :class="step.status"></div>
        <div class="step-content card" @click="toggleStep(step.id)">
          <div class="step-header">
            <span class="step-name">
              <span v-if="step.name === 'ai_analysis'" class="step-ai-badge">AI</span>
              <i :class="stepIcon(step.name)" class="step-icon"></i>
              {{ $t('steps.' + step.name) }}
            </span>
            <div class="step-right">
              <span :class="['status', step.status]">{{ $t('status.' + step.status) }}</span>
              <button v-if="step.detail && expanded[step.id]" class="step-dl-btn"
                @click.stop="downloadStep(step)" title="Download">
                <i class="fas fa-download"></i>
              </button>
            </div>
          </div>

          <!-- AI Analysis step -->
          <div v-if="expanded[step.id] && step.name === 'ai_analysis' && step.detail && step.status === 'completed'">
            <AiAnalysisCard :data="step.detail" />
          </div>

          <!-- Report step -->
          <div v-else-if="expanded[step.id] && step.name === 'report_generation' && step.detail?.report">
            <ReportViewer :content="step.detail.report" :runId="runsStore.currentRun.id" />
          </div>

          <!-- Other steps: formatted viewer -->
          <StepDetailViewer v-else-if="expanded[step.id] && step.detail"
            :detail="step.detail" @download="downloadStep(step)" />

          <!-- Skipped steps -->
          <div v-else-if="expanded[step.id] && step.detail" class="skipped-reason">
            {{ step.detail.reason || $t('status.skipped') }}
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="runsStore.loading" class="loading"><div class="spinner"></div></div>
  <div v-else class="empty">{{ $t('runs.notFound') }}</div>
</template>

<script setup>
import { reactive, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useRunsStore } from '../stores/runs.js'
import AiAnalysisCard from '../components/workbench/AiAnalysisCard.vue'
import ReportViewer from '../components/workbench/ReportViewer.vue'
import StepDetailViewer from '../components/workbench/StepDetailViewer.vue'

const route = useRoute()
const runsStore = useRunsStore()
const expanded = reactive({})

onMounted(() => { runsStore.fetchRunDetail(route.params.id); runsStore.startPolling(route.params.id) })
onUnmounted(() => runsStore.stopPolling())

function toggleStep(id) { expanded[id] = !expanded[id] }

function riskClass(s) { if (s >= 70) return 'risk-high'; if (s >= 40) return 'risk-mid'; return 'risk-low' }

function stepIcon(name) {
  const icons = {
    threat_intel: 'fas fa-satellite-dish',
    risk_assessment: 'fas fa-scale-balanced',
    ai_analysis: 'fas fa-brain',
    network_recon: 'fas fa-network-wired',
    firewall_block: 'fas fa-shield-halved',
    notify_email: 'fas fa-envelope',
    notify_slack: 'fas fa-hashtag',
    report_generation: 'fas fa-file-lines',
  }
  return icons[name] || 'fas fa-circle-dot'
}

function downloadStep(step) {
  let content = ''
  let filename = `step-${step.name}.json`

  if (step.name === 'report_generation' && step.detail?.report) {
    content = step.detail.report
    filename = `step-${step.name}-run${runsStore.currentRun.id}.md`
  } else if (step.name === 'ai_analysis' && typeof step.detail === 'object') {
    const d = step.detail
    const lines = [
      '=== AI Analysis Step Detail ===',
      `Step: ${step.name}`,
      `Status: ${step.status}`,
      '',
      `Threat Level: ${(d.threat_level || 'N/A').toUpperCase()}`,
      `Confidence: ${((d.confidence || 0) * 100).toFixed(0)}%`,
    ]
    if (d.attack_technique) lines.push(`Attack Technique: ${d.attack_technique}`)
    if (d.attack_tactic) lines.push(`Attack Tactic: ${d.attack_tactic}`)
    if (d.impact_assessment) lines.push(`\nImpact:\n${d.impact_assessment}`)
    if (d.recommended_actions?.length) {
      lines.push('\nRecommended Actions:')
      d.recommended_actions.forEach((a, i) => lines.push(`  ${i + 1}. ${a}`))
    }
    if (d.reasoning) lines.push(`\nReasoning:\n${d.reasoning}`)
    content = lines.join('\n')
    filename = `step-${step.name}-run${runsStore.currentRun.id}.txt`
  } else {
    content = JSON.stringify(step.detail, null, 2)
    filename = `step-${step.name}-run${runsStore.currentRun.id}.json`
  }

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function downloadAllSteps() {
  const lines = [`=== SOAR Playbook Run #${runsStore.currentRun.id} ===`, '']
  lines.push(`Status: ${runsStore.currentRun.status}`)
  lines.push(`Risk Score: ${runsStore.currentRun.risk_score ?? '-'}`)
  lines.push(`Action: ${runsStore.currentRun.decision?.action || '-'}`)
  lines.push('')

  for (const step of runsStore.currentSteps) {
    lines.push(`--- Step: ${step.name} [${step.status}] ---`)
    if (step.detail) {
      if (typeof step.detail === 'string') {
        lines.push(step.detail)
      } else {
        // Format as clean key-value pairs
        const flat = flattenForText(step.detail)
        lines.push(...flat)
      }
    } else {
      lines.push('(no detail)')
    }
    lines.push('')
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `soar-run-${runsStore.currentRun.id}-full.txt`
  a.click()
  URL.revokeObjectURL(url)
}

function flattenForText(obj, indent = 0) {
  const lines = []
  const pad = '  '.repeat(indent)
  for (const [key, val] of Object.entries(obj)) {
    const label = key.replace(/_/g, ' ')
    if (val === null || val === undefined) {
      lines.push(`${pad}${label}: —`)
    } else if (typeof val === 'object' && !Array.isArray(val)) {
      lines.push(`${pad}${label}:`)
      lines.push(...flattenForText(val, indent + 1))
    } else if (Array.isArray(val)) {
      if (val.length === 0) {
        lines.push(`${pad}${label}: []`)
      } else if (val.every(v => typeof v !== 'object')) {
        lines.push(`${pad}${label}: ${val.join(', ')}`)
      } else {
        lines.push(`${pad}${label}:`)
        val.forEach((v, i) => {
          if (typeof v === 'object') {
            lines.push(`${pad}  [${i}]:`)
            lines.push(...flattenForText(v, indent + 2))
          } else {
            lines.push(`${pad}  [${i}]: ${v}`)
          }
        })
      }
    } else {
      lines.push(`${pad}${label}: ${val}`)
    }
  }
  return lines
}
</script>

<style scoped>
.detail-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.header-actions { display: flex; align-items: center; gap: 10px; }
.download-all-btn {
  font-size: 11px; padding: 4px 12px;
  border-color: var(--border); color: var(--muted);
  display: flex; align-items: center; gap: 5px;
}
.download-all-btn:hover { border-color: var(--neon); color: var(--neon); }

.detail-meta {
  display: flex; flex-wrap: wrap; gap: 12px 24px;
  margin-bottom: 24px; font-size: 14px;
  padding: 14px; background: var(--card);
  border-radius: var(--radius); border: 1px solid var(--border);
}

.meta-item { display: flex; align-items: center; gap: 6px; }
.meta-label { font-family: var(--font-mono); font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; }

h2 { margin-bottom: 16px; font-size: 18px; }

.timeline { display: flex; flex-direction: column; gap: 12px; }
.step-item { display: flex; gap: 12px; }
.step-line { width: 4px; border-radius: 2px; min-height: 40px; flex-shrink: 0; }
.step-line.completed { background: var(--success); box-shadow: 0 0 6px rgba(0, 230, 118, 0.3); }
.step-line.failed { background: var(--danger); box-shadow: 0 0 6px rgba(255, 23, 68, 0.3); }
.step-line.running { background: var(--warning); box-shadow: 0 0 6px rgba(255, 179, 0, 0.3); animation: neonPulse 2s ease-in-out infinite; }
.step-line.skipped { background: var(--muted); }

.step-content { flex: 1; cursor: pointer; }
.step-header { display: flex; justify-content: space-between; align-items: center; }
.step-name { font-weight: 600; display: flex; align-items: center; gap: 8px; font-size: 13px; }
.step-icon { font-size: 12px; color: var(--neon); opacity: 0.6; }
.step-right { display: flex; align-items: center; gap: 8px; }

.step-ai-badge {
  font-size: 9px; font-weight: 700; padding: 1px 6px;
  border-radius: 3px; letter-spacing: 0.1em;
  background: rgba(0, 229, 255, 0.1); color: var(--neon-cyan);
  border: 1px solid rgba(0, 229, 255, 0.3);
}

.step-dl-btn {
  padding: 3px 8px; font-size: 10px;
  border-color: var(--border); color: var(--muted);
}
.step-dl-btn:hover { border-color: var(--neon); color: var(--neon); }

.skipped-reason {
  margin-top: 8px; font-size: 12px; color: var(--muted);
  font-style: italic; padding: 8px;
}

.risk-high { color: var(--danger); font-weight: 600; font-family: var(--font-mono); }
.risk-mid { color: var(--warning); font-weight: 600; font-family: var(--font-mono); }
.risk-low { color: var(--success); font-family: var(--font-mono); }

.loading { display: flex; justify-content: center; padding: 60px; }
.empty { color: var(--muted); text-align: center; padding: 60px; }
</style>
