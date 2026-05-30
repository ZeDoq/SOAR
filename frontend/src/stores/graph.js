import { defineStore } from 'pinia'
import api from '../api/client.js'

export const useGraphStore = defineStore('graph', {
  state: () => ({
    nodes: [],
    edges: [],
    stats: {},
    clusters: [],
    techniques: [],
    loading: false,
  }),
  actions: {
    async fetchGraph() {
      this.loading = true
      try {
        const { data } = await api.get('/graph')
        this.nodes = data.nodes || []
        this.edges = data.edges || []
        this.stats = data.stats || {}
      } catch { /* graph unavailable */ }
      finally { this.loading = false }
    },
    async fetchRelated(type, id) {
      try {
        const { data } = await api.get(`/graph/related/${type}/${id}`)
        return data.related || []
      } catch { return [] }
    },
    async fetchClusters() {
      try {
        const { data } = await api.get('/graph/clusters')
        this.clusters = data.clusters || []
      } catch { this.clusters = [] }
    },
    async fetchTechniques() {
      try {
        const { data } = await api.get('/graph/techniques')
        this.techniques = data.techniques || []
      } catch { this.techniques = [] }
    },
    async rebuildGraph() {
      try {
        await api.post('/graph/rebuild')
        await this.fetchGraph()
      } catch { /* ignore */ }
    },
  },
})
