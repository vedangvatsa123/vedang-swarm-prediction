"""
Report API routes
Handles report generation and interactive chat.
"""
from flask import request, jsonify
from . import report_bp
from ..models import project as proj_store
from ..services.graph_builder import get_graph
from ..services.simulation_engine import get_sim_state
from ..services.report_agent import ReportAgent

# In-memory report cache
_reports: dict = {}


@report_bp.route("/generate", methods=["POST"])
def generate_report():
    """
    Generate a prediction report.
    JSON body: { project_id, sim_id }
    """
    data = request.get_json(force=True)
    pid = data.get("project_id", "")
    sim_id = data.get("sim_id", "")

    project = proj_store.load_project(pid)
    if not project:
        return jsonify(success=False, error="Project not found"), 404

    sim_state = get_sim_state(sim_id)
    if not sim_state:
        return jsonify(success=False, error="Simulation not found"), 404

    graph_id = project.get("graph_id")
    graph = get_graph(graph_id) if graph_id else None
    if not graph:
        return jsonify(success=False, error="Graph not available"), 400

    goal = project.get("prediction_goal", "")

    sim_summary = {
        "agent_count": len(sim_state.get("posts", [])),
        "total_rounds": sim_state.get("total_rounds", 0),
        "post_count": len(sim_state.get("posts", [])),
        "posts": sim_state.get("posts", []),
        "actions": sim_state.get("actions", []),
    }

    agent = ReportAgent()
    result = agent.generate_full_report(goal, sim_summary, graph)

    report_id = f"rpt_{sim_id}"
    _reports[report_id] = result

    return jsonify(
        success=True,
        report_id=report_id,
        markdown=result["markdown"],
        outline=result["outline"],
    )


@report_bp.route("/<report_id>", methods=["GET"])
def get_report(report_id: str):
    """Fetch a previously generated report."""
    report = _reports.get(report_id)
    if not report:
        return jsonify(success=False, error="Report not found"), 404
    return jsonify(success=True, **report)


@report_bp.route("/chat", methods=["POST"])
def chat_with_report():
    """
    Interactive Q&A with the report agent.
    JSON body: { project_id, sim_id, question, history? }
    """
    data = request.get_json(force=True)
    pid = data.get("project_id", "")
    sim_id = data.get("sim_id", "")
    question = data.get("question", "").strip()
    history = data.get("history", [])

    if not question:
        return jsonify(success=False, error="question is required"), 400

    project = proj_store.load_project(pid)
    if not project:
        return jsonify(success=False, error="Project not found"), 404

    sim_state = get_sim_state(sim_id)
    if not sim_state:
        return jsonify(success=False, error="Simulation not found"), 404

    graph_id = project.get("graph_id")
    graph = get_graph(graph_id) if graph_id else None
    if not graph:
        return jsonify(success=False, error="Graph not available"), 400

    sim_summary = {
        "posts": sim_state.get("posts", []),
        "actions": sim_state.get("actions", []),
    }

    agent = ReportAgent()
    answer = agent.chat(question, sim_summary, graph, history)

    return jsonify(success=True, answer=answer)
