<template>
  <div class="stat-card" :style="{ borderColor: color }">
    <div class="stat-value" :style="{ color }">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
    <div class="stat-icon">{{ icon }}</div>
  </div>
</template>

<script setup>
defineProps({ value: [Number, String], label: String, icon: String, color: { type: String, default: 'var(--accent)' } })
</script>

<style scoped>
.stat-card {
  background: var(--card);
  border-radius: var(--radius-lg);
  padding: 20px;
  border: 1px solid var(--border);
  border-left: 4px solid;
  position: relative;
  overflow: hidden;
}
.stat-value { font-size: 36px; font-weight: 700; font-family: "Consolas", monospace; }
.stat-label { color: var(--muted); font-size: 14px; margin-top: 4px; }
.stat-icon { position: absolute; top: 16px; right: 16px; font-size: 28px; opacity: 0.3; }
</style>
