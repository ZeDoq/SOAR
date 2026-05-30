<template>
  <div class="pie-chart-container">
    <div class="chart-header">
      <div class="chart-title">
        <i class="fas fa-chart-pie chart-icon"></i>
        <span>{{ $t('dashboard.actionDistribution') }}</span>
      </div>
      <div class="chart-badge">REALTIME</div>
    </div>

    <div class="chart-body">
      <!-- SVG Pie Chart -->
      <div class="pie-wrapper">
        <svg viewBox="0 0 200 200" class="pie-svg">
          <!-- Background glow -->
          <defs>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
            <filter id="glow-strong">
              <feGaussianBlur stdDeviation="6" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          <!-- Outer ring decoration -->
          <circle cx="100" cy="100" r="95" fill="none" stroke="rgba(0,234,255,0.05)" stroke-width="1"
            stroke-dasharray="4 8" class="ring-rotate"/>
          <circle cx="100" cy="100" r="88" fill="none" stroke="rgba(0,234,255,0.03)" stroke-width="0.5"/>

          <!-- Pie segments -->
          <g filter="url(#glow)">
            <path v-for="(seg, i) in segments" :key="i"
              :d="seg.path"
              :fill="seg.color"
              :stroke="seg.stroke"
              stroke-width="1"
              class="pie-segment"
              :class="{ active: hoveredSegment === i }"
              @mouseenter="hoveredSegment = i"
              @mouseleave="hoveredSegment = -1"
              :style="{ animationDelay: (i * 200) + 'ms' }"/>
          </g>

          <!-- Center circle -->
          <circle cx="100" cy="100" r="50" fill="var(--card-inner)" stroke="rgba(0,234,255,0.1)" stroke-width="1"/>
          <circle cx="100" cy="100" r="48" fill="none" stroke="rgba(0,234,255,0.05)" stroke-width="0.5"
            stroke-dasharray="2 4" class="ring-rotate-reverse"/>

          <!-- Center text -->
          <text x="100" y="92" text-anchor="middle" class="center-total">{{ total }}</text>
          <text x="100" y="110" text-anchor="middle" class="center-label">TOTAL</text>
        </svg>

        <!-- Tooltip -->
        <transition name="tooltip-fade">
          <div v-if="hoveredSegment >= 0" class="pie-tooltip" :style="tooltipStyle">
            <div class="tooltip-color" :style="{ background: segments[hoveredSegment].color }"></div>
            <div class="tooltip-content">
              <div class="tooltip-label">{{ segments[hoveredSegment].label }}</div>
              <div class="tooltip-value">{{ segments[hoveredSegment].value }}</div>
              <div class="tooltip-pct">{{ segments[hoveredSegment].pct }}%</div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Legend -->
      <div class="pie-legend">
        <div v-for="(seg, i) in segments" :key="i" class="legend-item"
          :class="{ active: hoveredSegment === i }"
          @mouseenter="hoveredSegment = i"
          @mouseleave="hoveredSegment = -1">
          <div class="legend-color" :style="{ background: seg.color, boxShadow: `0 0 6px ${seg.glow}` }"></div>
          <div class="legend-info">
            <span class="legend-label">{{ seg.label }}</span>
            <span class="legend-value">{{ seg.value }}</span>
          </div>
          <div class="legend-bar">
            <div class="legend-bar-fill" :style="{ width: seg.pct + '%', background: seg.color }"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRunsStore } from '../../stores/runs.js'

const { t } = useI18n()
const runsStore = useRunsStore()
const hoveredSegment = ref(-1)
const tooltipStyle = ref({})

const segmentDefs = [
  { key: 'block', labelKey: 'actions.block', color: '#ff147c', glow: 'rgba(255,20,124,0.4)', stroke: 'rgba(255,20,124,0.6)' },
  { key: 'monitor', labelKey: 'actions.monitor', color: '#00eaff', glow: 'rgba(0,234,255,0.4)', stroke: 'rgba(0,234,255,0.6)' },
]

