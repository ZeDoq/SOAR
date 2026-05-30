<template>
  <!-- Boot Sequence Overlay -->
  <transition name="boot">
    <div v-if="booting" class="boot-overlay" role="status" aria-label="System loading">
      <div class="boot-text">
        <div v-for="(line, i) in bootLines" :key="i"
          class="boot-line" :class="line.cls"
          :style="{ animationDelay: (i * 120) + 'ms' }">
          {{ line.text }}
        </div>
      </div>
    </div>
  </transition>

  <!-- Matrix Rain Background -->
  <canvas ref="matrixCanvas" class="matrix-canvas" aria-hidden="true"></canvas>

  <div class="app-layout" :data-theme="theme">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }" role="navigation" aria-label="Main navigation">
      <div class="sidebar-header" @click="sidebarCollapsed = !sidebarCollapsed">
        <div class="logo-section">
          <span class="logo-bracket">[</span>
          <span class="logo-text glitch-text" data-text="SOAR">SOAR</span>
          <span class="logo-bracket">]</span>
        </div>
        <div v-if="!sidebarCollapsed" class="logo-sub">SECURITY OPS<span class="cursor-blink"></span></div>
      </div>

      <nav class="sidebar-nav">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item"
          :aria-label="item.label" :title="item.label">
          <i :class="item.icon" class="nav-icon-fa"></i>
          <span v-if="!sidebarCollapsed" class="nav-label">{{ $t(item.i18n) }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <!-- Theme Toggle -->
        <button class="theme-toggle" @click="toggleTheme" :aria-label="$t('settings.themeToggle')">
          <i :class="theme === 'green' ? 'fas fa-sun' : 'fas fa-moon'"></i>
          <span v-if="!sidebarCollapsed">{{ theme === 'green' ? 'BLUE' : 'GREEN' }}</span>
        </button>

        <!-- Language Toggle -->
        <button class="theme-toggle" @click="toggleLocale" aria-label="Switch language">
          <i class="fas fa-language"></i>
          <span v-if="!sidebarCollapsed">{{ locale === 'zh-CN' ? 'EN' : '中文' }}</span>
        </button>

        <!-- Auth -->
        <template v-if="authStore.isAuthenticated">
          <div class="user-indicator">
            <span class="user-dot"></span>
            <span v-if="!sidebarCollapsed" class="user-name">{{ authStore.user?.username }}</span>
          </div>
          <button class="theme-toggle logout" @click="handleLogout">
            <i class="fas fa-right-from-bracket"></i>
            <span v-if="!sidebarCollapsed">{{ $t('nav.logout') }}</span>
          </button>
        </template>
        <RouterLink v-else to="/login" class="nav-item" aria-label="Login">
          <i class="fas fa-right-to-bracket nav-icon-fa"></i>
          <span v-if="!sidebarCollapsed" class="nav-label">{{ $t('nav.login') }}</span>
        </RouterLink>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- Top Bar -->
      <header class="topbar">
        <div class="topbar-left">
          <button class="hamburger" @click="sidebarCollapsed = !sidebarCollapsed" aria-label="Toggle sidebar">
            <i class="fas fa-bars"></i>
          </button>
          <div class="breadcrumb">
            <span class="breadcrumb-prefix">&gt;&gt;</span>
            <span class="breadcrumb-path">{{ currentRoute }}</span>
            <span class="cursor-blink"></span>
          </div>
        </div>
        <div class="topbar-right">
          <span class="system-status">
            <span class="status-dot" :class="{ active: true }"></span>
            <span class="status-text">ONLINE</span>
          </span>
          <span class="topbar-clock">{{ clock }}</span>
        </div>
      </header>

      <!-- Page Content with Transition -->
      <div class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="page-transition" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from './stores/auth.js'

const { locale } = useI18n()
const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

// State
const theme = ref(localStorage.getItem('soar_theme') || 'green')
const sidebarCollapsed = ref(true)
const booting = ref(true)
const clock = ref('')
const matrixCanvas = ref(null)

const navItems = [
  { to: '/dashboard', icon: 'fas fa-chart-line', label: 'Dashboard', i18n: 'nav.dashboard' },
  { to: '/alerts', icon: 'fas fa-bell', label: 'Alerts', i18n: 'nav.alerts' },
  { to: '/runs', icon: 'fas fa-play', label: 'Runs', i18n: 'nav.runs' },
  { to: '/workbench', icon: 'fas fa-magnifying-glass', label: 'Workbench', i18n: 'nav.workbench' },
  { to: '/graph', icon: 'fas fa-diagram-project', label: 'Graph', i18n: 'nav.graph' },
  { to: '/simulator', icon: 'fas fa-crosshairs', label: 'Simulator', i18n: 'nav.simulator' },
  { to: '/settings', icon: 'fas fa-gear', label: 'Settings', i18n: 'nav.settings' },
]

const bootLines = [
  { text: '> BIOS POST... OK', cls: 'ok' },
  { text: '> Loading SOAR kernel v6.0...', cls: '' },
  { text: '> Initializing threat detection modules...', cls: '' },
  { text: '> Connecting to intelligence feeds...', cls: 'ok' },
  { text: '> AI analysis engine: READY', cls: 'ok' },
  { text: '> Firewall integration: ACTIVE', cls: 'ok' },
  { text: '> Knowledge graph: LOADED', cls: 'ok' },
  { text: '> All systems operational.', cls: 'warn' },
  { text: '> Welcome to SOAR Security Operations Center.', cls: 'ok' },
]

const currentRoute = computed(() => route.name || 'Dashboard')

// Clock
let clockTimer = null
function updateClock() {
  const now = new Date()
  clock.value = now.toLocaleTimeString('en-US', { hour12: false })
}

// Matrix Rain
function initMatrixRain() {
  const canvas = matrixCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight

  const chars = 'アイウエオカキクケコ01サシスセソタチツテト23456789ABCDEF'
  const fontSize = 14
  const columns = Math.floor(canvas.width / fontSize)
  const drops = new Array(columns).fill(1)

  function draw() {
    ctx.fillStyle = 'rgba(5, 10, 14, 0.05)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.fillStyle = theme.value === 'green' ? '#00ff41' : '#2979ff'
    ctx.font = `${fontSize}px "Fira Code"`

    for (let i = 0; i < drops.length; i++) {
      const text = chars[Math.floor(Math.random() * chars.length)]
      ctx.fillText(text, i * fontSize, drops[i] * fontSize)
      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
        drops[i] = 0
      }
      drops[i]++
    }
  }

  setInterval(draw, 50)

  window.addEventListener('resize', () => {
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
  })
}

