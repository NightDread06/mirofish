"""
MiroFish — Unified production entry point.

Serves the built Vue frontend (frontend/dist/) AND the Flask API on a single
port so the entire platform is reachable from one URL.

Usage:
    cd /home/user/mirofish
    npm run build                       # build Vue → frontend/dist/
    cd backend
    SERVE_FRONTEND=true uv run python run_unified.py

Environment variables (all optional):
    FLASK_HOST               bind address  (default: 0.0.0.0)
    FLASK_PORT               port          (default: 3000)
    SERVE_FRONTEND           must be "true" for SPA serving
    FLASK_DEBUG              set "true" for debug mode
"""

import os
import sys

if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Tell Flask to serve the built Vue files
os.environ['SERVE_FRONTEND'] = 'true'

from app import create_app
from app.config import Config


def main():
    # Skip the simulation-module validation (LLM_API_KEY / ZEP_API_KEY).
    # Those keys are only needed when the social-simulation engine is used.
    # The agency module runs on its own CLAUDE_API_KEY.
    app = create_app()

    host  = os.environ.get('FLASK_HOST', '0.0.0.0')
    port  = int(os.environ.get('FLASK_PORT', 3000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    print(f"\n  MiroFish Agency Platform")
    print(f"  Running at  http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"  Agency site http://localhost:{port}/agency")
    print(f"  API health  http://localhost:{port}/health\n")

    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    main()
