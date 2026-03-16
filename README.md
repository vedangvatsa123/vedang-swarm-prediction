# Vedang - Swarm Intelligence Prediction Engine

A prediction engine that uses multiple AI agents with different perspectives to debate, challenge each other, and converge on calibrated forecasts. Instead of asking one AI model one question, this system creates a swarm of agents and makes them argue until they reach consensus.

![Knowledge Graph](frontend/src/assets/wiki-graph.png)

## Why This Exists

Most AI prediction tools ask a single model a single question and return a single answer. The problem is that one model carries one set of biases and blind spots. It cannot challenge itself. If it starts down the wrong reasoning path, nothing pulls it back.

This engine forces genuine disagreement. It creates agents with different expertise domains, reasoning styles, and risk tolerances, then makes them debate across multiple rounds. The final prediction comes from the group consensus, not from any single agent.

The approach borrows from:
- **Ensemble methods** in ML, where many weak learners outperform one strong learner
- **Prediction markets**, where aggregated independent judgments beat individual expert forecasts
- **Structured analytic techniques** from intelligence analysis, where red teams challenge assumptions

The key difference is that the reasoning is fully transparent. You can read every argument, see every stance shift, and judge the conclusion for yourself.

## How It Works

Every prediction runs through five stages:

### 1. Document Ingestion
Upload files (PDF, Markdown, plain text), paste text, or provide a URL. The input is parsed into a clean text corpus with structure preserved. No summarisation or lossy compression happens here.

### 2. Knowledge Graph Extraction
The engine builds a domain-specific knowledge graph from your input:
- **Ontology detection** identifies what types of things matter in your data (companies, people, events, policies, etc.)
- **Entity extraction** populates the ontology with specific instances and their relationships
- Relationships are directional and typed: "Company A acquired Company B", "Policy X responded to Event Y"

This graph becomes the shared factual foundation for all agents.

### 3. Agent Generation
Each agent is a purpose-built cognitive persona with:
- **Expertise domain** drawn from the knowledge graph's entity types
- **Reasoning style** (analytical, intuitive, contrarian, or synthesis-oriented)
- **Risk posture** (conservative to aggressive)
- **Initial stance** on the prediction question
- **Persuadability** (how much evidence it takes to change their mind)

Agent count scales with simulation depth: 10 (Quick) to 100 (Maximum).

### 4. Multi-Round Simulation
Agents debate across discrete rounds. Each agent can:
- Post original analyses based on their reading of the knowledge graph
- Reply to and challenge other agents' reasoning
- Shift their stance when presented with compelling counter-arguments

Every stance shift is logged with the old position, new position, triggering argument, and stated reason. This creates a full audit trail of how opinion evolved.

### 5. Consensus Report
A dedicated report agent (who did not participate in the debate) analyses the full transcript and produces:
- Majority and minority positions with supporting rationale
- Stance shift analysis showing who changed their mind and why
- Points of agreement and unresolved disagreements
- Risk factors identified by contrarian agents
- Final probabilistic assessment with confidence bounds

After the report, you can ask follow-up questions. The system has access to the full debate transcript, all agent profiles, and the knowledge graph.

## Simulation Depth Presets

| Preset | Agents | Rounds | Approx. Time |
|--------|--------|--------|-------------|
| Quick | 10 | 4 | ~1 minute |
| Balanced | 30 | 8 | ~3 minutes |
| Deep | 50 | 12 | ~8 minutes |
| Maximum | 100 | 16 | ~15 minutes |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue.js 3 + Vite |
| Backend | Python / Flask |
| LLM Support | 8 providers via BYOK |
| Graph Engine | Custom ontology extraction |
| Visualisation | Force-directed SVG (D3.js) |
| Logging | Structured with file rotation |

## Supported LLM Providers

Bring Your Own Key (BYOK) model. Use whichever provider you already have an API key for:

- Anthropic
- OpenAI
- Google Gemini
- Groq
- Mistral AI
- Together AI
- OpenRouter
- DeepSeek

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- An API key from any supported LLM provider

### Setup

**1. Clone the repo**
```bash
git clone https://github.com/vedangvatsa123/vedang-swarm-prediction.git
cd vedang-swarm-prediction
```

**2. Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API key
```

**3. Install and start the backend**
```bash
cd backend
pip install -r requirements.txt
python run.py
```
The backend runs on `http://localhost:5001`.

**4. Install and start the frontend**
```bash
cd frontend
npm install
npm run dev
```
The frontend runs on `http://localhost:3000`.

**5. Open the app**

Visit `http://localhost:3000` in your browser. Upload a document, describe what you want to predict, and start the simulation.

## Project Structure

```
vedang-swarm-prediction/
  backend/
    app/
      api/            # Flask route handlers
      models/         # Data models (project, knowledge graph)
      services/       # Core engine (agent gen, graph builder, simulation, report)
      utils/          # LLM client, logger, retry, file parser
    run.py            # Entry point
  frontend/
    src/
      assets/         # Styles, images
      components/     # SwarmGraph visualisation
      views/          # Home, Project results, Wiki
      router/         # Vue Router config
      api/            # API client
    index.html
```

## Security and Privacy

- API keys are stored only in your browser's local storage
- Keys are sent over HTTPS, used for one request, then deleted from server memory
- Keys are never logged, written to disk, or shared
- Input data is processed in memory and not retained after the prediction completes
- No user accounts, no tracking, no database of past predictions

## Limitations

- **Garbage in, garbage out.** Prediction quality depends on input data quality.
- **LLM constraints apply.** Agents inherit the knowledge cutoffs and reasoning limitations of the underlying models.
- **Not calibrated on real outcomes.** Unlike prediction markets, there is no feedback mechanism. Treat confidence percentages as relative indicators.
- **Cost scales with depth.** A maximum-depth run with 100 agents across 16 rounds consumes significant API credits.

## License

MIT
