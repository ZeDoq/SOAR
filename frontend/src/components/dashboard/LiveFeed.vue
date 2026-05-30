<template>
  <div class="live-feed panel">
    <div class="feed-header">
      <div class="feed-title">
        <i class="fas fa-satellite-dish feed-icon"></i>
        <span>LIVE THREAT FEED</span>
      </div>
      <div class="feed-controls">
        <span class="feed-count">{{ events.length }} events</span>
        <div class="feed-status" :class="{ active: isLive }">
          <span class="pulse-dot"></span>
          {{ isLive ? 'STREAMING' : 'PAUSED' }}
        </div>
      </div>
    </div>

    <div class="feed-body" ref="feedBody">
      <transition-group name="feed-item" tag="div" class="feed-list">
        <div v-for="event in visibleEvents" :key="event.id" class="feed-event"
          :class="event.severity" @click="$emit('select', event)">
          <div class="event-time">{{ event.time }}</div>
          <div class="event-severity-bar" :class="event.severity"></div>
          <div class="event-content">
            <div class="event-header">
              <i :class="event.icon" class="event-icon" :style="{ color: event.color }"></i>
              <span class="event-type">{{ event.type }}</span>
              <span class="event-source">{{ event.source }}</span>
            </div>
            <div class="event-message">{{ event.message }}</div>
            <div class="event-meta">
              <span class="event-ip mono">{{ event.ip }}</span>
              <span v-if="event.score" class="event-score" :class="scoreClass(event.score)">
                {{ event.score }}
              </span>
            </div>
          </div>
          <div class="event-glow" :style="{ background: event.glow }"></div>
        </div>
      </transition-group>
    </div>

    <!-- Timeline Slider -->
    <div class="feed-timeline">
      <input type="range" min="0" :max="events.length - 1" v-model="timelinePos"
        class="timeline-slider" aria-label="Timeline position">
      <div class="timeline-labels">
        <span>{{ events.length > 0 ? events[events.length - 1]?.time : '--:--' }}</span>
        <span>HISTORY</span>
        <span>{{ events.length > 0 ? events[0]?.time : '--:--' }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useAlertsStore } from '../../stores/alerts.js'

defineEmits(['select'])

const alertsStore = useAlertsStore()
const isLive = ref(true)
const timelinePos = ref(0)
const feedBody = ref(null)

const severityTypes = [
  { type: 'CRITICAL', severity: 'critical', icon: 'fas fa-skull-crossbones', color: '#ff147c', glow: 'rgba(255,20,124,0.1)' },
  { type: 'HIGH', severity: 'high', icon: 'fas fa-exclamation-triangle', color: '#ff4444', glow: 'rgba(255,68,68,0.08)' },
  { type: 'MEDIUM', severity: 'medium', icon: 'fas fa-exclamation-circle', color: '#ffab00', glow: 'rgba(255,171,0,0.08)' },
  { type: 'LOW', severity: 'low', icon: 'fas fa-info-circle', color: '#00eaff', glow: 'rgba(0,234,255,0.08)' },
  { type: 'INFO', severity: 'info', icon: 'fas fa-check-circle', color: '#a7ff00', glow: 'rgba(167,255,0,0.06)' },
]

const eventMessages = [
  'Brute force attack detected from external IP',
  'Suspicious outbound connection to C2 server',
  'Port scan activity detected on internal network',
  'Unauthorized access attempt blocked',
  'DNS tunnel exfiltration attempt detected',
  'DDoS attack mitigated by firewall',
  'Malware signature matched in network traffic',
  'Privilege escalation attempt on server',
  'Anomalous login pattern detected',
  'Data exfiltration via encrypted channel',
  'Firewall rule triggered for IP block',
  'Threat intelligence match: known malicious actor',
]

let eventId = 0
let feedTimer = null

const events = ref([])

function generateEvent() {
  const st = severityTypes[Math.floor(Math.random() * severityTypes.length)]
  const msg = eventMessages[Math.floor(Math.random() * eventMessages.length)]
  const now = new Date()
  const alert = alertsStore.alerts[Math.floor(Math.random() * Math.max(alertsStore.alerts.length, 1))]
  eventId++
  return {
    id: eventId,
    time: now.toLocaleTimeString('en-US', { hour12: false }),
    ...st,
    message: msg,
    ip: alert?.ip || `${Math.floor(Math.random()*255)}.${Math.floor(Math.random()*255)}.${Math.floor(Math.random()*255)}.${Math.floor(Math.random()*255)}`,
    source: alert?.source || 'sensor-' + String.fromCharCode(65 + Math.floor(Math.random() * 5)),
    score: Math.floor(Math.random() * 100),
  }
}

