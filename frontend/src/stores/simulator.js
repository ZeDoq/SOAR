import { defineStore } from 'pinia'
import api from '../api/client.js'

export const useSimulatorStore = defineStore('simulator', {
  state: () => ({
    scenarios: [],
    lastResult: null,
    loading: false,
  }),
  actions: {
    async fetchScenarios() {
      this.loading = true
      try {
        const { data } = await api.get('/simulator/scenarios')
        this.scenarios = data.scenarios || []
      } finally { this.loading = false }
    },
    async runScenario(name, mode = 'adaptive') {
      this.loading = true
      try {
        const { data } = await api.post(`/simulator/run/${name}?mode=${mode}`)
        this.lastResult = data
        return data
      } finally { this.loading = false }
    },
    async runAll(mode = 'adaptive') {
      this.loading = true
      try {
        const { data } = await api.post(`/simulator/run-all?mode=${mode}`)
        this.lastResult = data
        return data
      } finally { this.loading = false }
    },
  },
})
