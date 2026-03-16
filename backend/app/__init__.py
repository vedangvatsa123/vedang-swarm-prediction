"""
Vedang Backend — Flask application factory.
"""
from flask import Flask
from flask_cors import CORS
from .config import Settings


def build_app(settings_cls=Settings):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(settings_cls)
    app.config["MAX_CONTENT_LENGTH"] = settings_cls.MAX_UPLOAD_BYTES

    # Allow JSON to render unicode directly
    if hasattr(app, "json") and hasattr(app.json, "ensure_ascii"):
        app.json.ensure_ascii = False

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ---- register blueprints ----
    from .api import graph_bp, simulation_bp, report_bp
    from .api.pipeline import pipeline_bp

    app.register_blueprint(graph_bp, url_prefix="/api/graph")
    app.register_blueprint(simulation_bp, url_prefix="/api/simulation")
    app.register_blueprint(report_bp, url_prefix="/api/report")
    app.register_blueprint(pipeline_bp, url_prefix="/api/pipeline")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "Vedang Backend"}

    return app
