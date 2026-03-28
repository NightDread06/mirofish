"""
WSGI entry point for production deployment (gunicorn).
"""

import os
import sys

# Ensure the backend directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config import Config

errors = Config.validate()
if errors:
    for err in errors:
        print(f"Config error: {err}", file=sys.stderr)
    sys.exit(1)

app = create_app()
