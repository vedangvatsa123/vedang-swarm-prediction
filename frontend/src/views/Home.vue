<template>
  <div class="home-page">
    <!-- Hero row -->
    <div class="hero-row">
      <img :src="swarmImg" alt="" class="hero-illust" />
      <div class="hero-text">
        <h1>Predict outcomes with collective AI intelligence</h1>
        <div class="steps-inline">
          <span v-for="(s, i) in steps" :key="i" class="step-chip">
            <span class="step-dot">{{ i + 1 }}</span> {{ s }}
          </span>
        </div>
      </div>
    </div>

    <!-- Form -->
    <div class="form-section">
      <div class="card" style="padding: 20px;">

        <div class="mb-12">
          <label>What do you want to predict?</label>
          <textarea v-model="goal" placeholder="Describe the scenario. Be specific." rows="2"></textarea>
        </div>

        <!-- Data source selector -->
        <div class="mb-12">
          <label>Data source</label>
          <div class="source-tabs">
            <button v-for="src in sources" :key="src.key"
              class="source-tab" :class="{ active: dataSource === src.key }"
              @click="dataSource = src.key">
              {{ src.label }}
            </button>
          </div>
        </div>

        <!-- Upload files -->
        <div v-if="dataSource === 'upload'" class="mb-12">
          <div
            class="drop-zone compact-drop"
            :class="{ dragover }"
            @dragover.prevent="dragover = true"
            @dragleave="dragover = false"
            @drop.prevent="onDrop"
            @click="$refs.fileInput.click()"
          >
            <div v-if="files.length === 0">
              <p style="color: var(--text-muted);">Click to browse or drag files here <span class="text-muted">(PDF, MD, TXT)</span></p>
            </div>
            <div v-else>
              <p v-for="f in files" :key="f.name" style="color: var(--text-secondary);">
                {{ f.name }} <span class="text-muted">({{ (f.size / 1024).toFixed(1) }} KB)</span>
              </p>
              <p class="text-muted" style="cursor: pointer; margin-top: 4px;" @click.stop="files = []">Clear</p>
            </div>
            <input ref="fileInput" type="file" multiple accept=".pdf,.md,.txt,.markdown" style="display:none" @change="onFileSelect" />
          </div>
        </div>

        <!-- URL input -->
        <div v-if="dataSource === 'url'" class="mb-12">
          <input type="text" v-model="sourceUrl" placeholder="https://example.com/article" />
          <p class="text-sm text-muted" style="margin-top: 4px;">Paste any public URL.</p>
        </div>

        <!-- Paste text -->
        <div v-if="dataSource === 'paste'" class="mb-12">
          <textarea v-model="pasteText" placeholder="Paste your text here..." rows="4"></textarea>
        </div>

        <!-- Advanced settings toggle -->
        <div class="mb-12">
          <button class="advanced-toggle" @click="showAdvanced = !showAdvanced">
            Advanced settings
            <span class="toggle-arrow" :class="{ open: showAdvanced }">▸</span>
          </button>
        </div>

        <!-- Advanced settings panel -->
        <div v-if="showAdvanced" class="advanced-panel mb-12">
          <div class="mb-12">
            <label>Your API key</label>
            <p class="key-notice">Your key is stored only in your browser's local storage. It is sent to this server over HTTPS, used for one request, then discarded from memory. It is never logged, saved to disk, or shared.</p>
            <div style="display: flex; gap: 8px;">
              <select v-model="apiProvider" style="width: 140px; flex-shrink: 0;" @change="saveKeyToStorage">
                <option value="anthropic">Anthropic</option>
                <option value="openai">OpenAI</option>
                <option value="gemini">Google Gemini</option>
                <option value="groq">Groq</option>
                <option value="mistral">Mistral AI</option>
                <option value="together">Together AI</option>
                <option value="openrouter">OpenRouter</option>
                <option value="deepseek">DeepSeek</option>
              </select>
              <input type="password" v-model="apiKey" :placeholder="keyPlaceholder" @blur="saveKeyToStorage" autocomplete="off" style="flex: 1;" />
            </div>
            <p v-if="apiKey" style="color: var(--success); margin-top: 4px;">Key saved in browser.</p>
            <button v-if="apiKey" class="clear-key-btn" @click="clearKey">Clear saved key</button>
          </div>
          <label>Simulation depth</label>
          <div class="depth-options">
            <button v-for="d in depthOptions" :key="d.key"
              class="depth-btn" :class="{ active: simDepth === d.key }"
              @click="simDepth = d.key">
              <strong>{{ d.label }}</strong>
              <span class="text-muted">{{ d.desc }}</span>
            </button>
          </div>
        </div>

        <button class="btn btn-primary w-full" :disabled="loading || !goal || !hasSource" @click="submit">
          <span v-if="loading" class="spinner" style="width:16px;height:16px;border-width:2px;"></span>
          {{ loading ? 'Starting...' : 'Start prediction' }}
        </button>

        <p v-if="error" style="color: var(--danger); margin-top: 8px;">{{ error }}</p>

        <p v-if="!goal || !hasSource" class="text-muted text-center" style="margin-top: 10px;">
          {{ !goal && !hasSource ? 'Add a question and provide data to begin.' : !goal ? 'Describe what you want to predict.' : 'Provide a data source above.' }}
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api/index.js'
import swarmImg from '../assets/swarm.png'

