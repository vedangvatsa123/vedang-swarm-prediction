<template>
  <div class="wiki-page">
    <div class="wiki-header">
      <router-link to="/" class="back-link">← Back</router-link>
      <h1>How It Works</h1>
      <p class="wiki-subtitle">The architecture behind swarm intelligence prediction</p>
    </div>

    <div class="wiki-body">
      <img :src="graphImg" alt="Knowledge graph network" class="wiki-illust" style="margin-bottom: 32px;" />

      <!-- Why -->
      <section class="wiki-section">
        <h2>Why swarm prediction?</h2>
        <p>
          Most AI prediction tools work the same way: you ask a single language model a question and it
          gives you one answer. The problem is that a single model carries a single set of biases, blind
          spots, and reasoning habits. It has no way to challenge itself. If it starts down the wrong
          path, there is nothing to pull it back.
        </p>
        <p>
          This engine takes a different approach. Instead of asking one model once, it creates a
          population of AI agents, each with a different perspective, and makes them debate. Agents
          argue, challenge each other, shift their positions when they encounter better evidence, and
          eventually settle into a consensus. The final prediction comes from that consensus, not from
          any single agent.
        </p>
        <p>
          The idea is borrowed from ensemble methods in machine learning (where many weak learners
          outperform one strong learner) and from prediction markets (where aggregated independent
          judgments beat individual expert forecasts). The difference is that this system makes the
          reasoning process visible. You can read the debate, see who changed their mind and why, and
          judge for yourself whether the conclusion is sound.
        </p>
      </section>

      <!-- The Problem -->
      <section class="wiki-section">
        <h2>The problem with single-model predictions</h2>
        <p>
          Language models are trained on massive datasets, but that training creates systematic
          tendencies. A model might consistently overweight recent events, avoid contrarian positions,
          or default to hedging language that sounds authoritative but says very little. When you ask
          a model "Will X happen?", the answer depends heavily on how the question is framed, what
          context is provided, and the model's implicit priors.
        </p>
        <p>
          There is no self-correction mechanism. If you ask the same model the same question ten
          times, you get ten variations of the same answer. The responses look diverse on the surface
          but share the same underlying reasoning structure. This is not diversity of thought. It
          is diversity of phrasing.
        </p>
        <p>
          This engine solves that by forcing genuine disagreement. Each agent is constructed with a
          different cognitive profile: different areas of expertise, different risk tolerances,
          different reasoning styles. Some agents are analytically rigorous. Some are intuition-driven.
          Some are deliberately contrarian. When these agents engage with each other, blind spots get
          exposed and weak arguments get challenged.
        </p>
      </section>

      <!-- Pipeline -->
      <section class="wiki-section">
        <h2>The prediction pipeline</h2>
        <p>
          Every prediction runs through five stages, each building on the output of the previous one.
          The pipeline is designed so that the quality of each stage compounds. A better knowledge graph
          leads to more relevant agents, which leads to a richer debate, which leads to a better report.
        </p>
        <div class="pipeline-steps">
          <div v-for="(step, i) in pipelineSteps" :key="i" class="pipeline-card">
            <div class="pipeline-num">{{ i + 1 }}</div>
            <div>
              <h3>{{ step.title }}</h3>
              <p>{{ step.desc }}</p>
            </div>
          </div>
        </div>
        <img :src="pipelineImg" alt="Pipeline flow diagram" class="wiki-illust" />
      </section>

      <!-- Document Ingestion -->
      <section class="wiki-section">
        <h2>Stage 1: Document ingestion</h2>
        <p>
          The engine accepts input in several formats: uploaded files (PDF, Markdown, plain text),
          pasted text, or a URL. The input is normalised into a clean text corpus with metadata
          preserved where possible (headings, structure, source attribution).
        </p>
        <p>
          This stage is intentionally simple. The goal is to get your data into a form that the next
          stage can work with. There is no summarisation or lossy compression here. The full text is
          preserved because the agents need access to specifics, not summaries.
        </p>
      </section>

      <!-- Knowledge Graph -->
      <section class="wiki-section">
        <h2>Stage 2: Knowledge graph extraction</h2>
        <p>
          Before any agents are created, the engine builds a knowledge graph from your input data. This
          is the factual substrate that all agents share. The process has two parts: ontology detection
          and entity extraction.
        </p>
        <p>
          <strong>Ontology detection</strong> identifies the types of things that matter in your data.
          If you upload a financial report, the ontology might include companies, metrics, market
          events, and regulatory actions. If you upload a geopolitical analysis, it might include
          nations, leaders, treaties, and conflicts. The ontology is not pre-defined. It is inferred
          from the data itself.
        </p>
        <p>
          <strong>Entity extraction</strong> then populates that ontology with specific instances.
          Each entity gets a type, a description, and a set of relationships to other entities. The
          relationships are directional and typed: "Company A acquired Company B", "Policy X was
          enacted in response to Event Y". These relationships form the edges of the knowledge graph.
        </p>
        <p>
          The knowledge graph serves two purposes. First, it gives agents a shared factual foundation
          so they argue about interpretation rather than facts. Second, it determines what kinds of
          agents get created in the next stage.
        </p>
      </section>
      <section class="wiki-section">
        <h2>Stage 3: Agent generation</h2>
        <p>
          Each agent in the swarm is not a generic chatbot. It is a purpose-built cognitive persona
          with several properties that shape how it thinks:
        </p>
        <ul class="feature-list">
          <li>
            <strong>Expertise domain.</strong> Drawn from the knowledge graph's entity types. An agent
            specialising in financial metrics will focus on different aspects of the data than one
            specialising in regulatory risk.
          </li>
          <li>
            <strong>Reasoning style.</strong> Some agents reason analytically, working through evidence
            step by step. Others reason by analogy, drawing on historical parallels. Others are
            synthesis-oriented, looking for patterns across domains.
          </li>
          <li>
            <strong>Risk posture.</strong> Conservative agents give more weight to downside scenarios.
            Aggressive agents focus on upside potential. This ensures that the debate explores the
            full probability space rather than clustering around the median.
          </li>
          <li>
            <strong>Initial stance.</strong> Every agent enters the simulation with a starting position
            on the prediction question. This position is informed by their profile but is explicitly
            subject to change during the debate.
          </li>
          <li>
            <strong>Persuadability.</strong> How much evidence it takes for an agent to change its mind.
            Low-persuadability agents act as anchors, forcing the debate to produce strong evidence
            before consensus can shift. High-persuadability agents respond quickly to new arguments,
            acting as early signals for emerging consensus.
          </li>
        </ul>
        <p>
          The number of agents scales with the chosen simulation depth. A quick run uses 10 agents.
          A maximum-depth run uses 100. The profiles are generated to maximise diversity across all
          five dimensions listed above.
        </p>
      </section>

      <!-- Simulation -->
      <section class="wiki-section">
        <h2>Stage 4: Multi-round simulation</h2>
        <p>
          This is where the prediction actually happens. The simulation runs in discrete rounds. In
          each round, a subset of agents are selected to participate. Each participating agent can
          do one of three things:
        </p>
        <ul class="feature-list">
          <li>
            <strong>Post an original analysis.</strong> The agent reads the knowledge graph, considers
            the prediction question through its cognitive lens, and writes a position statement with
            supporting reasoning.
          </li>
          <li>
            <strong>Reply to another agent.</strong> The agent reads a previous post and either
            supports it with additional evidence, challenges it with counter-arguments, or offers
            a synthesis that reconciles competing views.
          </li>
          <li>
            <strong>Shift its stance.</strong> If an agent encounters an argument compelling enough
            to overcome its persuadability threshold, it changes its position. The shift is logged
            with the old stance, the new stance, the triggering argument, and the agent's stated
            reason for changing. This creates an auditable trail of how opinion evolved.
          </li>
        </ul>
        <p>
          The simulation does not have a pre-determined outcome. Agents make independent decisions
          based on their profiles and the arguments they encounter. Consensus can emerge quickly if
          the evidence strongly favours one outcome, or the debate can remain contested through the
          final round if the question is genuinely uncertain.
        </p>
        <p>
          The depth settings control three parameters: the number of agents, the number of rounds,
          and the number of agents that participate per round. A deeper simulation explores more
          of the problem space but takes longer.
        </p>

        <div class="highlight-box">
          <strong>Depth presets:</strong>
          <ul class="depth-list">
            <li><strong>Quick</strong> - 10 agents, 4 rounds, about 1 minute</li>
            <li><strong>Balanced</strong> - 30 agents, 8 rounds, about 3 minutes</li>
            <li><strong>Deep</strong> - 50 agents, 12 rounds, about 8 minutes</li>
            <li><strong>Maximum</strong> - 100 agents, 16 rounds, about 15 minutes</li>
          </ul>
        </div>
      </section>
      <section class="wiki-section">
        <h2>Stage 5: Consensus report</h2>
        <p>
          After the simulation finishes, a dedicated report agent reads the complete debate
          transcript and generates a structured prediction report. This agent does not participate
          in the debate itself. It acts as an impartial analyst of the debate's outcome.
        </p>
        <p>The report includes:</p>
        <ul class="feature-list">
          <li>The majority position with the key arguments that support it</li>
          <li>Minority positions and why they persisted despite counter-arguments</li>
          <li>A list of stance shifts showing which agents changed their minds and why</li>
          <li>Points of agreement that held across all agents regardless of profile</li>
          <li>Unresolved disagreements where agents could not reach consensus</li>
          <li>Risk factors and edge cases identified by contrarian agents</li>
          <li>A final probabilistic assessment with confidence bounds</li>
        </ul>
        <p>
          The report is designed to be readable by someone who did not watch the simulation unfold.
          It should stand alone as a complete analysis of the prediction question.
        </p>
      </section>

      <!-- Follow-up -->
      <section class="wiki-section">
        <h2>Follow-up questions</h2>
        <p>
          After the report is generated, you can ask follow-up questions about the simulation. The
          system has access to the full debate transcript, all agent profiles, the knowledge graph,
          and the final report. You can ask things like "Which agents disagreed the most?", "What
          would change the prediction?", or "What assumptions is the majority position relying on?".
        </p>
        <p>
          This turns the prediction from a one-shot output into an interactive analysis session.
          You can drill into the reasoning, challenge the assumptions, and use the system as a
          thinking partner rather than an oracle.
        </p>
      </section>

      <!-- Visualisation -->
      <section class="wiki-section">
        <h2>Graph visualisation</h2>
        <p>
          The results page includes a force-directed graph showing all agents as nodes and their
          interactions as edges. You can see at a glance which agents formed clusters, who argued
          with whom, and where the fault lines in the debate were. The graph updates based on
          the simulation data and can be viewed alongside the report in a split-panel layout.
        </p>
      </section>

      <!-- Security -->
      <section class="wiki-section">
        <h2>Security and privacy</h2>
        <p>
          The engine operates on a Bring Your Own Key model. You provide your own API key from
          any supported provider. The key is stored only in your browser's local storage. When
          you start a prediction, the key is sent over HTTPS to the backend, used for a single
          request, and then deleted from server memory. It is never written to disk, never logged,
          and never shared with any third party.
        </p>
        <p>
          Your input data is processed in memory during the prediction run. Nothing is persisted
          after the process completes. There is no database of past predictions, no user accounts,
          and no tracking. Each prediction is a self-contained, stateless operation.
        </p>
      </section>

      <!-- Supported providers -->
      <section class="wiki-section">
        <h2>Supported LLM providers</h2>
        <p>
          The engine supports 8 LLM providers through the BYOK system. You can use whichever
          provider you already have an API key for:
        </p>
        <div class="tech-grid">
          <div v-for="p in providers" :key="p" class="tech-card">
            <span>{{ p }}</span>
          </div>
        </div>
      </section>

      <!-- Tech stack -->
      <section class="wiki-section">
        <h2>Technology stack</h2>
        <div class="tech-grid">
          <div v-for="t in techStack" :key="t.label" class="tech-card">
            <strong>{{ t.label }}</strong>
            <span>{{ t.detail }}</span>
          </div>
        </div>
      </section>

      <!-- Limitations -->
      <section class="wiki-section">
        <h2>Limitations and honest caveats</h2>
        <p>
          This system is a tool for structured thinking, not an oracle. There are real limitations
          worth understanding:
        </p>
        <ul class="feature-list">
          <li>
            <strong>Garbage in, garbage out.</strong> The quality of the prediction depends heavily
            on the quality and relevance of the input data. Vague or insufficient data produces
            vague predictions.
          </li>
          <li>
            <strong>LLM constraints apply.</strong> The agents are powered by language models, which
            means they inherit the training data cutoffs, knowledge gaps, and reasoning limitations
            of those models. The engine mitigates some of these through diversity, but it cannot
            overcome fundamental model limitations.
          </li>
          <li>
            <strong>Not calibrated on real outcomes.</strong> Unlike prediction markets, which are
            calibrated by real money and real outcomes, this system has no feedback mechanism. The
            confidence percentages should be treated as relative indicators, not absolute
            probabilities.
          </li>
          <li>
            <strong>Cost scales with depth.</strong> Each agent makes LLM calls. A maximum-depth
            run with 100 agents across 16 rounds can consume significant API credits. The depth
            presets exist to give you control over this tradeoff.
          </li>
        </ul>
      </section>

    </div>
  </div>
