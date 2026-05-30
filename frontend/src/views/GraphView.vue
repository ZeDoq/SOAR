<template>
  <div class="graph-page">
    <div class="graph-header">
      <h1>{{ $t('graph.title') }}</h1>
      <button @click="rebuildGraph" :disabled="rebuilding">
        {{ rebuilding ? $t('graph.rebuilding') : $t('graph.rebuildGraph') }}
      </button>
    </div>
    <div class="graph-layout">
      <div class="panel graph-canvas-wrap">
        <div ref="canvasRef" class="graph-canvas"></div>
        <div v-if="!graphStore.nodes.length" class="empty-overlay">
          <div class="empty">{{ $t('graph.noGraphData') }}</div>
        </div>
      </div>
      <div class="graph-sidebar">
        <div class="panel">
          <h3>{{ $t('graph.stats') }}</h3>
          <div class="info-row">{{ $t('graph.nodes') }} <b>{{ graphStore.stats.node_count || 0 }}</b></div>
          <div class="info-row">{{ $t('graph.edges') }} <b>{{ graphStore.stats.edge_count || 0 }}</b></div>
        </div>
        <div class="panel">
          <h3>{{ $t('graph.techniques') }}</h3>
          <div v-for="t in graphStore.techniques.slice(0, 8)" :key="t.technique_id" class="tech-item">
            <span class="mono">[{{ t.technique_id }}]</span> {{ t.name }}
            <span class="count">{{ t.count }}</span>
          </div>
          <div v-if="!graphStore.techniques.length" class="empty">{{ $t('graph.noData') }}</div>
        </div>
        <div class="panel">
          <h3>{{ $t('graph.clusters') }}</h3>
          <div v-for="(c, i) in graphStore.clusters" :key="i" class="cluster-item">
            <b>{{ $t('graph.cluster', { n: i + 1 }) }}</b> {{ c.join(', ') }}
          </div>
          <div v-if="!graphStore.clusters.length" class="empty">{{ $t('graph.noClusters') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { useGraphStore } from '../stores/graph.js'
const graphStore = useGraphStore()
const canvasRef = ref(null)
const rebuilding = ref(false)
let network = null
const NODE_COLORS = { ip: '#79c2d0', alert: '#f29d38', technique: '#4a6fa5', risk_level: '#ed5960', domain: '#9aa6b2' }
const NODE_SHAPES = { ip: 'dot', alert: 'diamond', technique: 'square', risk_level: 'triangle', domain: 'star' }

onMounted(async () => { await Promise.all([graphStore.fetchGraph(), graphStore.fetchTechniques(), graphStore.fetchClusters()]); await nextTick(); renderGraph() })
watch(() => graphStore.nodes.length, () => { nextTick(renderGraph) })

function renderGraph() {
  if (!canvasRef.value || !graphStore.nodes.length) return
  import('vis-network/standalone').then(({ Network, DataSet }) => {
    const nodes = new DataSet(graphStore.nodes.map(n => ({
      id: n.id, label: n.ip || n.name || n.domain || n.level || n.id,
      color: NODE_COLORS[n.node_type] || '#9aa6b2', shape: NODE_SHAPES[n.node_type] || 'dot',
      size: n.node_type === 'alert' ? 20 : 15, font: { color: '#e8ecef', size: 11 },
    })))
    const edges = new DataSet(graphStore.edges.map((e, i) => ({
      id: i, from: e.source, to: e.target, color: { color: 'rgba(255,255,255,0.15)', highlight: '#f29d38' }, arrows: 'to',
    })))
    network = new Network(canvasRef.value, { nodes, edges }, {
      physics: { barnesHut: { gravitationalConstant: -2000, springLength: 120 } },
      interaction: { hover: true, tooltipDelay: 200 },
    })
  })
}

async function rebuildGraph() {
  rebuilding.value = true
  await graphStore.rebuildGraph()
  await graphStore.fetchTechniques()
  await graphStore.fetchClusters()
  rebuilding.value = false
}
</script>

<style scoped>
.graph-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.graph-layout { display: grid; grid-template-columns: 1fr 280px; gap: 16px; height: calc(100vh - 120px); }
.graph-canvas-wrap { position: relative; padding: 0; overflow: hidden; }
.graph-canvas { width: 100%; height: 100%; }
.empty-overlay { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }
.graph-sidebar { display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
h3 { margin-bottom: 10px; font-size: 15px; }
.info-row { margin-bottom: 6px; font-size: 14px; }
.tech-item { margin-bottom: 6px; font-size: 13px; }
.count { float: right; color: var(--accent); font-weight: 600; }
.cluster-item { margin-bottom: 8px; font-size: 13px; word-break: break-all; }
.empty { color: var(--muted); font-size: 13px; }
</style>
