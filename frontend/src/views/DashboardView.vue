<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dash-header">
      <div>
        <h1 class="dash-title glitch-text" data-text="SECURITY DASHBOARD">
          SECURITY DASHBOARD
        </h1>
        <p class="dash-sub">// real-time threat monitoring and analysis</p>
      </div>
      <div class="dash-controls">
        <button @click="refresh" :disabled="refreshing">
          <i class="fas fa-rotate" :class="{ 'fa-spin': refreshing }"></i>
          REFRESH
        </button>
      </div>
    </div>

    <!-- Stats Row -->
    <div class="stats-grid">
      <div class="stat-card panel" v-for="stat in stats" :key="stat.key">
        <div class="stat-icon-wrap" :style="{ color: stat.color }">
          <i :class="stat.icon"></i>
        </div>
        <div class="stat-info">
          <div class="stat-value" :style="{ color: stat.color }">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
        <div class="stat-trend" v-if="stat.trend">
          <i :class="stat.trend > 0 ? 'fas fa-arrow-up' : 'fas fa-arrow-down'"
            :style="{ color: stat.trend > 0 ? '#ff147c' : '#a7ff00' }"></i>
        </div>
        <div class="stat-bg-icon">
          <i :class="stat.icon"></i>
        </div>
      </div>
    </div>

    <!-- Main Charts + Live Feed Grid -->
    <div class="main-grid">
      <!-- Left: Bar Chart (60%) -->
      <div class="panel chart-panel">
        <RiskChart />
      </div>

      <!-- Right Column (40%) -->
      <div class="right-column">
        <!-- Pie Chart -->
        <div class="panel chart-panel">
          <ActionChart />
        </div>

        <!-- Summary Stats -->
        <div class="panel summary-panel">
          <div class="summary-header">
            <i class="fas fa-shield-halved"></i>
            <span>SYSTEM STATUS</span>
          </div>
          <div class="summary-items">
            <div class="summary-item">
              <span class="summary-label">Threat Level</span>
              <span class="summary-value" :class="threatLevel.class">{{ threatLevel.label }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Avg Risk Score</span>
              <span class="summary-value">{{ runsStore.averageRiskScore }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Active Sources</span>
              <span class="summary-value mono">{{ activeSources }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">AI Engine</span>
              <span class="summary-value engine-status">
                <span class="engine-dot"></span> READY
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Live Feed -->
    <LiveFeed />

    <!-- Tables -->
    <div class="tables-grid">
      <RecentAlerts />
      <RecentRuns />
    </div>

    <!-- Terminal Log -->
    <div class="panel terminal-panel">
      <div class="terminal-header">
        <div class="terminal-dots">
          <span class="dot" style="background:#ff5f56"></span>
          <span class="dot" style="background:#ffbd2e"></span>
          <span class="dot" style="background:#27c93f"></span>
        </div>
        <span class="terminal-title">SOAR://system-log</span>
      </div>
      <div class="terminal-body">
        <div v-for="(log, i) in terminalLogs" :key="i" class="t-line">
          <span class="t-time">{{ log.time }}</span>
          <span class="t-level" :class="log.level">[{{ log.level }}]</span>
          <span class="t-msg">{{ log.msg }}</span>
        </div>
        <div class="t-input">
          <span class="t-prompt">soar@soc:~$</span>
          <span class="cursor-blink"></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import RiskChart from '../components/dashboard/RiskChart.vue'
import ActionChart from '../components/dashboard/ActionChart.vue'
import LiveFeed from '../components/dashboard/LiveFeed.vue'
import RecentAlerts from '../components/dashboard/RecentAlerts.vue'
import RecentRuns from '../components/dashboard/RecentRuns.vue'
import { useAlertsStore } from '../stores/alerts.js'
import { useRunsStore } from '../stores/runs.js'

const { t } = useI18n()
const alertsStore = useAlertsStore()
const runsStore = useRunsStore()
const refreshing = ref(false)

const stats = computed(() => [
  { key: 'alerts', label: t('dashboard.totalAlerts'), value: alertsStore.alertCount, icon: 'fas fa-bell', color: '#00eaff', trend: null },
  { key: 'runs', label: t('dashboard.totalRuns'), value: runsStore.runCount, icon: 'fas fa-play', color: '#a7ff00', trend: null },
  { key: 'ai', label: t('ai.analyses'), value: runsStore.aiAnalysisCount, icon: 'fas fa-brain', color: '#d500f9', trend: null },
  { key: 'blocked', label: t('dashboard.blocked'), value: runsStore.actionCounts.block, icon: 'fas fa-shield-halved', color: '#ff147c', trend: null },
])

const threatLevel = computed(() => {
  const avg = runsStore.averageRiskScore
  if (avg >= 70) return { label: 'CRITICAL', class: 'tl-critical' }
  if (avg >= 40) return { label: 'ELEVATED', class: 'tl-elevated' }
  return { label: 'NORMAL', class: 'tl-normal' }
})

const activeSources = computed(() => {
  return '3/3'
})

const terminalLogs = computed(() => [
  { time: '00:00:01', level: 'ok', msg: 'SOAR Security Operations Center initialized' },
  { time: '00:00:02', level: 'ok', msg: 'Threat intelligence feeds: CONNECTED' },
  { time: '00:00:03', level: 'ok', msg: 'AI analysis engine: STANDBY' },
  { time: '00:00:04', level: 'info', msg: `Database: ${alertsStore.alertCount} alerts, ${runsStore.runCount} runs indexed` },
  { time: '00:00:05', level: 'ok', msg: 'Firewall integration: ACTIVE' },
  { time: '00:00:06', level: 'info', msg: 'All subsystems operational. Entering monitoring mode...' },
])

async function refresh() {
  refreshing.value = true
  await Promise.all([alertsStore.fetchAlerts(), runsStore.fetchRuns()])
  setTimeout(() => { refreshing.value = false }, 500)
}

onMounted(() => {
  alertsStore.fetchAlerts()
  runsStore.fetchRuns()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeIn 0.5s ease;
}

/* Header */
.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.dash-title {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  color: var(--neon);
  letter-spacing: 0.12em;
  text-shadow: 0 0 20px var(--neon-glow);
  animation: textGlow 3s ease-in-out infinite;
}

.dash-sub {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted);
  margin-top: 4px;
}

.refresh-btn i.fa-spin { animation: spin 0.8s linear infinite; }

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}

.stat-card {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  overflow: hidden;
}

.stat-icon-wrap {
  width: 40px; height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid currentColor;
  font-size: 16px;
  opacity: 0.8;
  flex-shrink: 0;
}

.stat-info { flex: 1; }

.stat-value {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
}

.stat-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-top: 4px;
}

.stat-bg-icon {
  position: absolute;
  right: 12px; top: 50%;
  transform: translateY(-50%);
  font-size: 48px;
  opacity: 0.03;
  color: var(--text);
}

.stat-trend { font-size: 12px; }

/* Main Grid: 60/40 split */
.main-grid {
  display: grid;
  grid-template-columns: 60fr 40fr;
  gap: 16px;
}

.chart-panel {
  min-height: 320px;
  display: flex;
  flex-direction: column;
}

.right-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Summary Panel */
.summary-panel { padding: 14px; }

.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-bottom: 14px;
}