</template>

<script>
import pipelineImg from '../assets/wiki-pipeline.png'
import graphImg from '../assets/wiki-graph.png'
import debateImg from '../assets/wiki-debate.png'

export default {
  name: 'Wiki',
  data() {
    return {
      pipelineImg,
      graphImg,
      debateImg,
      pipelineSteps: [
        { title: 'Document ingestion', desc: 'Your source files are parsed into a clean text corpus with structure preserved.' },
        { title: 'Knowledge graph extraction', desc: 'Entities, relationships, and causal structures are identified and linked into a typed graph.' },
        { title: 'Agent generation', desc: 'Diverse cognitive personas are created, each with unique expertise, reasoning style, and risk posture.' },
        { title: 'Multi-round simulation', desc: 'Agents debate across multiple rounds, posting analyses, challenging each other, and shifting positions.' },
        { title: 'Consensus report', desc: 'The full debate transcript is analysed to produce a structured prediction with confidence bounds.' },
      ],
      providers: [
        'Anthropic', 'OpenAI', 'Google Gemini', 'Groq',
        'Mistral AI', 'Together AI', 'OpenRouter', 'DeepSeek',
      ],
      techStack: [
        { label: 'Frontend', detail: 'Vue.js 3 with Vite' },
        { label: 'Backend', detail: 'Python / Flask' },
        { label: 'LLM integration', detail: '8 providers via BYOK' },
        { label: 'Graph engine', detail: 'Custom ontology extraction' },
        { label: 'Visualisation', detail: 'Force-directed SVG rendering' },
        { label: 'Logging', detail: 'Structured with file rotation' },
      ],
    }
  },
}
</script>

