<template>
  <div class="workbench">
    <h1>{{ $t('workbench.title') }}</h1>
    <div class="wb-layout">
      <div class="panel alert-list-panel">
        <h3><i class="fas fa-list" style="color: var(--neon); margin-right: 6px; font-size: 12px"></i> {{ $t('nav.alerts') }}</h3>
        <input v-model="search" :placeholder="$t('workbench.filterPlaceholder')" class="filter-input" />
        <div class="alert-scroll">
          <div v-for="a in filtered" :key="a.id" class="card mini-alert"
            :class="{ selected: selectedId === a.id }" @click="selectAlert(a)">
            <span class="mono">{{ a.ip }}</span>
            <span class="tag">{{ a.source }}</span>
          </div>
          <div v-if="!filtered.length" class="no-alerts">{{ $t('alerts.notFound') }}</div>
        </div>
      </div>
      <div class="detail-area">
        <AlertDetailView v-if="selectedId" :key="selectedId" :alertId="selectedId" />
        <div v-else class="empty-state">
          <i class="fas fa-magnifying-glass-chart" style="font-size: 32px; margin-bottom: 12px; display: block; opacity: 0.3;"></i>
          {{ $t('workbench.selectAlert') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAlertsStore } from '../stores/alerts.js'
import AlertDetailView from './AlertDetailView.vue'

const alertsStore = useAlertsStore()
const search = ref('')
const selectedId = ref(null)

onMounted(() => alertsStore.fetchAlerts())

const filtered = computed(() => {
  if (!search.value) return alertsStore.alerts
  const q = search.value.toLowerCase()
  return alertsStore.alerts.filter(a =>
    a.ip.includes(q) || (a.description || '').toLowerCase().includes(q)
  )
})

function selectAlert(a) {
  selectedId.value = a.id
}
</script>

<style scoped>
.workbench { height: calc(100vh - 56px); }
h1 { margin-bottom: 16px; }
.wb-layout { display: grid; grid-template-columns: 280px 1fr; gap: 16px; height: calc(100% - 50px); }
.alert-list-panel { overflow: hidden; display: flex; flex-direction: column; }
.alert-list-panel h3 { margin-bottom: 12px; font-size: 13px; }
.filter-input { margin-bottom: 12px; width: 100%; }
.alert-scroll { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; }
.mini-alert { padding: 10px; display: flex; align-items: center; gap: 8px; }
.mini-alert.selected { border-color: var(--neon); background: var(--neon-subtle); box-shadow: 0 0 10px var(--neon-subtle); }
.no-alerts { color: var(--muted); font-size: 12px; text-align: center; padding: 20px; }
.detail-area { overflow-y: auto; }
.empty-state { color: var(--muted); text-align: center; padding: 80px; font-size: 14px; }

@media (max-width: 768px) {
  .wb-layout { grid-template-columns: 1fr; height: auto; }
}
</style>
