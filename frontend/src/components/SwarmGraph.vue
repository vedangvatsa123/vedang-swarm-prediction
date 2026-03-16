<template>
  <div class="graph-wrap" ref="wrap">
    <svg ref="svg" :viewBox="`0 0 ${width} ${height}`" preserveAspectRatio="xMidYMid meet" style="width:100%;height:100%;"></svg>
    <!-- Node detail panel -->
    <div v-if="selected" class="node-detail card">
      <div class="flex items-center justify-between mb-8">
        <span class="badge" :style="{ borderColor: typeColor(selected.type), color: typeColor(selected.type) }">{{ selected.type }}</span>
        <button class="btn btn-sm" @click="selected = null" style="padding: 2px 8px; font-size: 0.7rem;">✕</button>
      </div>
      <h3 style="font-size: 1rem; margin-bottom: 6px;">{{ selected.name }}</h3>
      <p class="text-sm text-secondary" v-if="selected.summary">{{ selected.summary }}</p>
      <p class="text-sm text-muted mt-8" v-if="selected.stance">Stance: <strong>{{ selected.stance }}</strong></p>
      <p class="text-sm text-muted" v-if="selected.posts !== undefined">Posts: <strong>{{ selected.posts }}</strong></p>
    </div>
    <!-- Legend -->
    <div class="graph-legend">
      <span class="text-sm text-muted" style="font-weight: 500;">Entity types</span>
      <div v-for="t in entityTypes" :key="t" style="display: flex; align-items: center; gap: 6px;">
        <span style="width: 8px; height: 8px; border-radius: 50%; display: inline-block;" :style="{ background: typeColor(t) }"></span>
        <span class="text-sm text-muted">{{ t }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import * as d3 from 'd3'

const TYPE_COLORS = [
  '#e5484d', '#3b82f6', '#30a46c', '#f59e0b', '#8b5cf6',
  '#ec4899', '#06b6d4', '#f97316', '#6366f1', '#14b8a6',
]

export default {
  name: 'SwarmGraph',
  props: {
    profiles: { type: Array, default: () => [] },
    posts: { type: Array, default: () => [] },
    width: { type: Number, default: 800 },
    height: { type: Number, default: 700 },
  },
  data() {
    return { selected: null }
  },
  computed: {
    entityTypes() {
      return [...new Set(this.profiles.map(p => p.entity_type || 'Person'))]
    },
  },
  mounted() {
    this.draw()
  },
  watch: {
    width() { this.draw() },
    height() { this.draw() },
    profiles() { this.draw() },
    posts() { this.draw() },
  },
  methods: {
    typeColor(type) {
      const idx = this.entityTypes.indexOf(type)
      return TYPE_COLORS[idx % TYPE_COLORS.length] || '#888'
    },
    draw() {
      const svg = d3.select(this.$refs.svg)
      svg.selectAll('*').remove()

      // Build nodes from profiles
      const nodes = this.profiles.map((p, i) => ({
        id: i,
        name: p.entity_name || p.username || `Agent ${i}`,
        type: p.entity_type || 'Person',
        stance: p.stance || 'neutral',
        summary: p.entity_summary || p.bio || '',
        posts: 0,
        radius: 6,
      }))

      // Count posts per agent
      const nameMap = {}
      nodes.forEach(n => { nameMap[n.name.toLowerCase()] = n })
      for (const post of this.posts) {
        const n = nameMap[(post.agent_name || '').toLowerCase()]
        if (n) n.posts++
      }

      // Scale radius by post count
      const maxPosts = Math.max(...nodes.map(n => n.posts), 1)
      nodes.forEach(n => {
        n.radius = 5 + (n.posts / maxPosts) * 15
      })

      // Build links from posts (reply connections and same-round connections)
      const links = []
      const roundGroups = {}
      for (const post of this.posts) {
        const rnd = post.round_num || 1
        if (!roundGroups[rnd]) roundGroups[rnd] = []
        roundGroups[rnd].push(post.agent_name)

        if (post.is_reply_to) {
          const src = nameMap[(post.agent_name || '').toLowerCase()]
          const tgt = nameMap[(post.is_reply_to || '').toLowerCase()]
          if (src && tgt && src.id !== tgt.id) {
            links.push({ source: src.id, target: tgt.id, type: 'reply' })
          }
        }
      }

      // Connect agents who posted in the same round
      for (const agents of Object.values(roundGroups)) {
        const unique = [...new Set(agents)]
        for (let i = 0; i < unique.length; i++) {
          for (let j = i + 1; j < unique.length; j++) {
            const a = nameMap[unique[i].toLowerCase()]
            const b = nameMap[unique[j].toLowerCase()]
            if (a && b) {
              const exists = links.find(l =>
                (l.source === a.id && l.target === b.id) ||
                (l.source === b.id && l.target === a.id)
              )
              if (!exists) {
                links.push({ source: a.id, target: b.id, type: 'interaction' })
              }
            }
          }
        }
      }

      const w = this.width
      const h = this.height

      const pad = 40

      // Simulation
      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id).distance(80))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(w / 2, h / 2))
        .force('collision', d3.forceCollide().radius(d => d.radius + 6))
        .force('x', d3.forceX(w / 2).strength(0.05))
        .force('y', d3.forceY(h / 2).strength(0.05))

      // Zoom
      const g = svg.append('g')
      svg.call(d3.zoom().scaleExtent([0.3, 4]).on('zoom', (e) => {
        g.attr('transform', e.transform)
      }))

      // Links
      const link = g.append('g')
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke', d => d.type === 'reply' ? '#555' : '#222')
        .attr('stroke-width', d => d.type === 'reply' ? 1.5 : 0.5)
        .attr('stroke-opacity', d => d.type === 'reply' ? 0.8 : 0.3)

      // Nodes
      const self = this
      const node = g.append('g')
        .selectAll('circle')
        .data(nodes)
        .join('circle')
        .attr('r', d => d.radius)
        .attr('fill', d => self.typeColor(d.type))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1)
        .attr('cursor', 'pointer')
        .on('click', (e, d) => {
          self.selected = d
        })
        .call(d3.drag()
          .on('start', (e, d) => {
            if (!e.active) simulation.alphaTarget(0.3).restart()
            d.fx = d.x; d.fy = d.y
          })
          .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y })
          .on('end', (e, d) => {
            if (!e.active) simulation.alphaTarget(0)
            d.fx = null; d.fy = null
          })
        )

      // Labels
      const labels = g.append('g')
        .selectAll('text')
        .data(nodes)
        .join('text')
        .text(d => d.name.length > 14 ? d.name.slice(0, 12) + '...' : d.name)
        .attr('font-size', '9px')
        .attr('fill', '#888')
        .attr('text-anchor', 'middle')
        .attr('dy', d => d.radius + 12)
        .style('pointer-events', 'none')

      simulation.on('tick', () => {
        // Keep nodes within bounds
        nodes.forEach(d => {
          d.x = Math.max(pad, Math.min(w - pad, d.x))
          d.y = Math.max(pad, Math.min(h - pad, d.y))
        })
        link
          .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
        node
          .attr('cx', d => d.x).attr('cy', d => d.y)
        labels
          .attr('x', d => d.x).attr('y', d => d.y)
      })
    },
  },
}
</script>

<style scoped>
.graph-wrap {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--bg-raised);
  overflow: hidden;
}
.graph-wrap svg {
  display: block;
  width: 100%;
  height: 100%;
}
.node-detail {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 200px;
  padding: 14px;
  background: var(--bg-surface);
  z-index: 10;
}
.graph-legend {
  position: absolute;
  bottom: 12px;
  left: 12px;
  display: flex;
  gap: 12px;
  background: rgba(0,0,0,0.7);
  padding: 6px 12px;
  border-radius: 6px;
}
</style>
