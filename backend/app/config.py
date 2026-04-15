"""
配置管理
统一从项目根目录的 .env 文件加载配置
"""

import os
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
# 路径: MiroFish/.env (相对于 backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # 如果根目录没有 .env，尝试加载环境变量（用于生产环境）
    load_dotenv(override=True)


class Config:
    """Flask配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # JSON配置 - 禁用ASCII转义，让中文直接显示（而不是 \uXXXX 格式）
    JSON_AS_ASCII = False
    
    # LLM配置（统一使用OpenAI格式）
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Zep配置
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
    # 文本处理配置
    DEFAULT_CHUNK_SIZE = 500  # 默认切块大小
    DEFAULT_CHUNK_OVERLAP = 50  # 默认重叠大小
    
    # OASIS模拟配置
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')
    
    # OASIS平台可用动作配置
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]
    
    # Report Agent配置
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    # ── Agency Module ──────────────────────────────────────────────────────────

    # SQLite DB for agency data (users, clients, content, outreach)
    # Stored inside the existing uploads/ volume so Docker picks it up automatically
    _AGENCY_DB_DIR = os.path.join(os.path.dirname(__file__), '../uploads/agency')
    AGENCY_DB_PATH = os.path.join(_AGENCY_DB_DIR, 'agency.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.abspath(AGENCY_DB_PATH)}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT — use a strong random secret in production
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'CHANGE-ME-IN-PRODUCTION-use-64-chars')
    JWT_ACCESS_TOKEN_EXPIRES = 3600       # 1 hour in seconds
    JWT_REFRESH_TOKEN_EXPIRES = 604800    # 7 days in seconds
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_SECURE = os.environ.get('FLASK_ENV', 'development') == 'production'
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_COOKIE_CSRF_PROTECT = False       # Disabled for API; CORS policy handles this

    # Claude API (Anthropic SDK — separate from the general OpenAI-compatible LLM)
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
    CLAUDE_BASE_URL = 'https://api.anthropic.com'
    CLAUDE_HAIKU_MODEL = 'claude-haiku-4-5-20251001'
    CLAUDE_SONNET_MODEL = 'claude-sonnet-4-6'

    # Agency admin credentials
    AGENCY_ADMIN_EMAIL = os.environ.get('AGENCY_ADMIN_EMAIL', 'admin@example.com')

    # GDPR: auto-purge inactive churned clients after this many days
    AGENCY_MAX_CONTENT_AGE_DAYS = int(os.environ.get('AGENCY_MAX_CONTENT_AGE_DAYS', '90'))

    # Rate limiting (in-memory for single-process; upgrade to Redis for multi-worker)
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_DEFAULT = '200 per day;50 per hour'

    # Allowed origins for agency CORS (comma-separated)
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000')

    # ── Email / SMTP ───────────────────────────────────────────────────────────
    SMTP_HOST      = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT      = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER      = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD  = os.environ.get('SMTP_PASSWORD', '')
    SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', 'ContentAgency.ai')

    # ── IMAP inbox polling ─────────────────────────────────────────────────────
    IMAP_HOST     = os.environ.get('IMAP_HOST', 'imap.gmail.com')
    IMAP_USER     = os.environ.get('IMAP_USER', '')
    IMAP_PASSWORD = os.environ.get('IMAP_PASSWORD', '')

    # ── Google Maps Places API ─────────────────────────────────────────────────
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

    # ── Buffer API ─────────────────────────────────────────────────────────────
    BUFFER_ACCESS_TOKEN = os.environ.get('BUFFER_ACCESS_TOKEN', '')
    # JSON dict mapping platform name → Buffer profile ID
    # e.g. '{"linkedin": "64abc...", "instagram": "64def...", "facebook": "64ghi..."}'
    BUFFER_PROFILE_IDS = os.environ.get('BUFFER_PROFILE_IDS', '{}')

    @classmethod
    def validate(cls):
        """验证必要配置"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY 未配置")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY 未配置")
        return errors