// Boot sequence
function runBootSequence() {
  setTimeout(() => {
    booting.value = false
  }, 2000)
}

// Theme
function toggleTheme() {
  theme.value = theme.value === 'green' ? 'blue' : 'green'
  localStorage.setItem('soar_theme', theme.value)
  document.documentElement.setAttribute('data-theme', theme.value)
}

// Locale
function toggleLocale() {
  const next = locale.value === 'zh-CN' ? 'en-US' : 'zh-CN'
  locale.value = next
  localStorage.setItem('soar_locale', next)
}

// Logout
function handleLogout() {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  document.documentElement.setAttribute('data-theme', theme.value)
  runBootSequence()
  initMatrixRain()
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<style scoped>
/* Boot transition */
.boot-leave-active { transition: opacity 0.8s ease; }
.boot-leave-to { opacity: 0; }

/* Page transition */
.page-transition-enter-active {
  animation: pageIn 0.4s ease;
}
.page-transition-leave-active {
  animation: pageOut 0.2s ease;
}

@keyframes pageIn {
  from { opacity: 0; transform: translateY(10px); filter: blur(2px); }
  to { opacity: 1; transform: translateY(0); filter: blur(0); }
}

@keyframes pageOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

/* Layout */
.app-layout {
  display: flex;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

/* Sidebar */
.sidebar {
  width: var(--sidebar-width);
  background: rgba(5, 10, 14, 0.95);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0;
  height: 100vh;
  z-index: 100;
  transition: width 0.3s ease;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.sidebar:not(.collapsed) {
  width: var(--sidebar-expanded);
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  text-align: center;
  position: relative;
}

.sidebar-header::after {
  content: '';
  position: absolute;
  bottom: 0; left: 10%; right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--neon), transparent);
  opacity: 0.3;
}

.logo-section {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.logo-bracket { color: var(--muted); font-weight: 300; }
.logo-text { color: var(--neon); letter-spacing: 0.2em; }
.logo-sub {
  font-family: var(--font-mono);
  font-size: 8px;
  color: var(--muted);
  letter-spacing: 0.4em;
  margin-top: 4px;
}

.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 8px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius);
  color: var(--muted);
  font-size: 12px;
  font-family: var(--font-mono);
  transition: all 0.2s;
  border: 1px solid transparent;
  white-space: nowrap;
  text-decoration: none;
}

