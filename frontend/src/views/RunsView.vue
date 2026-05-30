<template>
  <div>
    <h1>{{ $t('runs.title') }}</h1>
    <table>
      <thead>
        <tr><th>{{ $t('table.id') }}</th><th>{{ $t('table.alert') }}</th><th>{{ $t('table.status') }}</th><th>{{ $t('table.risk') }}</th><th>{{ $t('table.action') }}</th><th>{{ $t('table.template') }}</th><th>{{ $t('table.time') }}</th></tr>
      </thead>
      <tbody>
        <tr v-for="r in runsStore.runs" :key="r.id" @click="$router.push(`/runs/${r.id}`)">
          <td class="mono">{{ r.id }}</td><td>{{ r.alert_id }}</td>
          <td><span :class="['status', r.status]">{{ $t('status.' + r.status) }}</span></td>
          <td :class="riskClass(r.risk_score)">{{ r.risk_score ?? '-' }}</td>
          <td>{{ r.decision?.action ? $t('actions.' + r.decision.action) : '-' }}</td>
          <td class="muted">{{ r.decision?.template ? $t('template.' + r.decision.template, r.decision.template) : '-' }}</td>
          <td class="muted">{{ formatTime(r.started_at) }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="!runsStore.runs.length" class="empty">{{ $t('runs.noRuns') }}</div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRunsStore } from '../stores/runs.js'
const runsStore = useRunsStore()
onMounted(() => runsStore.fetchRuns())
function formatTime(t) { return t ? new Date(t).toLocaleString() : '-' }
function riskClass(s) { if (s == null) return 'muted'; if (s >= 70) return 'risk-high'; if (s >= 40) return 'risk-mid'; return 'risk-low' }
</script>

<style scoped>
h1 { margin-bottom: 16px; }
tr { cursor: pointer; }
.risk-high { color: var(--danger); font-weight: 600; }
.risk-mid { color: var(--warning); font-weight: 600; }
.risk-low { color: var(--success); }
.muted { color: var(--muted); font-size: 13px; }
.empty { color: var(--muted); text-align: center; padding: 40px; }
</style>
