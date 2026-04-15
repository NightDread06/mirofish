"""
Content package and individual post models.
A ContentPackage represents one 30-day calendar for a client.
ContentPost represents a single ready-to-publish social media post.
"""

import uuid
from datetime import datetime, date

from ..extensions import db


class ContentPackage(db.Model):
    __tablename__ = 'agency_content_packages'

    id           = db.Column(db.String(36), primary_key=True,
                             default=lambda: str(uuid.uuid4()))
    client_id    = db.Column(db.String(36), db.ForeignKey('agency_clients.id'),
                             nullable=False, index=True)
    task_id      = db.Column(db.String(36))   # TaskManager task_id for async tracking

    status       = db.Column(db.String(50), default='pending')
    # pending | generating | completed | failed

    month_label  = db.Column(db.String(7))    # "2026-04" format
    platforms    = db.Column(db.JSON, default=lambda: ['linkedin', 'instagram', 'facebook'])
    post_count   = db.Column(db.Integer, default=0)

    # Generation metadata
    model_used   = db.Column(db.String(100))
    tokens_used  = db.Column(db.Integer, default=0)
    generation_cost_eur = db.Column(db.Float, default=0.0)

    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error        = db.Column(db.Text)

    client = db.relationship('AgencyClient', back_populates='content_packages')
    posts  = db.relationship('ContentPost', back_populates='package',
                             cascade='all, delete-orphan',
                             order_by='ContentPost.day_number, ContentPost.platform')

    def to_dict(self, include_posts: bool = False):
        d = {
            'id': self.id,
            'client_id': self.client_id,
            'status': self.status,
            'month_label': self.month_label,
            'platforms': self.platforms,
            'post_count': self.post_count,
            'model_used': self.model_used,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
        }
        if include_posts:
            d['posts'] = [p.to_dict() for p in self.posts]
        return d


class ContentPost(db.Model):
    __tablename__ = 'agency_content_posts'

    id                 = db.Column(db.String(36), primary_key=True,
                                   default=lambda: str(uuid.uuid4()))
    package_id         = db.Column(db.String(36),
                                   db.ForeignKey('agency_content_packages.id'),
                                   nullable=False, index=True)

    platform           = db.Column(db.String(50))   # linkedin | instagram | facebook | twitter
    scheduled_date     = db.Column(db.Date)
    day_number         = db.Column(db.Integer)       # 1–30

    # Content fields
    post_copy          = db.Column(db.Text)
    hashtags           = db.Column(db.Text)          # space-separated
    call_to_action     = db.Column(db.Text)
    visual_description = db.Column(db.Text)          # Art direction note
    post_type          = db.Column(db.String(100))
    # promotional | educational | engagement | story

    is_approved        = db.Column(db.Boolean, default=False)
    revision_note      = db.Column(db.Text)

    package = db.relationship('ContentPackage', back_populates='posts')

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'day_number': self.day_number,
            'post_copy': self.post_copy,
            'hashtags': self.hashtags,
            'call_to_action': self.call_to_action,
            'visual_description': self.visual_description,
            'post_type': self.post_type,
            'is_approved': self.is_approved,
            'revision_note': self.revision_note,
        }