.summary-header i { color: var(--neon); font-size: 12px; }

.summary-items { display: flex; flex-direction: column; gap: 10px; }

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
}

.summary-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--muted);
}

.summary-value {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-bright);
}

.tl-critical { color: #ff147c; text-shadow: 0 0 8px rgba(255,20,124,0.4); }
.tl-elevated { color: #ffab00; }
.tl-normal { color: #a7ff00; text-shadow: 0 0 8px rgba(167,255,0,0.3); }

.engine-status {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #a7ff00;
  font-size: 11px;
}

.engine-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #a7ff00;
  box-shadow: 0 0 6px #a7ff00;
  animation: breathe 2s ease-in-out infinite;
}

/* Tables */
.tables-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* Terminal */
.terminal-panel {
  padding: 0;
  border-color: var(--border-bright);
  overflow: hidden;
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 14px;
  background: var(--card-inner);
  border-bottom: 1px solid var(--border);
}

.terminal-dots { display: flex; gap: 6px; }
.dot { width: 8px; height: 8px; border-radius: 50%; }

.terminal-title {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.12em;
}

.terminal-body {
  padding: 14px;
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.8;
  max-height: 180px;
  overflow-y: auto;
}

.t-line { display: flex; gap: 10px; }
.t-time { color: var(--muted); flex-shrink: 0; width: 60px; }
.t-level { flex-shrink: 0; width: 50px; font-weight: 600; font-size: 10px; }
.t-level.ok { color: #a7ff00; }
.t-level.info { color: #00eaff; }
.t-level.warn { color: #ffab00; }
.t-level.err { color: #ff147c; }
.t-msg { color: var(--text); }
.t-input { display: flex; gap: 8px; margin-top: 4px; }
.t-prompt { color: var(--neon); font-weight: 600; }

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .main-grid { grid-template-columns: 1fr; }
  .tables-grid { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: 1fr; }
  .dash-header { flex-direction: column; gap: 12px; align-items: flex-start; }
  .dash-title { font-size: 16px; }
}
</style>
