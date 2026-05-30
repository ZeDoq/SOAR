<template>
  <div>
    <div class="sim-header">
      <h1>{{ $t('simulator.title') }}</h1>
      <button @click="runAll" :disabled="simStore.loading">{{ $t('simulator.runAll') }}</button>
    </div>
    <div class="scenarios-grid">
      <div v-for="s in simStore.scenarios" :key="s.name" class="panel scenario-card">
        <div class="scenario-type tag">{{ $t('attackType.' + s.attack_type) }}</div>
        <h3>{{ s.display_name }}</h3>
        <p class="desc">{{ s.description }}</p>
        <div class="scenario-meta">{{ $t('simulator.alerts', { count: s.alert_count }) }}</div>
        <button @click="runOne(s.name)" :disabled="simStore.loading" class="run-btn">{{ $t('simulator.runScenario') }}</button>
        <div v-if="lastResults[s.name]" class="result-box">
          <div><b>{{ $t('simulator.alertsCreated') }}</b> {{ lastResults[s.name].alerts_created?.length || 0 }}</div>
          <div v-if="lastResults[s.name].expected_outcome">
            <b>{{ $t('simulator.expected') }}</b> {{ $t('actions.' + lastResults[s.name].expected_outcome.action) }}
          </div>
        </div>
      </div>
    </div>
    <div v-if="!simStore.scenarios.length" class="empty">{{ $t('simulator.loading') }}</div>
  </div>
</template>

<script setup>
import { reactive, onMounted } from 'vue'
import { useSimulatorStore } from '../stores/simulator.js'
import { useAlertsStore } from '../stores/alerts.js'
const simStore = useSimulatorStore()
const alertsStore = useAlertsStore()
const lastResults = reactive({})
onMounted(() => simStore.fetchScenarios())
async function runOne(name) { lastResults[name] = await simStore.runScenario(name); alertsStore.fetchAlerts() }
async function runAll() { const r = await simStore.runAll(); if (r?.results) for (const [n, d] of Object.entries(r.results)) lastResults[n] = d; alertsStore.fetchAlerts() }
</script>

<style scoped>
.sim-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.scenarios-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.scenario-card { display: flex; flex-direction: column; gap: 10px; }
.scenario-type { align-self: flex-start; }
h3 { font-size: 18px; }
.desc { color: var(--muted); font-size: 13px; }
.scenario-meta { color: var(--muted); font-size: 12px; }
.run-btn { align-self: flex-start; }
.result-box { background: var(--card-inner); border-radius: 8px; padding: 10px; font-size: 13px; margin-top: 4px; }
.empty { color: var(--muted); text-align: center; padding: 60px; }
</style>
