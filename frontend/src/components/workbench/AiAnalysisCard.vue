<template>
  <div class="ai-card ai-panel panel breathe">
    <div class="ai-header">
      <span class="ai-badge">AI ANALYSIS</span>
      <div class="ai-header-right">
        <span v-if="data.confidence" class="ai-version">{{ (data.confidence * 100).toFixed(0) }}%</span>
        <button class="download-btn" @click="downloadAnalysis" title="Download">
          <i class="fas fa-download"></i>
        </button>
      </div>
    </div>

    <!-- Threat Level -->
    <div class="threat-section">
      <span :class="['threat-badge', data.threat_level || 'unknown']">
        {{ $t('threatLevel.' + (data.threat_level || 'unknown')) }}
      </span>
      <div class="confidence-section">
        <div class="confidence-label">
          {{ $t('ai.confidence') }}: {{ ((data.confidence || 0) * 100).toFixed(0) }}%
        </div>
        <div class="confidence-bar">
          <div :class="['confidence-fill', confidenceClass]" :style="{ width: ((data.confidence || 0) * 100) + '%' }"></div>
        </div>
      </div>
    </div>

    <!-- ATT&CK Technique -->
    <div v-if="data.attack_technique" class="info-row">
      <span class="info-label">{{ $t('ai.technique') }}</span>
      <span class="tag attack-tag">{{ data.attack_technique }}</span>
      <span v-if="data.attack_tactic" class="tag">{{ data.attack_tactic }}</span>
    </div>

    <!-- Impact Assessment -->
    <div v-if="data.impact_assessment" class="info-block">
      <div class="info-label">{{ $t('ai.impact') }}</div>
      <div class="info-value">{{ data.impact_assessment }}</div>
    </div>

    <!-- Recommended Actions -->
    <div v-if="data.recommended_actions && data.recommended_actions.length" class="info-block">
      <div class="info-label">{{ $t('ai.actions') }}</div>
      <ul class="action-list">
        <li v-for="(action, i) in data.recommended_actions" :key="i" class="action-item">
          <span class="action-marker">▸</span> {{ action }}
        </li>
      </ul>
    </div>

    <!-- Reasoning (collapsible) -->
    <div v-if="data.reasoning" class="info-block">
      <div class="info-label toggle-label" @click="showReasoning = !showReasoning">
        {{ $t('ai.reasoning') }} <span class="toggle-arrow">{{ showReasoning ? '▼' : '▶' }}</span>
      </div>
      <div v-if="showReasoning" class="reasoning-text">{{ data.reasoning }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ data: { type: Object, default: () => ({}) } })
const showReasoning = ref(false)

const confidenceClass = computed(() => {
  const c = (props.data.confidence || 0) * 100
  if (c >= 70) return 'high'
  if (c >= 40) return 'mid'
  return 'low'
})

function downloadAnalysis() {
  const d = props.data
  const lines = [
    '=== SOAR AI Analysis Report ===',
    '',
    `Threat Level: ${(d.threat_level || 'N/A').toUpperCase()}`,
    `Confidence: ${((d.confidence || 0) * 100).toFixed(0)}%`,
    '',
  ]
  if (d.attack_technique) lines.push(`Attack Technique: ${d.attack_technique}`)
  if (d.attack_tactic) lines.push(`Attack Tactic: ${d.attack_tactic}`)
  if (d.impact_assessment) lines.push(`\nImpact Assessment:\n${d.impact_assessment}`)
  if (d.recommended_actions?.length) {
    lines.push('\nRecommended Actions:')
    d.recommended_actions.forEach((a, i) => lines.push(`  ${i + 1}. ${a}`))
  }
  if (d.additional_intel_needed?.length) {
    lines.push('\nAdditional Intel Needed:')
    d.additional_intel_needed.forEach((a, i) => lines.push(`  ${i + 1}. ${a}`))
  }
  if (d.reasoning) lines.push(`\nAI Reasoning:\n${d.reasoning}`)

  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ai-analysis-${d.threat_level || 'unknown'}.txt`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.ai-card { display: flex; flex-direction: column; gap: 14px; }
.ai-header { display: flex; justify-content: space-between; align-items: center; }
.ai-badge {
  font-family: var(--font-mono); font-size: 11px; font-weight: 700;
  letter-spacing: 0.15em; color: var(--neon-cyan);
  background: rgba(0, 229, 255, 0.08); padding: 3px 10px;
  border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 3px;
}
.ai-header-right { display: flex; align-items: center; gap: 8px; }
.ai-version {
  font-family: var(--font-mono); font-size: 11px;
  color: var(--muted);
}
.download-btn {
  padding: 3px 8px; font-size: 11px;
  border-color: var(--border); color: var(--muted);
}
.download-btn:hover { border-color: var(--neon-cyan); color: var(--neon-cyan); }
.threat-section { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.confidence-section { flex: 1; min-width: 150px; }
.confidence-label {
  font-family: var(--font-mono); font-size: 12px;
  color: var(--muted); margin-bottom: 4px;
}
.info-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.info-label {
  font-family: var(--font-mono); font-size: 11px;
  color: var(--muted); text-transform: uppercase;
  letter-spacing: 0.1em; min-width: 80px;
}
.info-block { display: flex; flex-direction: column; gap: 6px; }
.info-value { font-size: 13px; line-height: 1.6; }
.attack-tag { background: rgba(248, 81, 73, 0.1); color: var(--danger); border-color: rgba(248, 81, 73, 0.3); }
.action-list { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.action-item {
  font-size: 13px; display: flex; align-items: flex-start; gap: 8px;
  padding: 6px 10px; background: rgba(0, 255, 65, 0.03);
  border-radius: var(--radius); border: 1px solid rgba(0, 255, 65, 0.08);
}
.action-marker { color: var(--terminal-green); font-weight: 700; flex-shrink: 0; }
.toggle-label { cursor: pointer; user-select: none; display: flex; align-items: center; gap: 6px; }
.toggle-label:hover { color: var(--terminal-cyan); }
.toggle-arrow { font-size: 10px; }
.reasoning-text {
  font-size: 13px; line-height: 1.7; color: var(--text);
  padding: 12px; background: var(--card-inner);
  border-radius: var(--radius); border: 1px solid var(--border);
  white-space: pre-wrap;
}
</style>
