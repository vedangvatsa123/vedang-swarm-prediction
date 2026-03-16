"""API route blueprints."""
from flask import Blueprint

graph_bp = Blueprint("graph", __name__)
simulation_bp = Blueprint("simulation", __name__)
report_bp = Blueprint("report", __name__)

from . import graph as _g      # noqa: E402,F401
from . import simulation as _s  # noqa: E402,F401
from . import report as _r      # noqa: E402,F401
