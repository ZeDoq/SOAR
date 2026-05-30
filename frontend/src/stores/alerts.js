import { defineStore } from 'pinia'
import api from '../api/client.js'

export const useAlertsStore = defineStore('alerts', {
  state: () => ({
    alerts: [],
    currentAlert: null,
    loading: false,
  }),
  getters: {
    alertCount: (state) => state.alerts.length,
    recentAlerts: (state) => state.alerts.slice(0, 5),
    alertsBySource: (state) => {
      const groups = {}
      for (const a of state.alerts) {
        groups[a.source] = groups[a.source] || []
        groups[a.source].push(a)
      }
      return groups
    },
  },
  actions: {
    async fetchAlerts() {
      this.loading = true
      try {
        const { data } = await api.get('/alerts')
        this.alerts = data.alerts || []
      } finally {
        this.loading = false
      }
    },
    async fetchAlert(id) {
      this.loading = true
      try {
        const { data } = await api.get(`/alerts/${id}`)
        this.currentAlert = data.alert
      } finally {
        this.loading = false
      }
    },
  },
})
