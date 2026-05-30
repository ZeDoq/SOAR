import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard', component: () => import('./views/DashboardView.vue') },
  { path: '/alerts', name: 'Alerts', component: () => import('./views/AlertsView.vue') },
  { path: '/alerts/:id', name: 'AlertDetail', component: () => import('./views/AlertDetailView.vue'), props: true },
  { path: '/runs', name: 'Runs', component: () => import('./views/RunsView.vue') },
  { path: '/runs/:id', name: 'RunDetail', component: () => import('./views/RunDetailView.vue'), props: true },
  { path: '/workbench', name: 'Workbench', component: () => import('./views/WorkbenchView.vue') },
  { path: '/graph', name: 'Graph', component: () => import('./views/GraphView.vue') },
  { path: '/simulator', name: 'Simulator', component: () => import('./views/SimulatorView.vue') },
  { path: '/settings', name: 'Settings', component: () => import('./views/SettingsView.vue') },
  { path: '/login', name: 'Login', component: () => import('./views/LoginView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