export default {
  name: 'Home',
  data() {
    return {
      swarmImg,
      steps: [
        'Feed your data',
        'Agents simulate & debate',
        'Get prediction report',
      ],
      goal: '',
      files: [],
      dragover: false,
      loading: false,
      error: '',
      dataSource: 'upload',
      sourceUrl: '',
      pasteText: '',
      showAdvanced: false,
      simDepth: 'balanced',
      apiKey: '',
      apiProvider: 'anthropic',
      depthOptions: [
        { key: 'quick', label: 'Quick', desc: '~1 min' },
        { key: 'balanced', label: 'Balanced', desc: '~3 min' },
        { key: 'deep', label: 'Deep', desc: '~8 min' },
        { key: 'maximum', label: 'Maximum', desc: '~15 min' },
      ],
      sources: [
        { key: 'upload', label: 'Upload files' },
        { key: 'url', label: 'From URL' },
        { key: 'paste', label: 'Paste text' },
      ],
    }
  },
  computed: {
    hasSource() {
      if (this.dataSource === 'upload') return this.files.length > 0
      if (this.dataSource === 'url') return this.sourceUrl.trim().length > 0
      if (this.dataSource === 'paste') return this.pasteText.trim().length > 0
      return false
    },
    keyPlaceholder() {
      return {
        anthropic: 'sk-ant-...',
        openai: 'sk-...',
        gemini: 'AIza...',
        groq: 'gsk_...',
        mistral: '...',
        together: '...',
        openrouter: 'sk-or-...',
        deepseek: 'sk-...',
      }[this.apiProvider] || 'API key'
    },
  },
  mounted() {
    const saved = localStorage.getItem('vedang_api_key')
    const savedProvider = localStorage.getItem('vedang_api_provider')
    if (saved) this.apiKey = saved
    if (savedProvider) this.apiProvider = savedProvider
  },
  methods: {
    saveKeyToStorage() {
      if (this.apiKey) {
        localStorage.setItem('vedang_api_key', this.apiKey)
        localStorage.setItem('vedang_api_provider', this.apiProvider)
      }
    },
    clearKey() {
      this.apiKey = ''
      this.apiProvider = 'anthropic'
      localStorage.removeItem('vedang_api_key')
      localStorage.removeItem('vedang_api_provider')
    },
    onFileSelect(e) {
      this.files = Array.from(e.target.files)
    },
    onDrop(e) {
      this.dragover = false
      this.files = Array.from(e.dataTransfer.files)
    },
    async submit() {
      this.loading = true
      this.error = ''
      try {
        const depthMap = {
          quick: { agents: 10, rounds: 4, per_round: 4 },
          balanced: { agents: 30, rounds: 8, per_round: 8 },
          deep: { agents: 50, rounds: 12, per_round: 8 },
          maximum: { agents: 100, rounds: 16, per_round: 10 },
        }
        const depth = depthMap[this.simDepth] || depthMap.balanced

        const form = new FormData()
        form.append('prediction_goal', this.goal)
        form.append('project_name', 'Prediction')
        form.append('agent_count', String(depth.agents))
        form.append('round_count', String(depth.rounds))
        form.append('agents_per_round', String(depth.per_round))

        if (this.apiKey) {
          form.append('api_key', this.apiKey)
          form.append('api_provider', this.apiProvider)
        }

        if (this.dataSource === 'upload') {
          this.files.forEach(f => form.append('files', f))
        } else if (this.dataSource === 'url') {
          const blob = new Blob([`Source URL: ${this.sourceUrl}\n\nContent will be fetched from this URL.`], { type: 'text/plain' })
          form.append('files', blob, 'source_url.txt')
          form.append('source_url', this.sourceUrl)
        } else if (this.dataSource === 'paste') {
          const blob = new Blob([this.pasteText], { type: 'text/plain' })
          form.append('files', blob, 'pasted_text.txt')
        }

        const res = await api.post('/api/pipeline/start', form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })

        if (res.success) {
          this.$router.push({ name: 'Project', params: { projectId: res.project_id } })
        } else {
          this.error = res.error || 'Upload failed'
        }
      } catch (err) {
        this.error = err.response?.data?.error || err.message || 'Something went wrong'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.home-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 32px 32px 40px;
}
.mb-12 { margin-bottom: 10px; }

/* Hero row */
.hero-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  margin-bottom: 20px;
}
.hero-illust {
  width: 160px;
  height: auto;
}
.hero-text h1 {
  font-size: 1.8rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin-bottom: 12px;
}
.steps-inline {
  display: flex;
  gap: 16px;
  flex-wrap: nowrap;
  justify-content: center;
}
.step-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: var(--text-secondary);
  white-space: nowrap;
}
.step-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1.5px solid var(--border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--text-muted);
  flex-shrink: 0;
}

