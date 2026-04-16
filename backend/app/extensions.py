"""
Flask extension singletons.

All extensions are instantiated here and initialized via .init_app(app)
inside the create_app() factory. Models import db from this module
to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)
scheduler = BackgroundScheduler(
    timezone='Europe/Dublin',
    job_defaults={'misfire_grace_time': 300, 'coalesce': True},
)