.nav-item:hover {
  color: var(--neon);
  background: var(--neon-subtle);
  border-color: var(--neon-border);
  text-shadow: 0 0 8px var(--neon-glow);
}

.nav-item.router-link-active {
  color: var(--neon);
  background: rgba(0, 255, 65, 0.08);
  border-color: var(--neon-border);
  box-shadow: inset 3px 0 0 var(--neon);
}

.nav-icon-fa {
  width: 20px;
  text-align: center;
  font-size: 14px;
  flex-shrink: 0;
}

.nav-label { font-size: 12px; }

.sidebar-footer {
  border-top: 1px solid var(--border);
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.theme-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: transparent;
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.theme-toggle:hover {
  color: var(--neon-cyan);
  border-color: var(--neon-cyan);
}

.theme-toggle.logout:hover {
  color: var(--neon-red);
  border-color: var(--neon-red);
}

.user-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  font-family: var(--font-mono);
  font-size: 11px;
}

.user-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--neon);
  box-shadow: 0 0 8px var(--neon);
  animation: breathe 3s ease-in-out infinite;
  flex-shrink: 0;
}

.user-name {
  color: var(--neon);
  font-weight: 600;
  text-transform: uppercase;
}

/* Main Content */
.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  transition: margin-left 0.3s ease;
}

.main-content.sidebar-collapsed {
  margin-left: var(--sidebar-width);
}

.sidebar:not(.collapsed) ~ .main-content {
  margin-left: var(--sidebar-expanded);
}

/* Top Bar */
.topbar {
  height: var(--topbar-height);
  background: rgba(5, 10, 14, 0.9);
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 50;
  backdrop-filter: blur(10px);
}

.topbar::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--neon), transparent);
  opacity: 0.15;
}

.topbar-left { display: flex; align-items: center; gap: 16px; }

.hamburger {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--muted);
  width: 32px; height: 32px;
  display: none;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
}

.breadcrumb {
  font-family: var(--font-mono);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.breadcrumb-prefix { color: var(--neon); opacity: 0.5; }
.breadcrumb-path { color: var(--text-bright); text-transform: uppercase; letter-spacing: 0.1em; }

.topbar-right { display: flex; align-items: center; gap: 20px; }

.system-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.1em;
}

.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--muted);
}

.status-dot.active {
  background: var(--neon);
  box-shadow: 0 0 8px var(--neon);
  animation: breathe 2s ease-in-out infinite;
}

.status-text { color: var(--neon); }

.topbar-clock {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--muted);
  letter-spacing: 0.1em;
}

.page-content {
  padding: 24px;
}

/* Mobile */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    width: var(--sidebar-expanded) !important;
    z-index: 200;
  }

  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }

  .main-content {
    margin-left: 0 !important;
  }

  .hamburger { display: flex; }

  .page-content { padding: 16px; }
}

/* Tablet */
@media (min-width: 769px) and (max-width: 1024px) {
  .sidebar { width: var(--sidebar-expanded); }
  .main-content { margin-left: var(--sidebar-expanded); }
}
</style>
