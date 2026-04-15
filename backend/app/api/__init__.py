"""
API路由模块
"""

from flask import Blueprint

graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)

from . import graph  # noqa: E402, F401
from . import simulation  # noqa: E402, F401
from . import report  # noqa: E402, F401

# Agency module blueprints (imported from their own files, not created here)
from .agency_auth import agency_auth_bp  # noqa: E402, F401
from .agency_clients import agency_clients_bp  # noqa: E402, F401
from .agency_content import agency_content_bp  # noqa: E402, F401
from .agency_outreach import agency_outreach_bp  # noqa: E402, F401
from .agency_chat import agency_chat_bp  # noqa: E402, F401
from .agency_scheduler_api import agency_scheduler_bp  # noqa: E402, F401

