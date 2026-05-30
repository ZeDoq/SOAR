<template>
  <div class="panel recent-panel">
    <div class="panel-header">
      <h3>{{ $t('dashboard.recentAlerts') }}</h3>
      <RouterLink to="/alerts" class="see-all">{{ $t('common.viewAll') }}</RouterLink>
    </div>
    <table v-if="alerts.length">
      <thead><tr><th>{{ $t('table.ip') }}</th><th>{{ $t('table.source') }}</th><th>{{ $t('table.description') }}</th><th>{{ $t('table.time') }}</th></tr></thead>
      <tbody>
        <tr v-for="a in alerts" :key="a.id" @click="$router.push(`/alerts/${a.id}`)">
          <td class="mono">{{ a.ip }}</td><td>{{ a.source }}</td>
          <td>{{ (a.description || '').substring(0, 40) }}...</td>
          <td class="muted">{{ formatTime(a.observed_at) }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">{{ $t('dashboard.noAlerts') }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAlertsStore } from '../../stores/alerts.js'
const alertsStore = useAlertsStore()
const alerts = computed(() => alertsStore.recentAlerts)
function formatTime(t) { return t ? new Date(t).toLocaleString() : '-' }
</script>

<style scoped>
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
h3 { font-size: 16px; } .see-all { font-size: 13px; }
.empty { color: var(--muted); text-align: center; padding: 30px; }
tr { cursor: pointer; } .muted { color: var(--muted); font-size: 12px; }
</style>
