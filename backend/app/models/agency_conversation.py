"""
AI conversation model for the autonomous chat closer.
Each AgencyConversation represents one Claude Sonnet conversation thread
with a lead — from first discovery question through to closing.
"""

import uuid
from datetime import datetime

from ..extensions import db


class AgencyConversation(db.Model):
    __tablename__ = 'agency_conversations'

    id         = db.Column(db.String(36), primary_key=True,
                           default=lambda: str(uuid.uuid4()))
    lead_id    = db.Column(db.String(36), db.ForeignKey('agency_leads.id'),
                           nullable=False, index=True)

    # Full message history — list of {"role": "assistant"|"user", "content": str, "timestamp": ISO}
    messages   = db.Column(db.JSON, default=list)

    stage      = db.Column(db.String(50), default='discovery')
    # discovery | qualifying | pitching | objections | closing | won | lost

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    lead = db.relationship('OutreachLead', back_populates='conversations')

    def to_dict(self, include_messages: bool = True) -> dict:
        d = {
            'id': self.id,
            'lead_id': self.lead_id,
            'stage': self.stage,
            'message_count': len(self.messages or []),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_messages:
            d['messages'] = self.messages or []
        return d
