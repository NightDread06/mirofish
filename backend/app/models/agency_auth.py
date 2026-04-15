"""
Agency user authentication model.
Stores email + hashed password only — no PII beyond email address.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from ..extensions import db


class AgencyUser(db.Model):
    __tablename__ = 'agency_users'

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(50), default='client')  # 'client' | 'admin'
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime)

    # One-to-one link to agency client profile
    client = db.relationship('AgencyClient', back_populates='user', uselist=False)

    def set_password(self, plaintext: str) -> None:
        self.password_hash = generate_password_hash(plaintext, method='pbkdf2:sha256:600000')

    def check_password(self, plaintext: str) -> bool:
        return check_password_hash(self.password_hash, plaintext)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }
