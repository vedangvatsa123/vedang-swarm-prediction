<template>
  <div>
    <!-- Processing -->
    <div v-if="!done && !failed" class="page-center">
      <h2>Running prediction</h2>

      <div class="card mt-24">
        <div class="flex items-center justify-between mb-8">
          <div class="flex items-center gap-8">
            <span class="pulse-dot"></span>
            <span style="font-weight: 500;">{{ phaseLabel }}</span>
          </div>
          <span class="mono text-sm text-muted">{{ elapsed }}</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
        </div>
        <p class="text-sm text-muted mt-8" style="min-height: 1.4em;">
          <transition name="fade" mode="out-in">
            <span :key="activeHint">{{ activeHint }}</span>
          </transition>
        </p>
      </div>

      <div class="mt-24" style="display: flex; flex-direction: column; gap: 10px;">
        <div v-for="step in phases" :key="step.key" class="flex items-center gap-12">
          <span class="text-sm" :style="{ color: phaseIndex(step.key) <= phaseIndex(currentPhase) ? 'var(--text)' : 'var(--text-muted)' }">
            {{ phaseIndex(step.key) < phaseIndex(currentPhase) ? '✓' : phaseIndex(step.key) === phaseIndex(currentPhase) ? '·' : ' ' }}
          </span>
          <span :class="phaseIndex(step.key) <= phaseIndex(currentPhase) ? '' : 'text-muted'" class="text-sm">
            {{ step.label }}
          </span>
        </div>
      </div>
    </div>

    <!-- Failed -->
    <div v-if="failed" class="page-center">
      <h2>Something went wrong</h2>
      <p class="text-secondary mt-8">{{ message }}</p>
      <button class="btn mt-16" @click="$router.push('/')">Start over</button>
    </div>

    <!-- Results: full-width split layout -->
    <div v-if="done" class="results-layout">
      <!-- Top bar -->
      <div class="results-header">
        <div class="flex items-center gap-16">
          <router-link to="/" style="color: var(--text-muted); font-size: 0.875rem;">← Back</router-link>
          <div class="view-switcher">
            <button v-for="m in ['graph', 'split', 'report']" :key="m"
              class="switch-btn" :class="{ active: viewMode === m }" @click="viewMode = m">
              {{ { graph: 'Graph', split: 'Split', report: 'Report' }[m] }}
            </button>
          </div>
        </div>
        <div class="flex items-center gap-16">
          <div class="flex items-center gap-8">
            <span class="stat-pill">{{ stats.entities }} entities</span>
            <span class="stat-pill">{{ stats.agents }} agents</span>
            <span class="stat-pill">{{ stats.posts }} posts</span>
          </div>
          <button class="btn btn-sm" @click="$router.push('/')">New prediction</button>
        </div>
      </div>

      <!-- Content area -->
      <div class="results-panels">
        <!-- Graph panel -->
        <div class="panel graph-panel" :style="graphPanelStyle">
          <SwarmGraph
            :profiles="profiles"
            :posts="posts"
            :width="graphWidth"
            :height="graphHeight"
            ref="swarmGraph"
          />
        </div>

        <!-- Right panel: report + chat -->
        <div class="panel workbench-panel" :style="workbenchPanelStyle">
          <div style="padding: 24px; overflow-y: auto; height: 100%;">
            <!-- Stance breakdown inline -->
            <div class="stance-row mb-24">
              <div v-for="s in stanceData" :key="s.label" class="stance-item">
                <div class="stance-bar-mini" :style="{ background: s.color, width: s.pct + '%' }"></div>
                <span class="text-sm" :style="{ color: s.color }">{{ s.count }} {{ s.label }}</span>
              </div>
            </div>

            <!-- Stance shifts -->
            <div v-if="stanceShifts.length > 0" class="mb-24">
              <h3 style="margin-bottom: 12px;">Stance shifts ({{ stanceShifts.length }})</h3>
              <div class="shift-list">
                <div v-for="(shift, i) in stanceShifts" :key="i" class="shift-item">
                  <strong>{{ shift.agent }}</strong>
                  <span class="text-muted text-sm">R{{ shift.round }}</span>
                  <span class="stance-badge" :class="shift.from">{{ shift.from }}</span>
                  <span class="text-muted">→</span>
                  <span class="stance-badge" :class="shift.to">{{ shift.to }}</span>
                  <span class="text-sm text-secondary" v-if="shift.reason">{{ shift.reason }}</span>
                </div>
              </div>
            </div>

            <!-- Simulation feed -->
            <h3 style="margin-bottom: 12px;">Simulation feed ({{ posts.length }} posts)</h3>
            <div class="sim-feed mb-24">
              <div v-for="post in posts" :key="post.post_id" class="feed-item" style="padding: 8px 0;">
                <div class="flex items-center gap-8">
                  <span class="feed-author">{{ post.agent_name }}</span>
                  <span class="feed-meta">R{{ post.round_num }}</span>
                  <span v-if="post.stance" class="stance-badge" :class="post.stance">{{ post.stance }}</span>
                  <span v-if="post.reply_to" class="text-muted text-sm">→ {{ post.reply_to }}</span>
                </div>
                <div class="feed-content">{{ post.content }}</div>
              </div>
              <div v-if="posts.length === 0" class="text-sm text-muted" style="padding: 16px 0; text-align: center;">No posts.</div>
            </div>

            <!-- Report -->
            <h3 style="margin-bottom: 12px;">Prediction report</h3>
            <div class="md-content mb-24" v-html="reportHtml"></div>

            <!-- Chat -->
            <div class="divider" style="margin: 24px 0;"></div>
            <h3>Follow-up questions</h3>
            <p class="text-sm text-muted mt-4 mb-12">Ask about the simulation.</p>

            <div class="card">
              <div class="chat-messages" ref="chatBox">
                <div v-if="messages.length === 0" style="text-align: center; padding: 12px 0;">
                  <div style="display: flex; flex-wrap: wrap; gap: 6px; justify-content: center;">
                    <button v-for="q in suggestions" :key="q" class="btn btn-sm" @click="askQ(q)">{{ q }}</button>
                  </div>
                </div>
                <div v-for="(msg, i) in messages" :key="i" class="chat-msg" :class="msg.role">
                  <div v-if="msg.role === 'assistant'" class="md-content" v-html="renderMd(msg.content)"></div>
                  <span v-else>{{ msg.content }}</span>
                </div>
                <div v-if="thinking" class="chat-msg assistant">
                  <div class="flex items-center gap-8">
                    <div class="spinner" style="width:14px;height:14px;border-width:2px;"></div>
                    <span class="text-muted text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
              <div class="chat-input-row">
                <input type="text" v-model="question" placeholder="Ask a question..." @keydown.enter="askQ(question)" :disabled="thinking" />
                <button class="btn btn-primary" @click="askQ(question)" :disabled="!question.trim() || thinking">Send</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api/index.js'