/* Form */
.form-section {
  width: 100%;
}

/* Source tabs */
.source-tabs {
  display: flex;
  gap: 6px;
}
.source-tab {
  flex: 1;
  padding: 8px 10px;
  font-size: 0.9rem;
  font-family: var(--font);
  font-weight: 500;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
}
.source-tab:hover {
  border-color: var(--border-hover);
  color: var(--text);
}
.source-tab.active {
  border-color: var(--accent);
  color: var(--text);
  background: var(--bg-surface);
}

/* Drop zone */
.compact-drop {
  padding: 14px 16px !important;
}

/* Advanced toggle */
.advanced-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  background: none;
  border: none;
  font-family: var(--font);
  font-size: 0.95rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.15s;
}
.advanced-toggle:hover {
  color: var(--text);
}
.toggle-arrow {
  font-size: 0.75rem;
  transition: transform 0.15s;
}
.toggle-arrow.open {
  transform: rotate(90deg);
}

/* Advanced panel */
.advanced-panel {
  padding: 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.key-notice {
  font-size: 0.8rem;
  color: var(--text-muted);
  line-height: 1.4;
  margin-bottom: 8px;
}
.clear-key-btn {
  display: inline-block;
  margin-top: 4px;
  padding: 0;
  background: none;
  border: none;
  font-family: var(--font);
  font-size: 0.85rem;
  color: var(--danger);
  cursor: pointer;
  text-decoration: underline;
}

/* Depth selector */
.depth-options {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 6px;
}
.depth-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 6px;
  font-family: var(--font);
  font-size: 0.85rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: transparent;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--text);
  text-align: center;
}
.depth-btn:hover {
  border-color: var(--border-hover);
}
.depth-btn.active {
  border-color: var(--accent);
  background: var(--bg);
}

@media (max-width: 768px) {
  .home-page {
    padding: 20px 16px 32px;
  }
  .hero-row {
    gap: 12px;
  }
  .hero-illust {
    width: 80px;
  }
  .hero-text h1 {
    font-size: 1.4rem;
  }
  .steps-inline {
    flex-wrap: wrap;
    justify-content: center;
  }
  .depth-options {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
