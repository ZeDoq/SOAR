<template>
  <div class="panel recent-panel">
    <div class="panel-header">
      <h3>{{ $t('dashboard.recentRuns') }}</h3>
      <RouterLink to="/runs" class="see-all">{{ $t('common.viewAll') }}</RouterLink>
    </div>
    <table v-if="runs.length">
      <thead><tr><th>#</th><th>{{ $t('table.alert') }}</th><th>{{ $t('table.status') }}</th><th>{{ $t('table.risk') }}</th><th>{{ $t('table.action') }}</th></tr></thead>
      <tbody>
        <tr v-for="r in runs" :key="r.id" @click="$router.push(`/runs/${r.id}`)">
          <td class="mono">{{ r.id }}</td><td>{{ r.alert_id }}</td>
          <td><span :class="['status', r.status]">{{ $t('status.' + r.status) }}</span></td>
          <td :class="riskColor(r.risk_score)">{{ r.risk_score ?? '-' }}</td>
          <td>{{ r.decision?.action ? $t('actions.' + r.decision.action) : '-' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">{{ $t('dashboard.noRuns') }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useRunsStore } from '../../stores/runs.js'
const runsStore = useRunsStore()
const runs = computed(() => runsStore.runs.slice(0, 5))
function riskColor(s) { if (s == null) return 'muted'; if (s >= 70) return 'risk-high'; if (s >= 40) return 'risk-mid'; return 'risk-low' }
</script>

<style scoped>
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
h3 { font-size: 16px; } .see-all { font-size: 13px; }
.empty { color: var(--muted); text-align: center; padding: 30px; }
tr { cursor: pointer; }
.risk-high { color: var(--danger); font-weight: 600; }
.risk-mid { color: var(--warning); font-weight: 600; }
.risk-low { color: var(--success); } .muted { color: var(--muted); }
</style>