import { marked } from 'marked'
import SwarmGraph from '../components/SwarmGraph.vue'

export default {
  name: 'ProjectView',
  components: { SwarmGraph },
  props: ['projectId'],
  data() {
    return {
      currentPhase: 'starting',
      progress: 0,
      message: 'Starting...',
      done: false,
      failed: false,
      reportHtml: '',
      posts: [],
      profiles: [],
      stats: { entities: 0, agents: 0, posts: 0 },
      stanceShifts: [],
      simId: null,
      graphId: null,
      viewMode: 'split',
      graphWidth: 600,
      graphHeight: 600,
      messages: [],
      question: '',
      thinking: false,
      suggestions: [
        'Which agents changed their stance?',
        'What were the strongest disagreements?',
        'What consensus emerged?',
      ],
      phases: [
        { key: 'ontology', label: 'Analysing document structure' },
        { key: 'graph', label: 'Extracting entities' },
        { key: 'agents', label: 'Creating agent profiles' },
        { key: 'simulation', label: 'Running simulation' },
        { key: 'report', label: 'Writing report' },
      ],
      pollTimer: null,
      startTime: Date.now(),
      elapsedSeconds: 0,
      tickTimer: null,
      hintIndex: 0,
      hintTimer: null,
      phaseHints: {
        starting: [
          'Initialising prediction engine...',
          'Preparing your data for analysis...',
        ],
        ontology: [
          'Scanning document for domain structure...',
          'Identifying key concepts and categories...',
          'Mapping relationships between entities...',
          'Building a semantic understanding of your data...',
        ],
        graph: [
          'Extracting named entities from text...',
          'Linking entities to form a knowledge network...',
          'Weighting connections by evidence strength...',
          'Constructing the knowledge graph...',
        ],
        agents: [
          'Generating diverse cognitive profiles...',
          'Assigning expertise domains to each agent...',
          'Calibrating reasoning styles and risk postures...',
          'Each agent gets a unique perspective on the data...',
        ],
        simulation: [
          'Agents are reading the knowledge graph...',
          'Round in progress, agents posting analyses...',
          'Agents challenging each other\'s reasoning...',
          'Tracking stance shifts across the swarm...',
          'Debate is heating up, positions crystallising...',
          'Minority agents stress-testing the consensus...',
          'Coalition patterns emerging among agents...',
        ],
        report: [
          'Analysing the full debate transcript...',
          'Measuring consensus strength...',
          'Synthesising the final prediction report...',
          'Calculating confidence intervals...',
        ],
      },
    }
  },
  computed: {
    elapsed() {
      const m = Math.floor(this.elapsedSeconds / 60)
      const s = this.elapsedSeconds % 60
      return `${m}:${String(s).padStart(2, '0')}`
    },
    phaseLabel() {
      const found = this.phases.find(p => p.key === this.currentPhase)
      return found ? found.label : 'Processing...'
    },
    activeHint() {
      const hints = this.phaseHints[this.currentPhase] || ['Processing...']
      return hints[this.hintIndex % hints.length]
    },
    graphPanelStyle() {
      if (this.viewMode === 'graph') return { width: '100%' }
      if (this.viewMode === 'report') return { width: '0%', overflow: 'hidden', opacity: 0 }
      return { width: '50%' }
    },
    workbenchPanelStyle() {
      if (this.viewMode === 'report') return { width: '100%' }
      if (this.viewMode === 'graph') return { width: '0%', overflow: 'hidden', opacity: 0 }
      return { width: '50%' }
    },
    stanceData() {
      const counts = { supportive: 0, opposing: 0, neutral: 0 }
      for (const p of this.profiles) {
        const s = (p.stance || 'neutral').toLowerCase()
        if (s.includes('support') || s.includes('favor')) counts.supportive++
        else if (s.includes('oppos') || s.includes('against') || s.includes('critic')) counts.opposing++
        else counts.neutral++
      }
      const total = Math.max(counts.supportive + counts.opposing + counts.neutral, 1)
      return [
        { label: 'supportive', count: counts.supportive, pct: (counts.supportive / total) * 100, color: '#30a46c' },
        { label: 'opposing', count: counts.opposing, pct: (counts.opposing / total) * 100, color: '#e5484d' },
        { label: 'neutral', count: counts.neutral, pct: (counts.neutral / total) * 100, color: '#666' },
      ]
    },
  },
  mounted() {
    this.poll()
    this.tickTimer = setInterval(() => { this.elapsedSeconds++ }, 1000)
    this.hintTimer = setInterval(() => { this.hintIndex++ }, 4000)
    window.addEventListener('resize', this.updateGraphSize)
  },
  beforeUnmount() {
    if (this.pollTimer) clearTimeout(this.pollTimer)
    if (this.tickTimer) clearInterval(this.tickTimer)
    if (this.hintTimer) clearInterval(this.hintTimer)
    window.removeEventListener('resize', this.updateGraphSize)
  },
  methods: {
    phaseIndex(key) {
      return this.phases.findIndex(p => p.key === key)
    },
    renderMd(text) {
      return marked(text || '')
    },
    updateGraphSize() {
      const el = document.querySelector('.graph-panel')
      if (el) {
        this.graphWidth = el.clientWidth
        this.graphHeight = el.clientHeight
      }
    },
    async poll() {
      try {
        const res = await api.get(`/api/pipeline/status/${this.projectId}`)
        if (res.success) {
          this.currentPhase = res.phase || 'starting'
          this.progress = res.progress || 0
          this.message = res.message || ''

          if (res.phase === 'done') {
            this.done = true
            this.reportHtml = marked(res.report_markdown || '')
            this.posts = res.posts || []
            this.profiles = res.profiles || []
            this.stats = {
              entities: res.entity_count || 0,
              agents: res.agent_count || 0,
              posts: res.post_count || 0,
            }
            this.simId = res.sim_id
            this.graphId = res.graph_id
            this.stanceShifts = res.stance_shifts || []
            this.$nextTick(() => this.updateGraphSize())
            return
          }
          if (res.phase === 'failed') {
            this.failed = true
            return
          }
        }
      } catch (err) {
        console.error(err)
      }
      this.pollTimer = setTimeout(() => this.poll(), 2000)
    },
    async askQ(q) {
      q = (q || '').trim()
      if (!q) return
      this.messages.push({ role: 'user', content: q })
      this.question = ''
      this.thinking = true
      this.$nextTick(() => { if (this.$refs.chatBox) this.$refs.chatBox.scrollTop = this.$refs.chatBox.scrollHeight })

      try {
        const res = await api.post('/api/report/chat', {
          project_id: this.projectId,
          sim_id: this.simId,
          question: q,
          history: this.messages.map(m => ({ role: m.role, content: m.content })),
        })
        if (res.success) this.messages.push({ role: 'assistant', content: res.answer })
      } catch {
        this.messages.push({ role: 'assistant', content: 'Something went wrong. Try again.' })
      } finally {
        this.thinking = false
        this.$nextTick(() => { if (this.$refs.chatBox) this.$refs.chatBox.scrollTop = this.$refs.chatBox.scrollHeight })
      }
    },
  },
}
</script>

