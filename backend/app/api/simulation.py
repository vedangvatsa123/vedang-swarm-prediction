"""
Simulation API routes
Handles agent generation, simulation running, and status queries.
"""
import uuid
from flask import request, jsonify
from . import simulation_bp
from ..models import project as proj_store
from ..services.graph_builder import get_graph
from ..services.agent_generator import AgentGenerator
from ..services.simulation_engine import SimulationEngine, get_sim_state


# In-memory store for profiles per simulation
_profiles_store: dict = {}


@simulation_bp.route("/prepare", methods=["POST"])
def prepare_simulation():
    """
    Generate agent profiles from the knowledge graph.
    JSON body: { project_id }
    Returns: agent profiles
    """
    data = request.get_json(force=True)
    pid = data.get("project_id", "")
    project = proj_store.load_project(pid)
    if not project:
        return jsonify(success=False, error="Project not found"), 404

    graph_id = project.get("graph_id")
    if not graph_id:
        return jsonify(success=False, error="Graph not built"), 400

    graph = get_graph(graph_id)
    if not graph:
        return jsonify(success=False, error="Graph not found in memory"), 400

    goal = project.get("prediction_goal", "")
    gen = AgentGenerator()
    profiles = gen.generate_profiles(graph, goal)

    sim_id = f"sim_{uuid.uuid4().hex[:12]}"
    _profiles_store[sim_id] = profiles

    proj_store.update_project(pid, {"sim_id": sim_id, "status": "sim_ready"})

    return jsonify(
        success=True,
        sim_id=sim_id,
        profiles=profiles,
        agent_count=len(profiles),
    )


@simulation_bp.route("/start", methods=["POST"])
def start_simulation():
    """
    Launch the multi-agent simulation.
    JSON body: { project_id, sim_id, total_rounds?, agents_per_round?, initial_prompt? }
    """
    data = request.get_json(force=True)
    pid = data.get("project_id", "")
    sim_id = data.get("sim_id", "")
    total_rounds = data.get("total_rounds", 20)
    agents_per_round = data.get("agents_per_round", 5)
    initial_prompt = data.get("initial_prompt", "")

    project = proj_store.load_project(pid)
    if not project:
        return jsonify(success=False, error="Project not found"), 404

    profiles = _profiles_store.get(sim_id)
    if not profiles:
        return jsonify(success=False, error="Profiles not found — run /prepare first"), 400

    graph_id = project.get("graph_id")
    graph = get_graph(graph_id) if graph_id else None
    if not graph:
        return jsonify(success=False, error="Graph not available"), 400

    goal = project.get("prediction_goal", "")
    engine = SimulationEngine()
    state = engine.start(
        sim_id=sim_id,
        profiles=profiles,
        graph=graph,
        prediction_goal=goal,
        total_rounds=total_rounds,
        agents_per_round=agents_per_round,
        initial_prompt=initial_prompt,
    )

    proj_store.update_project(pid, {"status": "sim_running"})

    return jsonify(success=True, sim_id=sim_id, status=state["status"])


@simulation_bp.route("/status/<sim_id>", methods=["GET"])
def simulation_status(sim_id: str):
    """Get current simulation state."""
    state = get_sim_state(sim_id)
    if not state:
        return jsonify(success=False, error="Simulation not found"), 404
    return jsonify(success=True, **state)


@simulation_bp.route("/profiles/<sim_id>", methods=["GET"])
def get_profiles(sim_id: str):
    """Return stored agent profiles."""
    profiles = _profiles_store.get(sim_id, [])
    return jsonify(success=True, profiles=profiles)
