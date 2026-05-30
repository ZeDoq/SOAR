<template>
  <div>
    <h1>{{ $t('alerts.title') }}</h1>
    <div class="toolbar">
      <input v-model="search" :placeholder="$t('alerts.searchPlaceholder')" />
      <select v-model="sourceFilter">
        <option value="">{{ $t('alerts.allSources') }}</option>
        <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
    <div class="alerts-list">
      <div v-for="a in filtered" :key="a.id" class="card alert-card" @click="$router.push(`/alerts/${a.id}`)">
        <div class="alert-top">
          <span class="mono">{{ a.ip }}</span>
          <span class="tag">{{ a.source }}</span>
          <span class="time">{{ formatTime(a.observed_at) }}</span>
        </div>
        <div class="alert-desc">{{ a.description || $t('alerts.noDescription') }}</div>
        <div class="alert-tags"><span v-for="t in a.tags" :key="t" class="tag">{{ t }}</span></div>
      </div>
      <div v-if="!filtered.length" class="empty">{{ $t('alerts.notFound') }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAlertsStore } from '../stores/alerts.js'
const alertsStore = useAlertsStore()
const search = ref('')
const sourceFilter = ref('')
onMounted(() => alertsStore.fetchAlerts())
const sources = computed(() => [...new Set(alertsStore.alerts.map(a => a.source))])
const filtered = computed(() => alertsStore.alerts.filter(a => {
  const ms = !search.value || a.ip.includes(search.value) || (a.description || '').toLowerCase().includes(search.value.toLowerCase())
  const mf = !sourceFilter.value || a.source === sourceFilter.value
  return ms && mf
}))
function formatTime(t) { return t ? new Date(t).toLocaleString() : '-' }
</script>

<style scoped>
h1 { margin-bottom: 16px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 20px; }
.toolbar input { flex: 1; }
.alerts-list { display: flex; flex-direction: column; gap: 10px; }
.alert-card { padding: 16px; }
.alert-top { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
.alert-top .mono { font-size: 15px; font-weight: 600; }
.time { color: var(--muted); font-size: 12px; margin-left: auto; }
.alert-desc { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
.alert-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.empty { color: var(--muted); text-align: center; padding: 40px; }
</style>