const total = computed(() => runsStore.actionCounts.block + runsStore.actionCounts.monitor)

const segments = computed(() => {
  const values = [runsStore.actionCounts.block, runsStore.actionCounts.monitor]
  let startAngle = -90
  return segmentDefs.map((def, i) => {
    const value = values[i]
    const pct = total.value > 0 ? Math.round((value / total.value) * 100) : 0
    const angle = total.value > 0 ? (value / total.value) * 360 : 0
    const endAngle = startAngle + angle
    const path = describeArc(100, 100, 78, startAngle, endAngle)
    startAngle = endAngle
    return { ...def, label: t(def.labelKey), value, pct, path }
  })
})

function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = (angleDeg * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function describeArc(cx, cy, r, startAngle, endAngle) {
  if (endAngle - startAngle >= 360) {
    endAngle = startAngle + 359.99
  }
  const start = polarToCartesian(cx, cy, r, endAngle)
  const end = polarToCartesian(cx, cy, r, startAngle)
  const largeArc = endAngle - startAngle > 180 ? 1 : 0
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y} Z`
}
</script>

<style scoped>
.pie-chart-container {
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

.chart-icon { color: var(--neon-cyan); font-size: 14px; }

.chart-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 2px;
  background: rgba(0, 234, 255, 0.1);
  color: #00eaff;
  border: 1px solid rgba(0, 234, 255, 0.3);
  letter-spacing: 0.15em;
  animation: neonPulse 2s ease-in-out infinite;
}

.chart-body {
  flex: 1;
  display: flex;
  gap: 16px;
  align-items: center;
}

/* Pie SVG */
.pie-wrapper {
  position: relative;
  width: 200px;
  flex-shrink: 0;
}

.pie-svg { width: 100%; height: 100%; }

.ring-rotate {
  animation: ringRotate 20s linear infinite;
  transform-origin: center;
}

.ring-rotate-reverse {
  animation: ringRotate 15s linear infinite reverse;
  transform-origin: center;
}

@keyframes ringRotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pie-segment {
  cursor: pointer;
  transition: all 0.3s ease;
  opacity: 0.85;
}

.pie-segment:hover, .pie-segment.active {
  opacity: 1;
  filter: url(#glow-strong);
  transform: scale(1.02);
  transform-origin: center;
}

.center-total {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 800;
  fill: var(--text-bright);
}

.center-label {
  font-family: var(--font-mono);
  font-size: 9px;
  fill: var(--muted);
  letter-spacing: 0.2em;
}

/* Tooltip */
.pie-tooltip {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(5, 10, 14, 0.95);
  border: 1px solid rgba(0, 234, 255, 0.3);
  border-radius: 4px;
  padding: 8px 12px;
  display: flex;
  gap: 8px;
  align-items: center;
  backdrop-filter: blur(10px);
  z-index: 10;
  white-space: nowrap;
}

.tooltip-color {
  width: 8px; height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.tooltip-content { display: flex; gap: 8px; align-items: baseline; }
.tooltip-label { font-family: var(--font-mono); font-size: 11px; color: var(--text); }
.tooltip-value { font-family: var(--font-display); font-size: 14px; font-weight: 700; color: var(--text-bright); }
.tooltip-pct { font-family: var(--font-mono); font-size: 10px; color: var(--muted); }

.tooltip-fade-enter-active { transition: all 0.2s ease; }
.tooltip-fade-leave-active { transition: all 0.15s ease; }
.tooltip-fade-enter-from, .tooltip-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(5px); }

/* Legend */
.pie-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
}

.legend-item:hover, .legend-item.active {
  border-color: rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.legend-color {
  width: 10px; height: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 70px;
}

.legend-label {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.legend-value {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 800;
  color: var(--text-bright);
}

.legend-bar {
  flex: 1;
  height: 3px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 2px;
  overflow: hidden;
}

.legend-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s ease;
  box-shadow: 0 0 6px currentColor;
}
</style>