const visibleEvents = computed(() => {
  const start = Math.max(0, events.value.length - 1 - timelinePos.value)
  return events.value.slice(Math.max(0, start - 15), start + 1).reverse()
})

function scoreClass(s) {
  if (s >= 70) return 'score-critical'
  if (s >= 40) return 'score-medium'
  return 'score-low'
}

onMounted(() => {
  // Seed initial events
  for (let i = 0; i < 8; i++) {
    events.value.unshift(generateEvent())
  }
  // Live feed
  feedTimer = setInterval(() => {
    if (isLive.value && events.value.length < 200) {
      events.value.unshift(generateEvent())
    }
  }, 3000)
})

onUnmounted(() => {
  if (feedTimer) clearInterval(feedTimer)
})
</script>

<style scoped>
.live-feed {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
  overflow: hidden;
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
}

.feed-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.15em;
}

.feed-icon { color: var(--neon); font-size: 13px; }

.feed-controls { display: flex; align-items: center; gap: 12px; }

.feed-count {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--muted);
}

.feed-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 0.1em;
}

.feed-status.active { color: #a7ff00; }

.pulse-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--muted);
}

.feed-status.active .pulse-dot {
  background: #a7ff00;
  box-shadow: 0 0 8px #a7ff00;
  animation: breathe 1.5s ease-in-out infinite;
}

.feed-body {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
}

.feed-list {
  display: flex;
  flex-direction: column;
}

.feed-event {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.feed-event:hover {
  background: rgba(255, 255, 255, 0.02);
}

.event-severity-bar {
  width: 3px;
  border-radius: 2px;
  margin-right: 12px;
  flex-shrink: 0;
}

.event-severity-bar.critical { background: #ff147c; box-shadow: 0 0 6px rgba(255,20,124,0.5); }
.event-severity-bar.high { background: #ff4444; box-shadow: 0 0 6px rgba(255,68,68,0.4); }
.event-severity-bar.medium { background: #ffab00; box-shadow: 0 0 6px rgba(255,171,0,0.4); }
.event-severity-bar.low { background: #00eaff; box-shadow: 0 0 6px rgba(0,234,255,0.4); }
.event-severity-bar.info { background: #a7ff00; }

.event-time {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--muted);
  flex-shrink: 0;
  width: 60px;
  display: flex;
  align-items: center;
}

.event-content { flex: 1; min-width: 0; }

.event-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.event-icon { font-size: 11px; }
.event-type {
  font-family: var(--font-display);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.15em;
  color: var(--text-bright);
}
.event-source {
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--muted);
}

.event-message {
  font-size: 12px;
  color: var(--text);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.event-ip { font-size: 10px; color: var(--neon-cyan); }

.event-score {
  font-family: var(--font-display);
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 2px;
}

.score-critical { color: #ff147c; background: rgba(255,20,124,0.1); }
.score-medium { color: #ffab00; background: rgba(255,171,0,0.1); }
.score-low { color: #a7ff00; background: rgba(167,255,0,0.1); }

.event-glow {
  position: absolute;
  top: 0; right: 0;
  width: 80px; height: 100%;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
}

.feed-event:hover .event-glow { opacity: 1; }

/* Feed item animation */
.feed-item-enter-active {
  animation: feedSlideIn 0.4s ease;
}

@keyframes feedSlideIn {
  from { opacity: 0; transform: translateX(-20px); max-height: 0; }
  to { opacity: 1; transform: translateX(0); max-height: 100px; }
}

/* Timeline */
.feed-timeline {
  padding: 10px 16px 12px;
  border-top: 1px solid var(--border);
}

.timeline-slider {
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  outline: none;
  cursor: pointer;
}

.timeline-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px; height: 12px;
  border-radius: 2px;
  background: var(--neon);
  box-shadow: 0 0 8px var(--neon-glow);
  cursor: pointer;
}

.timeline-slider::-moz-range-thumb {
  width: 12px; height: 12px;
  border-radius: 2px;
  background: var(--neon);
  border: none;
  box-shadow: 0 0 8px var(--neon-glow);
  cursor: pointer;
}

.timeline-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--muted);
  letter-spacing: 0.05em;
}
</style>
