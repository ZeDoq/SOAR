import { defineStore } from 'pinia'
import api from '../api/client.js'

export const useRunsStore = defineStore('runs', {
  state: () => ({
    runs: [],
    currentRun: null,
    currentSteps: [],
    loading: false,
    polling: null,
  }),
  getters: {
    runCount: (state) => state.runs.length,
    completedRuns: (state) => state.runs.filter((r) => r.status === 'completed'),
    failedRuns: (state) => state.runs.filter((r) => r.status === 'failed'),
    averageRiskScore: (state) => {
      const completed = state.runs.filter((r) => r.risk_score != null)
      if (!completed.length) return 0
      return Math.round(completed.reduce((s, r) => s + r.risk_score, 0) / completed.length)
    },
    actionCounts: (state) => {
      let block = 0, monitor = 0
      for (const r of state.runs) {
        const action = r.decision?.action || 'monitor'
        if (action === 'block') block++
        else monitor++
      }
      return { block, monitor }
    },
    riskDistribution: (state) => {
      const buckets = [0, 0, 0, 0, 0]
      for (const r of state.runs) {
        const s = r.risk_score ?? 0
        if (s <= 20) buckets[0]++
        else if (s <= 40) buckets[1]++
        else if (s <= 60) buckets[2]++
        else if (s <= 80) buckets[3]++
        else buckets[4]++
      }
      return buckets
    },
    aiAnalysisCount: (state) => {
      return state.runs.filter(r => r.status === 'completed').length
    },
    threatLevelDistribution: (state) => {
      const dist = { malicious: 0, suspicious: 0, benign: 0, false_positive: 0 }
      for (const r of state.runs) {
        if (r.risk_score == null) continue
        if (r.risk_score >= 70) dist.malicious++
        else if (r.risk_score >= 40) dist.suspicious++
        else dist.benign++
      }
      return dist
    },
  },
  actions: {
    async fetchRuns() {
      this.loading = true
      try {
        const { data } = await api.get('/runs')
        this.runs = data.runs || []
      } finally {
        this.loading = false
      }
    },
    async fetchRunDetail(id) {
      this.loading = true
      try {
        const { data } = await api.get(`/runs/${id}`)
        this.currentRun = data.run
        this.currentSteps = data.steps || []
      } finally {
        this.loading = false
      }
    },
    async startRun(alertId, mode = 'classic') {
      const { data } = await api.post('/runs', { alert_id: alertId, mode })
      return data.run
    },
    startPolling(runId) {
      this.stopPolling()
      this.polling = setInterval(async () => {
        await this.fetchRunDetail(runId)
        if (this.currentRun?.status === 'completed' || this.currentRun?.status === 'failed') {
          this.stopPolling()
        }
      }, 2000)
    },
    stopPolling() {
      if (this.polling) {
        clearInterval(this.polling)
        this.polling = null
      }
    },
  },
})
