"""
Graph API routes
Handles document upload, ontology generation, and knowledge-graph building.
"""
import os
import uuid
from flask import request, jsonify
from . import graph_bp
from ..config import Settings
from ..models import project as proj_store
from ..utils.file_parser import extract_multiple
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilder, get_graph, get_build_progress


@graph_bp.route("/upload", methods=["POST"])
def upload_and_analyse():
    """
    Upload files + prediction goal → create project + generate ontology.
    Form data: files[], prediction_goal, project_name (optional)
    """
    files = request.files.getlist("files")
    goal = request.form.get("prediction_goal", "").strip()

    if not files:
        return jsonify(success=False, error="No files uploaded"), 400
    if not goal:
        return jsonify(success=False, error="prediction_goal is required"), 400

    # Validate extensions
    allowed = Settings.ALLOWED_EXTENSIONS
    for f in files:
        ext = os.path.splitext(f.filename or "")[1].lstrip(".").lower()
        if ext not in allowed:
            return jsonify(success=False, error=f"Unsupported file type: .{ext}"), 400

    # Create project
    name = request.form.get("project_name", "").strip() or "New Project"
    project = proj_store.create_project(name)
    pid = project["project_id"]

    # Save files
    saved = []
    for f in files:
        info = proj_store.save_uploaded_file(pid, f, f.filename)
        saved.append(info)

    proj_store.update_project(pid, {"files": saved, "prediction_goal": goal})

    # Extract text
    paths = proj_store.get_project_files(pid)
    full_text = extract_multiple(paths)
    proj_store.save_extracted_text(pid, full_text)

    # Generate ontology
    gen = OntologyGenerator()
    ontology = gen.generate([full_text], goal)

    proj_store.update_project(pid, {
        "ontology": ontology,
        "analysis_summary": ontology.get("analysis_summary", ""),
        "status": "ontology_ready",
    })

    return jsonify(
        success=True,
        project_id=pid,
        ontology=ontology,
        analysis_summary=ontology.get("analysis_summary", ""),
        files_count=len(saved),
    )


@graph_bp.route("/build", methods=["POST"])
def build_graph():
    """
    Start building the knowledge graph.
    JSON body: { project_id }
    """
    data = request.get_json(force=True)
    pid = data.get("project_id", "")
    project = proj_store.load_project(pid)
    if not project:
        return jsonify(success=False, error="Project not found"), 404

    ontology = project.get("ontology")
    if not ontology:
        return jsonify(success=False, error="Ontology not generated yet"), 400

    text = proj_store.get_extracted_text(pid)
    if not text:
        return jsonify(success=False, error="No text found"), 400

    graph_id = f"g_{uuid.uuid4().hex[:12]}"
    builder = GraphBuilder()
    builder.build_async(graph_id, text, ontology)

    proj_store.update_project(pid, {"graph_id": graph_id, "status": "graph_building"})

    return jsonify(success=True, graph_id=graph_id)


@graph_bp.route("/build/status/<graph_id>", methods=["GET"])
def build_status(graph_id: str):
    """Poll graph-build progress."""
    progress = get_build_progress(graph_id)
    if not progress:
        return jsonify(success=False, error="Unknown graph_id"), 404
    return jsonify(success=True, **progress)


@graph_bp.route("/data/<graph_id>", methods=["GET"])
def graph_data(graph_id: str):
    """Return the full graph for visualisation."""
    g = get_graph(graph_id)
    if not g:
        return jsonify(success=False, error="Graph not built yet"), 404
    return jsonify(success=True, **g.to_dict())


@graph_bp.route("/project/<project_id>", methods=["GET"])
def get_project(project_id: str):
    """Return project metadata."""
    project = proj_store.load_project(project_id)
    if not project:
        return jsonify(success=False, error="Project not found"), 404
    return jsonify(success=True, project=project)
