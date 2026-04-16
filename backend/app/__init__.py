"""
MiroFish Backend - Flask应用工厂
"""

import os
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 设置JSON编码：确保中文直接显示（而不是 \uXXXX 格式）
    # Flask >= 2.3 使用 app.json.ensure_ascii，旧版本使用 JSON_AS_ASCII 配置
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    # 设置日志
    logger = setup_logger('mirofish')

    # 只在 reloader 子进程中打印启动信息（避免 debug 模式下打印两次）
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend 启动中...")
        logger.info("=" * 50)

    # ── Flask extensions (agency module) ──────────────────────────────────────
    from .extensions import db, jwt, limiter

    # Ensure the agency DB directory exists before SQLAlchemy tries to create the file
    agency_db_dir = os.path.join(os.path.dirname(__file__), '../uploads/agency')
    os.makedirs(agency_db_dir, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    # Create all agency DB tables on first run (idempotent)
    with app.app_context():
        from .models.agency_auth import AgencyUser                           # noqa: F401
        from .models.agency_client import AgencyClient                       # noqa: F401
        from .models.agency_content import ContentPackage, ContentPost       # noqa: F401
        from .models.agency_outreach import OutreachCampaign, OutreachLead   # noqa: F401
        from .models.agency_conversation import AgencyConversation           # noqa: F401
        db.create_all()

    if should_log_startup:
        logger.info("Agency SQLite DB initialised")

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Existing simulation/graph/report APIs: open to all origins (unchanged)
    # Agency APIs: restricted to ALLOWED_ORIGINS for security
    allowed_origins = [o.strip() for o in
                       app.config.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')]
    CORS(app, resources={
        r"/api/graph/*":      {"origins": "*"},
        r"/api/simulation/*": {"origins": "*"},
        r"/api/report/*":     {"origins": "*"},
        r"/api/agency/*": {
            "origins":             allowed_origins,
            "supports_credentials": True,
            "allow_headers":       ["Content-Type", "Authorization"],
            "methods":             ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        },
    })

    # 注册模拟进程清理函数（确保服务器关闭时终止所有模拟进程）
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("已注册模拟进程清理函数")

    # ── Request / response hooks ──────────────────────────────────────────────

    @app.before_request
    def log_request():
        req_logger = get_logger('mirofish.request')
        req_logger.debug(f"请求: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            req_logger.debug(f"请求体: {request.get_json(silent=True)}")

    @app.after_request
    def add_security_headers(response):
        """Attach security headers to every response."""
        get_logger('mirofish.request').debug(f"响应: {response.status_code}")
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options']        = 'DENY'
        response.headers['X-XSS-Protection']       = '1; mode=block'
        response.headers['Referrer-Policy']        = 'strict-origin-when-cross-origin'
        return response

    # ── Blueprints ────────────────────────────────────────────────────────────

    # Existing simulation engine blueprints (unchanged)
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp,      url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp,     url_prefix='/api/report')

    # Agency module blueprints
    from .api import (agency_auth_bp, agency_clients_bp,
                      agency_content_bp, agency_outreach_bp,
                      agency_chat_bp, agency_scheduler_bp)
    app.register_blueprint(agency_auth_bp,      url_prefix='/api/agency/auth')
    app.register_blueprint(agency_clients_bp,   url_prefix='/api/agency/clients')
    app.register_blueprint(agency_content_bp,   url_prefix='/api/agency/content')
    app.register_blueprint(agency_outreach_bp,  url_prefix='/api/agency/outreach')
    app.register_blueprint(agency_chat_bp,      url_prefix='/api/agency/chat')
    app.register_blueprint(agency_scheduler_bp, url_prefix='/api/agency/scheduler')

    # ── Health check ──────────────────────────────────────────────────────────

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}

    # ── Autonomous scheduler ──────────────────────────────────────────────────
    # Start APScheduler only in the main process (not the Werkzeug reloader watcher)
    if not app.config.get('TESTING') and (
        not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    ):
        try:
            from .services.agency_scheduler import init_scheduler
            init_scheduler(app)
            if should_log_startup:
                logger.info("Autonomous scheduler started")
        except Exception as _sched_err:
            logger.warning(f"Scheduler could not start: {_sched_err}")

    # ── Serve Vue SPA (unified production mode) ───────────────────────────────
    # When SERVE_FRONTEND=true, Flask serves the built Vue dist folder so the
    # entire app (API + frontend) runs on a single port / URL.
    if os.environ.get('SERVE_FRONTEND', 'false').lower() == 'true':
        from flask import send_from_directory

        frontend_dist = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../frontend/dist')
        )

        if os.path.isdir(frontend_dist):
            if should_log_startup:
                logger.info(f"Serving Vue SPA from {frontend_dist}")

            @app.route('/', defaults={'path': ''})
            @app.route('/<path:path>')
            def serve_spa(path):
                """Catch-all: serve static asset if it exists, else return index.html."""
                import os as _os
                full = _os.path.join(frontend_dist, path)
                if path and _os.path.isfile(full):
                    return send_from_directory(frontend_dist, path)
                return send_from_directory(frontend_dist, 'index.html')
        else:
            logger.warning(
                f"SERVE_FRONTEND=true but dist not found at {frontend_dist}. "
                "Run `npm run build` first."
            )

    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")

    return app

