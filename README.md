# Vedang

Swarm intelligence prediction engine. You give it data and a question. It spins up a bunch of AI agents, makes them argue about it, and gives you a prediction based on where they land.

Demo: https://veda.ng/swarm-prediction

![Knowledge Graph](frontend/src/assets/wiki-graph.png)

## What is this

If you ask one AI model to predict something, you get one opinion shaped by one set of biases. Ask it again, you get the same opinion worded differently. That's not useful.

This project creates 10 to 100 agents, each with different expertise, different reasoning habits, and different risk tolerances. They read your data, form opinions, argue with each other across multiple rounds, and change their minds when they hear better arguments. At the end, a separate agent reads the entire debate and writes a prediction report.

You can read every argument. You can see who flipped and why. You can ask follow-up questions after.

## The pipeline

1. **Ingest** - Upload files (PDF, MD, TXT), paste text, or give a URL. Nothing gets summarised. Full text goes in.
2. **Graph** - Pulls out entities and relationships from your data. Companies, people, events, policies, whatever is in there. Builds a knowledge graph.
3. **Agents** - Creates agents based on what's in the graph. Each one gets a domain, a reasoning style, a risk posture, and a starting opinion. Some are conservative, some are aggressive, some are contrarians.
4. **Debate** - Agents post analyses, reply to each other, challenge weak arguments. If an agent sees something convincing enough, it shifts its position. Every shift gets logged with reasoning.
5. **Report** - A neutral agent (not part of the debate) reads the transcript and writes a structured report. Majority view, minority view, who changed their mind, confidence level.

## Depth settings

| | Agents | Rounds | Time |
|---|--------|--------|------|
| Quick | 10 | 4 | ~1 min |
| Balanced | 30 | 8 | ~3 min |
| Deep | 50 | 12 | ~8 min |
| Maximum | 100 | 16 | ~15 min |

More agents and rounds means more of the problem space gets explored. Also means more API calls.

## Stack

- **Frontend**: Vue 3, Vite
- **Backend**: Python, Flask
- **LLM**: Bring your own key. Supports Anthropic, OpenAI, Gemini, Groq, Mistral, Together, OpenRouter, DeepSeek.
- **Graph**: D3.js force-directed visualisation

## Running it

```bash
git clone https://github.com/vedangvatsa123/vedang-swarm-prediction.git
cd vedang-swarm-prediction

# Backend
cp .env.example .env        # add your API key in here
cd backend
pip install -r requirements.txt
python run.py                # runs on :5001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                  # runs on :3000
```

Open `http://localhost:3000`.

## Structure

```
backend/
  app/
    api/          # route handlers
    models/       # project, knowledge graph
    services/     # the actual engine: agents, graph, simulation, report
    utils/        # llm client, logger, retry
  run.py

frontend/
  src/
    views/        # Home, Project results, Wiki
    components/   # Graph visualisation
    assets/       # styles, images
    api/          # http client
```

## Keys and data

Your API key stays in your browser's local storage. It gets sent over HTTPS when you run a prediction, used once, then dropped from memory. Never logged, never saved to disk.

Your input data lives in memory during the run. Nothing persists after.

## Caveats

- Bad input gives bad predictions. Be specific with your data and question.
- Agents are powered by LLMs, so they share whatever limitations those models have.
- The confidence numbers are relative, not calibrated against real outcomes.
- Maximum depth burns through API credits. Start with Quick or Balanced.