<style scoped>
.wiki-page {
  max-width: 780px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}
.wiki-header {
  margin-bottom: 40px;
}
.back-link {
  font-size: 0.875rem;
  color: var(--text-muted);
  display: inline-block;
  margin-bottom: 16px;
}
.back-link:hover {
  color: var(--text);
}
.wiki-header h1 {
  font-size: 2.2rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin-bottom: 8px;
}
.wiki-subtitle {
  font-size: 1.1rem;
  color: var(--text-muted);
}

.wiki-section {
  margin-bottom: 36px;
}
.wiki-illust {
  width: 100%;
  max-width: 520px;
  height: auto;
  display: block;
  margin: 20px auto 0;
  border-radius: var(--radius);
}
.wiki-section h2 {
  font-size: 1.35rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.wiki-section p {
  margin-bottom: 12px;
  line-height: 1.7;
  color: var(--text-secondary);
}
.wiki-section p strong {
  color: var(--text);
}

.highlight-box {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 18px;
  margin: 16px 0;
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--text-secondary);
}
.highlight-box strong {
  color: var(--text);
}
.depth-list {
  padding-left: 18px;
  margin-top: 8px;
  margin-bottom: 0;
}
.depth-list li {
  margin-bottom: 4px;
  font-size: 0.9rem;
}

.feature-list {
  padding-left: 20px;
  margin-bottom: 14px;
}
.feature-list li {
  margin-bottom: 10px;
  line-height: 1.65;
  color: var(--text-secondary);
  font-size: 0.95rem;
}
.feature-list li strong {
  color: var(--text);
}

.pipeline-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}
.pipeline-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}
.pipeline-card h3 {
  font-size: 1rem;
  margin-bottom: 2px;
}
.pipeline-card p {
  font-size: 0.9rem;
  margin-bottom: 0;
}
.pipeline-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 2px;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 12px;
}
.tech-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px 14px;
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 0.9rem;
}
.tech-card strong {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}
.tech-card span {
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .wiki-page {
    padding: 20px 16px 48px;
  }
  .wiki-header h1 {
    font-size: 1.6rem;
  }
  .tech-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .tech-grid {
    grid-template-columns: 1fr;
  }
}
</style>