<style scoped>
.results-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.results-header {
  height: 52px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
}
.results-header .logo {
  font-weight: 700;
  font-size: 1rem;
  letter-spacing: -0.02em;
}
.view-switcher {
  display: flex;
  background: var(--bg-surface);
  padding: 3px;
  border-radius: 6px;
  gap: 2px;
}
.switch-btn {
  border: none;
  background: transparent;
  padding: 5px 14px;
  font-size: 0.73rem;
  font-weight: 600;
  color: var(--text-muted);
  border-radius: 4px;
  cursor: pointer;
  font-family: var(--font);
  transition: all 0.15s;
}
.switch-btn.active {
  background: var(--bg-raised);
  color: var(--text);
  border: 1px solid var(--border);
}
.stat-pill {
  font-size: 0.7rem;
  font-family: var(--mono);
  color: var(--text-muted);
  padding: 3px 8px;
  border: 1px solid var(--border);
  border-radius: 100px;
}
.results-panels {
  flex: 1;
  display: flex;
  overflow: hidden;
}
.panel {
  height: 100%;
  overflow: hidden;
  transition: width 0.3s ease, opacity 0.2s ease;
}
.graph-panel {
  border-right: 1px solid var(--border);
}
.workbench-panel {
  overflow-y: auto;
}
.stance-row {
  display: flex;
  gap: 16px;
  align-items: center;
}
.stance-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.stance-bar-mini {
  height: 8px;
  min-width: 8px;
  border-radius: 4px;
}
.sim-feed {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px 14px;
}
.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--success);
  display: inline-block;
  animation: pulse-glow 1.5s ease-in-out infinite;
}
@keyframes pulse-glow {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}
.stance-badge {
  font-size: 0.65rem;
  padding: 1px 6px;
  border-radius: 100px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}
