<template>
  <div class="bar-chart-container">
    <div class="chart-header">
      <div class="chart-title">
        <i class="fas fa-chart-bar chart-icon"></i>
        <span>{{ $t('dashboard.riskDistribution') }}</span>
      </div>
      <div class="chart-badge">LIVE</div>
    </div>
    <div class="chart-body">
      <div class="bars-wrapper">
        <div v-for="(bar, i) in bars" :key="i" class="bar-column">
          <div class="bar-value" :class="{ active: bar.value > 0 }">{{ bar.value }}</div>
          <div class="bar-track">
            <div class="bar-fill" :style="{
              height: bar.height + '%',
              background: bar.gradient,
              boxShadow: `0 0 ${bar.value > 0 ? 12 : 0}px ${bar.glow}`,
              animationDelay: (i * 100) + 'ms'
            }">
              <div class="bar-shine"></div>
            </div>
          </div>
          <div class="bar-label">{{ bar.label }}</div>
          <div class="bar-risk-tag" :style="{ color: bar.color }">{{ bar.tag }}</div>
        </div>
      </div>
      <div class="chart-grid-lines">
        <div v-for="n in 5" :key="n" class="grid-line">
          <span class="grid-label">{{ Math.round(maxValue * (6 - n) / 5) }}</span>
        </div>
      </div>
    </div>
    <div class="chart-footer">
      <span class="footer-item"><i class="fas fa-circle" style="color: #a7ff00"></i> LOW</span>
      <span class="footer-item"><i class="fas fa-circle" style="color: #00eaff"></i> MEDIUM</span>
      <span class="footer-item"><i class="fas fa-circle" style="color: #ff147c"></i> HIGH</span>
      <span class="footer-item"><i class="fas fa-circle" style="color: #ff4444"></i> CRITICAL</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRunsStore } from '../../stores/runs.js'

const runsStore = useRunsStore()

// Simulated real-time data with smooth transitions
const liveData = ref([0, 0, 0, 0, 0])
let updateTimer = null

const barDefs = [
  { label: '0-20', tag: 'SAFE', color: '#a7ff00', gradient: 'linear-gradient(180deg, #a7ff00, #5a8a00)', glow: 'rgba(167, 255, 0, 0.4)' },
  { label: '21-40', tag: 'LOW', color: '#00eaff', gradient: 'linear-gradient(180deg, #00eaff, #007a99)', glow: 'rgba(0, 234, 255, 0.4)' },
  { label: '41-60', tag: 'MED', color: '#00eaff', gradient: 'linear-gradient(180deg, #00eaff, #005577)', glow: 'rgba(0, 234, 255, 0.3)' },
  { label: '61-80', tag: 'HIGH', color: '#ff147c', gradient: 'linear-gradient(180deg, #ff147c, #991050)', glow: 'rgba(255, 20, 124, 0.4)' },
  { label: '81-100', tag: 'CRIT', color: '#ff4444', gradient: 'linear-gradient(180deg, #ff4444, #991111)', glow: 'rgba(255, 68, 68, 0.5)' },
]

const maxValue = computed(() => Math.max(...liveData.value, 1))

const bars = computed(() =>
  barDefs.map((def, i) => ({
    ...def,
    value: liveData.value[i],
    height: maxValue.value > 0 ? (liveData.value[i] / maxValue.value) * 100 : 0,
  }))
)

function updateData() {
  // Mix real store data with simulated live fluctuation
  const base = runsStore.riskDistribution
  liveData.value = base.map((v, i) => {
    const jitter = Math.floor(Math.random() * 3) - 1
    return Math.max(0, v + jitter)
  })
}

onMounted(() => {
  updateData()
  updateTimer = setInterval(updateData, 3000)
})

onUnmounted(() => {
  if (updateTimer) clearInterval(updateTimer)
})
</script>

<style scoped>
.bar-chart-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: 100%;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-size: 12px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.15em;
}

.chart-icon { color: var(--neon); font-size: 14px; }

.chart-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 2px;
  background: rgba(167, 255, 0, 0.1);
  color: #a7ff00;
  border: 1px solid rgba(167, 255, 0, 0.3);
  letter-spacing: 0.15em;
  animation: neonPulse 2s ease-in-out infinite;
}

.chart-body {
  flex: 1;
  display: flex;
  position: relative;
  min-height: 200px;
  padding-bottom: 8px;
}

.bars-wrapper {
  flex: 1;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 0 8px;
  position: relative;
  z-index: 1;
}

.bar-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.bar-value {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  transition: all 0.5s ease;
  min-height: 18px;
}

.bar-value.active {
  color: var(--text-bright);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
}

.bar-track {
  width: 100%;
  height: 180px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 3px 3px 0 0;
  display: flex;
  align-items: flex-end;
  border: 1px solid rgba(255, 255, 255, 0.03);
  border-bottom: none;
  position: relative;
  overflow: hidden;
}

.bar-track::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 30px,
    rgba(255, 255, 255, 0.02) 30px,
    rgba(255, 255, 255, 0.02) 31px
  );
  pointer-events: none;
}

.bar-fill {
  width: 100%;
  border-radius: 3px 3px 0 0;
  transition: height 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-height: 2px;
}

.bar-shine {
  position: absolute;
  top: 0; left: -50%;
  width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  animation: barShine 3s ease-in-out infinite;
}

@keyframes barShine {
  0% { left: -50%; }
  100% { left: 150%; }
}

.bar-label {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--muted);
  letter-spacing: 0.05em;
}

.bar-risk-tag {
  font-family: var(--font-display);
  font-size: 8px;
  font-weight: 700;
  letter-spacing: 0.2em;
  opacity: 0.7;
}

.chart-grid-lines {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  pointer-events: none;
  padding: 0 4px;
}

.grid-line {
  border-bottom: 1px dashed rgba(255, 255, 255, 0.03);
  position: relative;
}

.grid-label {
  position: absolute;
  right: 100%;
  top: -6px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: rgba(255, 255, 255, 0.15);
  margin-right: 4px;
}

.chart-footer {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 0.1em;
}

.footer-item i { font-size: 6px; }
</style>
