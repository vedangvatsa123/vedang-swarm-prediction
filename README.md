# Swarm Intelligence Prediction Engine

Multi-agent AI debate system for forecasting. Feed it data and a question, it creates a population of AI agents with different perspectives, makes them argue across multiple rounds, and produces a structured prediction from where they land.

**Demo:** [veda.ng/swarm-prediction](https://veda.ng/swarm-prediction)

![Knowledge graph visualisation](frontend/src/assets/wiki-graph.png)

---

## Table of Contents

- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [The Pipeline](#the-pipeline)
- [Backend Services](#backend-services)
- [Frontend Structure](#frontend-structure)
- [Data Flow](#data-flow)
- [LLM Integration](#llm-integration)
- [Simulation Mechanics](#simulation-mechanics)
- [Depth Presets](#depth-presets)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [Security Model](#security-model)
- [Limitations](#limitations)

---

## What It Does

If you ask one LLM to predict something, you get one answer with one set of biases. Ask again, you get the same answer in different words. Nothing pushes back.

This takes a different approach:

1. Parses your input data into a knowledge graph of entities and relationships
2. Spins up 10–100 AI agents, each with different expertise, reasoning habits, and risk tolerance
3. Runs a multi-round debate where agents post, reply, challenge each other, and change their minds when they see better arguments
4. A separate report agent (not part of the debate) reads the full transcript and writes a prediction with confidence levels

Every stance shift is logged with the triggering argument. You can read the full debate, see who changed their mind, and ask follow-up questions after.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       Frontend                          │
│                  Vue 3 + Vite + D3.js                   │
│                                                         │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Home    │  │  Project     │  │  Wiki             │  │
│  │  View    │  │  Results     │  │  (Architecture)   │  │
│  └────┬─────┘  └──────┬───────┘  └───────────────────┘  │
│       │               │                                  │
│       │    ┌──────────┴──────────┐                       │
│       │    │  SwarmGraph (D3)    │                       │
│       │    │  Force-directed     │                       │
│       │    │  network viz        │                       │
│       │    └─────────────────────┘                       │
│       │                                                  │
│  ┌────┴────────────────────────────────────────────┐     │
│  │              HTTP Client (api/)                 │     │
│  └────────────────────┬───────────────────────────-┘     │
└───────────────────────┼─────────────────────────────────┘
                        │ HTTP / JSON
┌───────────────────────┼─────────────────────────────────┐
│                       │         Backend                  │
│              Flask (threaded, :5001)                      │
│                       │                                  │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │                 API Routes (api/)                  │  │
│  │  POST /predict, GET /status, POST /chat, etc.     │  │
│  └────────────────────┬───────────────────────────────┘  │
│                       │                                  │
│  ┌────────────────────┴───────────────────────────────┐  │
│  │              Service Layer (services/)             │  │
│  │                                                    │  │
│  │  ┌──────────────────┐  ┌────────────────────────┐  │  │
│  │  │ OntologyGenerator│  │ GraphBuilder            │  │  │
│  │  │ Infers entity &  │  │ Extracts entities &    │  │  │
│  │  │ relation types   │  │ relationships, builds  │  │  │
│  │  │ from raw text    │──│ KnowledgeGraph object  │  │  │
│  │  └──────────────────┘  └────────────┬───────────┘  │  │
│  │                                     │              │  │
│  │  ┌──────────────────┐               │              │  │
│  │  │ AgentGenerator   │◄──────────────┘              │  │
│  │  │ Creates N agent  │                              │  │
│  │  │ profiles from    │                              │  │
│  │  │ graph entities + │                              │  │
│  │  │ extra archetypes │                              │  │
│  │  └────────┬─────────┘                              │  │
│  │           │                                        │  │
│  │  ┌────────┴─────────┐                              │  │
│  │  │SimulationEngine  │                              │  │
│  │  │ Runs in a daemon │                              │  │
│  │  │ thread. Each     │                              │  │
│  │  │ agent is an LLM  │                              │  │
│  │  │ persona that     │                              │  │
│  │  │ reads the feed,  │                              │  │
│  │  │ posts, replies,  │                              │  │
│  │  │ shifts stance    │                              │  │
│  │  └────────┬─────────┘                              │  │
│  │           │                                        │  │
│  │  ┌────────┴─────────┐                              │  │
│  │  │ ReportAgent      │                              │  │
│  │  │ Reads full       │                              │  │
│  │  │ transcript,      │                              │  │
│  │  │ writes Markdown  │                              │  │
│  │  │ report. Also     │                              │  │
│  │  │ handles post-    │                              │  │
│  │  │ simulation chat  │                              │  │
│  │  └──────────────────┘                              │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │                 Utilities (utils/)                 │  │
│  │  LLM Client (OpenAI + Anthropic, retry w/backoff) │  │
│  │  Logger (structured, file rotation)               │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Models (models/)                      │  │
│  │  KnowledgeGraph: in-memory graph with entities,   │  │
│  │  relationships, adjacency tracking, type counts   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## The Pipeline

Every prediction goes through five stages. Output from each stage feeds into the next.

### Stage 1: Document Ingestion

Takes PDF, Markdown, or plain text. PDFs are parsed with PyMuPDF. Full text is kept as-is, no summarisation. Truncated at ~12,000 characters to fit context windows.

### Stage 2: Ontology Detection

The `OntologyGenerator` sends the text and prediction goal to the LLM and asks it to identify what types of actors exist in the data (people, companies, regulatory bodies, etc.) and what types of relationships connect them (acquired, regulates, competes with, etc.).

This step produces a schema, not data. It defines 4–6 entity types and 3–5 relationship types. The schema is inferred from the input, not predefined. Person and Organization are always included as fallbacks.

Output format:
```json
{
  "entity_types": [{"name": "Company", "description": "Business entity"}],
  "edge_types": [{"name": "ACQUIRED", "description": "Corporate acquisition"}],
  "analysis_summary": "One-line description of the source material"
}
```

### Stage 3: Knowledge Graph Extraction

The `GraphBuilder` takes the schema and the raw text, sends both to the LLM in one call, and pulls out concrete entities and relationships.

Each entity gets a name, type, and one-line summary. Relationships are directional: "Company A → ACQUIRED → Company B". Everything goes into an in-memory `KnowledgeGraph` object that tracks adjacency (outgoing/incoming edges per entity).

If extraction returns zero entities, it retries with a simpler prompt. If that also fails, it creates four default archetypes (Government Official, Industry Leader, Public Advocate, Independent Analyst) so the simulation can still run.

The graph does two things:
1. Gives agents shared facts so they argue about interpretation, not about what happened
2. Decides what kinds of agents get created next

### Stage 4: Agent Generation

The `AgentGenerator` creates agent profiles. Each agent gets:

- **Entity type** — drawn from the knowledge graph (Person, Organization, Analyst, etc.)
- **Username and bio** — a specific background, not generic filler
- **Personality** — analytical, emotional, contrarian, pragmatic, idealistic, skeptical
- **Stance** — supportive, opposing, neutral, or cautious
- **Activity level** — 0.0 to 1.0, controls how often they participate
- **Influence** — 0.0 to 1.0, affects how other agents weight their arguments

Profiles are first generated from entities in the knowledge graph. If that produces fewer agents than the target count, a second LLM call generates additional stakeholder archetypes (journalists, academics, lobbyists, affected citizens, industry insiders). Duplicates are filtered by name.

### Stage 5: Multi-Round Simulation

The `SimulationEngine` runs in a daemon thread. Each round:

1. **Agent selection** — A scoring function picks who goes this round. Agents connected to recent posters score higher. Agents who haven't posted yet get a bonus. Random noise keeps it non-deterministic.

2. **Per-agent LLM call** — Each selected agent receives a system prompt defining its persona, the last ~3,000 characters of the feed, its own memory (last 5 posts), and its known connections. The agent returns JSON with its post content, who it's replying to (if anyone), its current stance, and a one-sentence reason for that stance.

3. **Stance tracking** — If an agent's stance differs from its previous stance, the shift is logged with the old position, new position, triggering round, and stated reason.

4. **Feed update** — New posts are appended to a running text feed in the format `[R3] AgentName (replying to @OtherAgent): content`. This feed is what subsequent agents read.

After all rounds complete, agents are grouped into final stance clusters.

### Stage 6: Consensus Report

The `ReportAgent` reads the complete debate transcript (up to 8,000 characters of gathered facts including posts, stance shifts, and cluster data) and generates a Markdown report covering:

- Executive summary (2–3 sentences)
- Key findings from the debate
- Points of agreement and disagreement
- Risk factors identified by agents
- Overall prediction with confidence assessment

The report agent did not participate in the debate. It just reads and summarises.

After the report, you can ask follow-up questions. The chat has access to the full simulation data and keeps the last 10 messages of context.

---

## Backend Services

| File | Responsibility |
|------|---------------|
| `ontology_generator.py` | Infers entity/relationship types from raw text. Single LLM call, temperature 0.3. |
| `graph_builder.py` | Extracts entities and relationships. Runs async in a daemon thread. Tracks progress with status callbacks. |
| `agent_generator.py` | Creates agent profiles in batch. Two-phase: first from graph entities, then fills remaining slots with archetypes. |
| `simulation_engine.py` | Runs the multi-round debate. Each agent is an independent LLM persona. Manages feed state, stance history, and cluster computation. |
| `report_agent.py` | Generates the final Markdown report. Also handles post-simulation Q&A chat. |

---

## Frontend Structure

The frontend is a Vue 3 SPA built with Vite.

| Directory | Contents |
|-----------|----------|
| `views/` | Three views — Home (input form), Project (results with report + graph), Wiki (architecture explainer) |
| `components/` | `SwarmGraph` — D3.js force-directed network graph. Node size scales with post count. Reply edges are thick, co-participation edges are thin. Zoom/pan enabled. |
| `api/` | HTTP client wrapper for backend communication |
| `router/` | Vue Router config |
| `assets/` | CSS and static images |

The graph visualisation works like this:
- Each agent is a node, coloured by entity type
- Node radius scales with number of posts (more active agents are bigger)
- A solid edge means one agent replied to another
- A faint edge means two agents participated in the same round
- Zoom and pan are handled by D3's zoom behavior

---

## Data Flow

```
User input (text/file/URL + prediction question)
  │
  ▼
OntologyGenerator.generate()
  │  → LLM call: "what types of things are in this data?"
  │  → returns schema {entity_types, edge_types}
  │
  ▼
GraphBuilder.build_async()
  │  → runs in daemon thread
  │  → LLM call: "extract concrete entities using this schema"
  │  → populates KnowledgeGraph (in-memory, maps + adjacency sets)
  │
  ▼
AgentGenerator.generate_profiles()
  │  → LLM call: "create personas from these entities"
  │  → if count < target: second LLM call for more archetypes
  │  → deduplicates, assigns IDs
  │
  ▼
SimulationEngine.start()
  │  → daemon thread
  │  → for each round:
  │      → score and select agents
  │      → for each selected agent:
  │          → LLM call with persona prompt + feed + memory
  │          → parse JSON response (post, stance, reply target)
  │          → track stance shifts
  │      → append posts to feed
  │  → compute final stance clusters
  │
  ▼
ReportAgent.generate_full_report()
  │  → gathers facts from simulation output
  │  → LLM call: "write a prediction report from this debate"
  │  → returns Markdown
  │
  ▼
User reads report, asks follow-up questions
  │  → ReportAgent.chat() with full simulation context
```

---

## LLM Integration

The `LLM` class in `utils/llm_client.py` supports two provider types:

**Anthropic Claude** — detected by `sk-ant-` key prefix or `LLM_PROVIDER=anthropic` env var. Uses the `anthropic` Python SDK directly. System messages are separated and passed via the `system` parameter. Ensures message alternation (user/assistant) as required by the Claude API.

**OpenAI-compatible** — anything else. Uses the `openai` Python SDK with a configurable `base_url`. This covers OpenAI, Gemini, Groq, Mistral, Together, OpenRouter, and DeepSeek — any provider that implements the OpenAI chat completions format.

Both paths include:
- Automatic retry with exponential backoff (up to 5 retries)
- Rate limit detection (429 status, "rate" in error message, "overloaded" for Anthropic)
- Retry-After header parsing when available
- `<think>` tag stripping (for models that emit chain-of-thought internally)

The `complete_json()` method wraps `complete()` and attempts to parse JSON from the response. It handles markdown fence stripping, finds JSON objects or arrays in messy output, and falls back to `{}` if parsing fails entirely.

---

## Simulation Mechanics

### Agent Selection

Each round, a subset of agents is selected for participation. Selection is scored:

- **Connection bonus (+0.5)**: agents linked to recent posters are more likely to go next. Discussions follow the graph.
- **First-post bonus (+0.3)**: agents who haven't spoken yet get priority. Stops the same few from dominating.
- **Random noise (+0.0–0.3)**: keeps things non-deterministic.

Top-scoring agents up to the `agents_per_round` limit are selected.

### Agent Persona Prompt

Each agent's system prompt is built from a template:

```
You are {name}, a {entity_type}.
Background: {bio}
Personality: {personality}
Your initial stance on the topic: {stance}

You are participating in a social media discussion about: "{topic}"
```

The agent sees the last ~3,000 characters of the feed, its own last 5 posts (memory), and its known connections. It returns JSON: `{post, reply_to, current_stance, stance_reason}`.

### Stance Shifts

When an agent's returned `current_stance` differs from its previous stance, the engine logs:
- Agent name
- Round number
- Previous stance → new stance
- Agent's stated reason for the change

This logs how opinions changed during the debate.

### Cluster Computation

After all rounds, agents are grouped by final stance. You see how many ended up supportive, opposing, or neutral, and who is in each group.

---

## Depth Presets

| Preset | Agents | Rounds | Agents/Round | Approx. Time | LLM Calls (rough) |
|--------|--------|--------|-------------|---------------|-------------------|
| Quick | 10 | 4 | 4 | ~1 min | ~25 |
| Balanced | 30 | 8 | 6 | ~3 min | ~60 |
| Deep | 50 | 12 | 8 | ~8 min | ~110 |
| Maximum | 100 | 16 | 10 | ~15 min | ~180 |

LLM call count = ontology (1) + graph (1) + agent gen (1–2) + simulation (agents_per_round × rounds) + report (1). The simulation phase dominates.

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | Vue 3, Vite | SPA with hot reload. |
| Backend | Python 3, Flask | Threaded mode for running simulations concurrently. |
| Graph vis | D3.js | Force-directed graph with zoom, pan, dynamic node sizing. |
| PDF parsing | PyMuPDF (fitz) | Text extraction from uploaded PDFs. |
| LLM SDK | `openai` + `anthropic` | Direct SDK calls with retry. No LangChain. |
| Config | python-dotenv | Loads `.env` into env vars. |
| CORS | flask-cors | Lets frontend on :3000 talk to backend on :5001. |

---

## Project Structure

```
vedang-swarm-prediction/
├── backend/
│   ├── run.py                         # Entry point. Starts Flask on :5001
│   ├── app/
│   │   ├── __init__.py                # build_app() — Flask app factory
│   │   ├── config.py                  # Settings class, reads .env
│   │   ├── api/                       # Route handlers
│   │   │   └── *.py                   # /predict, /status, /chat endpoints
│   │   ├── models/
│   │   │   └── knowledge_graph.py     # KnowledgeGraph class: entities, relationships, adjacency
│   │   ├── services/
│   │   │   ├── ontology_generator.py  # Infers entity/relation types from text
│   │   │   ├── graph_builder.py       # Extracts entities, builds graph (async, threaded)
│   │   │   ├── agent_generator.py     # Creates agent profiles in batch
│   │   │   ├── simulation_engine.py   # Multi-round debate engine (daemon thread)
│   │   │   └── report_agent.py        # Writes prediction report + handles Q&A chat
│   │   └── utils/
│   │       ├── llm_client.py          # LLM class: OpenAI + Anthropic, retry, JSON parsing
│   │       └── logger.py              # Structured logging with rotation
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.js                    # Vue app bootstrap
│   │   ├── App.vue                    # Root component
│   │   ├── views/                     # Home, Project results, Wiki pages
│   │   ├── components/                # SwarmGraph (D3 force-directed graph)
│   │   ├── api/                       # HTTP client
│   │   ├── router/                    # Vue Router
│   │   └── assets/                    # CSS, images
│   └── package.json
├── .env.example
├── .gitignore
└── package.json
```

---

## Running Locally

```bash
git clone https://github.com/vedangvatsa123/vedang-swarm-prediction.git
cd vedang-swarm-prediction

# Backend
cp .env.example .env
# Edit .env — set LLM_API_KEY, optionally change LLM_PROVIDER and LLM_MODEL_NAME

cd backend
pip install -r requirements.txt
python run.py
# Runs on http://localhost:5001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

Open [http://localhost:3000](http://localhost:3000).

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | (none) | Your API key. Required. |
| `LLM_PROVIDER` | `openai` | `openai` or `anthropic`. OpenAI-compatible covers Gemini, Groq, Mistral, Together, OpenRouter, DeepSeek. |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | API endpoint. Change this for non-OpenAI providers (e.g., `https://api.groq.com/openai/v1`). |
| `LLM_MODEL_NAME` | `gpt-4o-mini` | Model to use for all LLM calls. |
| `FLASK_DEBUG` | `True` | Flask debug mode. |
| `FLASK_HOST` | `0.0.0.0` | Bind address. |
| `FLASK_PORT` | `5001` | Backend port. |
| `SECRET_KEY` | `vedang-dev-key` | Flask secret key. Change in production. |

---

## Security Model

- **API keys** stay in your browser's local storage. They are sent over HTTPS to the backend, used for LLM calls, then dropped from memory. Never written to disk. Never logged.
- **Input data** is processed in memory during the prediction run. Nothing persists after the process finishes. No database, no user accounts, no tracking.
- **Simulation state** is held in Python dicts keyed by simulation ID. State is garbage-collected when the process ends.
- Max upload size is 50 MB.

---

## Limitations

- **Input quality matters.** Vague data produces vague predictions. Give it specific, relevant text and a clear question.
- **LLM constraints apply.** Agents inherit whatever training cutoffs, knowledge gaps, and reasoning quirks the underlying model has.
- **Not calibrated.** Unlike prediction markets where real money creates accountability, there is no feedback loop from real outcomes. Treat the confidence numbers as relative rankings, not calibrated probabilities.
- **Cost scales with depth.** A Maximum run (100 agents, 16 rounds) makes roughly 180 LLM calls. Start with Quick or Balanced to test before running deep simulations.
- **Context window limits.** Text is truncated to ~12,000 characters for graph extraction and ~3,000 characters for the simulation feed window. Very long documents lose tail content.
