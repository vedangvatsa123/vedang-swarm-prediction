"""
Pipeline API
Single endpoint that runs the entire flow:
ontology -> graph -> agents (30+) -> real multi-agent simulation -> report
"""
import uuid
import threading
from flask import request, jsonify, Blueprint

from ..models import project as proj_store
from ..utils.file_parser import extract_multiple
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilder, get_graph, get_build_progress, _graphs, _lock
from ..services.agent_generator import AgentGenerator
from ..services.simulation_engine import SimulationEngine, get_sim_state
from ..services.report_agent import ReportAgent

pipeline_bp = Blueprint("pipeline", __name__)

_pipeline_status: dict = {}


def get_pipeline_status(project_id: str):
    return _pipeline_status.get(project_id)


@pipeline_bp.route("/start", methods=["POST"])
def start_pipeline():
    """Upload files + run entire pipeline in background."""
    import os
    from ..config import Settings

    files = request.files.getlist("files")
    goal = request.form.get("prediction_goal", "").strip()

    if not files:
        return jsonify(success=False, error="No files uploaded"), 400
    if not goal:
        return jsonify(success=False, error="prediction_goal is required"), 400

    allowed = Settings.ALLOWED_EXTENSIONS
    for f in files:
        ext = os.path.splitext(f.filename or "")[1].lstrip(".").lower()
        if ext not in allowed:
            return jsonify(success=False, error=f"Unsupported file type: .{ext}"), 400

    name = request.form.get("project_name", "").strip() or "New Project"
    project = proj_store.create_project(name)
    pid = project["project_id"]

    saved = []
    for f in files:
        info = proj_store.save_uploaded_file(pid, f, f.filename)
        saved.append(info)

    proj_store.update_project(pid, {"files": saved, "prediction_goal": goal})

    paths = proj_store.get_project_files(pid)
    full_text = extract_multiple(paths)
    proj_store.save_extracted_text(pid, full_text)

    # User-provided API key (BYOK)
    user_api_key = request.form.get("api_key", "").strip() or None
    user_api_provider = request.form.get("api_provider", "").strip() or None

    _pipeline_status[pid] = {
        "phase": "starting",
        "progress": 0,
        "message": "Documents uploaded, starting analysis...",
    }

    t = threading.Thread(
        target=_run_pipeline,
        args=(pid, full_text, goal),
        kwargs={"api_key": user_api_key, "api_provider": user_api_provider},
        daemon=True,
    )
    t.start()

    return jsonify(success=True, project_id=pid)


@pipeline_bp.route("/status/<project_id>", methods=["GET"])
def pipeline_status(project_id: str):
    status = _pipeline_status.get(project_id)
    if not status:
        return jsonify(success=False, error="Not found"), 404
    return jsonify(success=True, **status)