.stance-badge.supportive { background: #dcfce7; color: #166534; }
.stance-badge.opposing { background: #fef2f2; color: #991b1b; }
.stance-badge.neutral { background: #f5f5f5; color: #666; }
.stance-badge.cautious { background: #fef9c3; color: #854d0e; }
.stance-badge.shifted { background: #ede9fe; color: #5b21b6; }
.shift-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.shift-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
}
.sim-feed {
  max-height: 500px;
}

/* Fade transition for hints */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .results-layout {
    height: auto;
    min-height: 100vh;
  }
  .results-header {
    height: auto;
    flex-direction: column;
    gap: 8px;
    padding: 10px 16px;
  }
  .results-panels {
    flex-direction: column;
  }
  .panel {
    height: auto !important;
    width: 100% !important;
  }
  .graph-panel {
    border-right: none;
    border-bottom: 1px solid var(--border);
    height: 300px !important;
  }
  .workbench-panel > div {
    padding: 16px !important;
  }
  .stat-pill {
    font-size: 0.6rem;
    padding: 2px 6px;
  }
  .stance-row {
    flex-wrap: wrap;
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .view-switcher {
    gap: 1px;
  }
  .switch-btn {
    padding: 4px 10px;
    font-size: 0.65rem;
  }
  .sim-feed {
    max-height: 250px;
  }
}
</style>
