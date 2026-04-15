"""
Agency client (business) model.
Stores the minimum data needed to generate personalised content.
GDPR: includes consent tracking and a deletion flag.
"""

import uuid
from datetime import datetime

from ..extensions import db


class AgencyClient(db.Model):
    __tablename__ = 'agency_clients'

    id               = db.Column(db.String(36), primary_key=True,
                                 default=lambda: str(uuid.uuid4()))
    user_id          = db.Column(db.Integer, db.ForeignKey('agency_users.id'),
                                 nullable=True, index=True)

    # ── Business identity ─────────────────────────────────────────────────────
    business_name    = db.Column(db.String(255), nullable=False)
    business_type    = db.Column(db.String(100))
    # Allowed values: gym | salon | restaurant | clinic | real_estate | other
    city             = db.Column(db.String(100))
    country          = db.Column(db.String(2), default='IE')  # ISO 3166-1 alpha-2
    email            = db.Column(db.String(255), nullable=False)

    # ── Brand voice (from onboarding form) ────────────────────────────────────
    tone             = db.Column(db.String(100))
    # Allowed: professional | friendly | bold | calm | playful
    target_audience  = db.Column(db.Text)
    competitors      = db.Column(db.Text)      # comma-separated business names
    brand_keywords   = db.Column(db.Text)      # comma-separated words/phrases

    # ── Social handles (optional — no auth tokens ever stored) ────────────────
    linkedin_url     = db.Column(db.String(500))
    instagram_handle = db.Column(db.String(100))
    facebook_page    = db.Column(db.String(500))

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status           = db.Column(db.String(50), default='onboarding')
    # onboarding | active | paused | churned
    plan             = db.Column(db.String(50), default='pilot')
    # pilot | retainer

    # ── GDPR ──────────────────────────────────────────────────────────────────
    gdpr_consent        = db.Column(db.Boolean, default=False)
    gdpr_consent_at     = db.Column(db.DateTime)
    data_deletion_requested = db.Column(db.Boolean, default=False)
    last_activity       = db.Column(db.DateTime, default=datetime.utcnow)

    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow,
                                 onupdate=datetime.utcnow)

    # ── Relationships ─────────────────────────────────────────────────────────
    user             = db.relationship('AgencyUser', back_populates='client')
    content_packages = db.relationship('ContentPackage', back_populates='client',
                                       cascade='all, delete-orphan',
                                       lazy='dynamic')

    def to_dict(self, include_sensitive: bool = False):
        d = {
            'id': self.id,
            'business_name': self.business_name,
            'business_type': self.business_type,
            'city': self.city,
            'country': self.country,
            'status': self.status,
            'plan': self.plan,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
        }
        if include_sensitive:
            d.update({
                'email': self.email,
                'tone': self.tone,
                'target_audience': self.target_audience,
                'competitors': self.competitors,
                'brand_keywords': self.brand_keywords,
                'linkedin_url': self.linkedin_url,
                'instagram_handle': self.instagram_handle,
                'facebook_page': self.facebook_page,
                'gdpr_consent': self.gdpr_consent,
            })
        return d