def _run_pipeline(pid: str, text: str, goal: str, api_key: str = None, api_provider: str = None):
    """Runs ontology -> graph -> agents -> simulation -> report."""
    status = _pipeline_status[pid]

    try:
        from ..utils.llm_client import LLM

        # Build LLM with user key if provided — key is never logged or saved
        llm_kwargs = {}
        if api_key:
            llm_kwargs["api_key"] = api_key

            provider_config = {
                "anthropic": {"model": "claude-sonnet-4-20250514"},
                "openai": {"model": "gpt-4o-mini", "base_url": "https://api.openai.com/v1"},
                "gemini": {"model": "gemini-2.0-flash", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/"},
                "groq": {"model": "llama-3.1-70b-versatile", "base_url": "https://api.groq.com/openai/v1"},
                "mistral": {"model": "mistral-large-latest", "base_url": "https://api.mistral.ai/v1"},
                "together": {"model": "meta-llama/Llama-3-70b-chat-hf", "base_url": "https://api.together.xyz/v1"},
                "openrouter": {"model": "anthropic/claude-sonnet-4-20250514", "base_url": "https://openrouter.ai/api/v1"},
                "deepseek": {"model": "deepseek-chat", "base_url": "https://api.deepseek.com/v1"},
            }

            cfg = provider_config.get(api_provider, provider_config["anthropic"])
            llm_kwargs["model"] = cfg["model"]
            if "base_url" in cfg:
                llm_kwargs["base_url"] = cfg["base_url"]

        llm = LLM(**llm_kwargs)

        # Immediately clear key from local scope — defense in depth
        api_key = None

        # 1. Ontology
        status.update(phase="ontology", progress=5, message="Analysing document structure...")
        gen = OntologyGenerator(llm)
        ontology = gen.generate([text], goal)
        proj_store.update_project(pid, {"ontology": ontology})

        # 2. Entity extraction
        status.update(phase="graph", progress=15, message="Extracting entities and relationships...")
        from ..models.knowledge_graph import KnowledgeGraph
        graph = KnowledgeGraph()
        graph_id = f"g_{uuid.uuid4().hex[:12]}"

        truncated = text[:12000] + "\n...(truncated)" if len(text) > 12000 else text
        type_names = [et["name"] for et in ontology.get("entity_types", [])]
        rel_names = [ed["name"] for ed in ontology.get("edge_types", [])]
        schema_desc = f"Entity types: {', '.join(type_names)}\nRelationship types: {', '.join(rel_names)}"

        extracted = llm.complete_json(
            messages=[
                {"role": "system", "content": "You are an entity and relationship extractor. Given text and a schema, extract ALL entities and relationships. Return JSON: {\"entities\": [{\"name\": \"...\", \"type\": \"...\", \"summary\": \"...\"}], \"relationships\": [{\"source\": \"...\", \"target\": \"...\", \"type\": \"...\", \"description\": \"...\"}]}"},
                {"role": "user", "content": f"## Schema\n{schema_desc}\n\n## Text\n{truncated}\n\nExtract all entities and relationships. Return JSON only."},
            ],
            temperature=0.2,
            max_tokens=4000,
        )

        name_to_uid = {}
        for ent in extracted.get("entities", []):
            n = ent.get("name", "").strip()
            if not n:
                continue
            key = n.lower()
            if key not in name_to_uid:
                e = graph.add_entity(n, ent.get("type", "Person"), ent.get("summary", ""))
                name_to_uid[key] = e.uid

        for rel in extracted.get("relationships", []):
            s, t = rel.get("source", "").strip().lower(), rel.get("target", "").strip().lower()
            if name_to_uid.get(s) and name_to_uid.get(t):
                graph.add_relationship(name_to_uid[s], name_to_uid[t], rel.get("type", "RELATED_TO"), rel.get("description", ""))

        # Fallback if no entities
        if len(graph.entities) == 0:
            status.update(message="Retrying entity extraction...")
            fallback = llm.complete_json(
                messages=[
                    {"role": "system", "content": "List the people, organizations, and groups mentioned in this text. Return JSON: {\"entities\": [{\"name\": \"...\", \"type\": \"Person or Organization\", \"summary\": \"one sentence\"}]}"},
                    {"role": "user", "content": truncated[:4000]},
                ],
                temperature=0.3,
                max_tokens=1500,
            )
            for ent in fallback.get("entities", []):
                n = ent.get("name", "").strip()
                if n and n.lower() not in name_to_uid:
                    e = graph.add_entity(n, ent.get("type", "Person"), ent.get("summary", ""))
                    name_to_uid[n.lower()] = e.uid

        # Last resort fallback
        if len(graph.entities) == 0:
            defaults = [
                ("Government Official", "Person", "A government representative involved in this scenario"),
                ("Industry Leader", "Organization", "A key business or industry stakeholder"),
                ("Public Advocate", "Person", "A voice representing public interest"),
                ("Independent Analyst", "Person", "An independent expert analyzing the situation"),
            ]
            for name, etype, summary in defaults:
                e = graph.add_entity(name, etype, summary)
                name_to_uid[name.lower()] = e.uid

        with _lock:
            _graphs[graph_id] = graph
        proj_store.update_project(pid, {"graph_id": graph_id})

        status.update(
            phase="agents", progress=25,
            message=f"Found {len(graph.entities)} entities. Generating 30+ agent profiles...",
        )

        # 3. Agents (target 30)
        agent_gen = AgentGenerator(llm)
        profiles = agent_gen.generate_profiles(
            graph, goal, target_count=30,
            progress_cb=lambda i, t, m: status.update(
                progress=25 + int((i / max(t, 1)) * 15),
                message=m,
            ),
        )

        # 4. Real multi-agent simulation
        sim_id = f"sim_{uuid.uuid4().hex[:12]}"
        proj_store.update_project(pid, {"sim_id": sim_id})

        total_rounds = 8
        agents_per_round = min(8, len(profiles))

        status.update(
            phase="simulation", progress=45,
            message=f"Starting simulation: {len(profiles)} agents, {total_rounds} rounds...",
        )

        engine = SimulationEngine(llm)
        engine.start(
            sim_id=sim_id,
            profiles=profiles,
            graph=graph,
            prediction_goal=goal,
            total_rounds=total_rounds,
            agents_per_round=agents_per_round,
            initial_prompt=goal,
        )

        # Poll simulation progress
        import time
        while True:
            sim_state = get_sim_state(sim_id)
            if sim_state and sim_state["status"] in ("completed", "failed"):
                break
            if sim_state:
                rnd = sim_state.get("current_round", 0)
                total = sim_state.get("total_rounds", total_rounds)
                post_count = len(sim_state.get("posts", []))
                status.update(
                    progress=45 + int((rnd / max(total, 1)) * 35),
                    message=f"Round {rnd}/{total}, {post_count} posts so far...",
                )
            time.sleep(2)

        if sim_state["status"] == "failed":
            raise Exception("Simulation failed: " + (sim_state.get("error") or "unknown"))

        # 5. Report
        status.update(phase="report", progress=85, message="Writing prediction report...")

        sim_summary = {
            "agent_count": len(profiles),
            "total_rounds": sim_state.get("total_rounds", 0),
            "post_count": len(sim_state.get("posts", [])),
            "posts": sim_state.get("posts", []),
            "actions": sim_state.get("actions", []),
            "stance_shifts": sim_state.get("stance_shifts", []),
            "clusters": sim_state.get("clusters", {}),
        }

        reporter = ReportAgent(llm)
        report = reporter.generate_full_report(goal, sim_summary, graph)

        status.update(
            phase="done",
            progress=100,
            message="Complete",
            report_markdown=report["markdown"],
            report_outline=report.get("outline", {}),
            entity_count=len(graph.entities),
            relationship_count=len(graph.relationships),
            agent_count=len(profiles),
            post_count=len(sim_state.get("posts", [])),
            posts=sim_state.get("posts", []),
            profiles=profiles,
            stance_shifts=sim_state.get("stance_shifts", []),
            clusters=sim_state.get("clusters", {}),
            sim_id=sim_id,
            graph_id=graph_id,
        )

    except Exception as exc:
        import traceback
        traceback.print_exc()
        status.update(phase="failed", progress=0, message=str(exc))
