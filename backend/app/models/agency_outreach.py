"""
Outreach campaign and lead models.
Campaigns hold AI-generated message templates.
Leads track the manual outreach funnel stages.
No LinkedIn/email credentials are ever stored here.
"""

import uuid
from datetime import datetime

from ..extensions import db


class OutreachCampaign(db.Model):
    __tablename__ = 'agency_campaigns'

    id              = db.Column(db.String(36), primary_key=True,
                                default=lambda: str(uuid.uuid4()))
    name            = db.Column(db.String(255), nullable=False)
    business_type   = db.Column(db.String(100))
    target_city     = db.Column(db.String(100))
    status          = db.Column(db.String(50), default='draft')
    # draft | active | paused | completed

    # AI-generated outreach templates (plain text, ready to copy-paste)
    connection_msg  = db.Column(db.Text)   # ≤ 300 chars LinkedIn connection note
    dm_template_1   = db.Column(db.Text)   # Initial DM after connecting
    dm_template_2   = db.Column(db.Text)   # Follow-up #1 (day 3)
    dm_template_3   = db.Column(db.Text)   # Follow-up #2 (day 7)
    loom_script     = db.Column(db.Text)   # 60-second video pitch script

    # Funnel metrics (manually updated via admin portal)
    leads_total     = db.Column(db.Integer, default=0)
    leads_connected = db.Column(db.Integer, default=0)
    leads_replied   = db.Column(db.Integer, default=0)
    leads_booked    = db.Column(db.Integer, default=0)
    leads_closed    = db.Column(db.Integer, default=0)

    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    leads = db.relationship('OutreachLead', back_populates='campaign',
                            cascade='all, delete-orphan', lazy='dynamic')

    def to_dict(self, include_templates: bool = True):
        d = {
            'id': self.id,
            'name': self.name,
            'business_type': self.business_type,
            'target_city': self.target_city,
            'status': self.status,
            'metrics': {
                'total': self.leads_total,
                'connected': self.leads_connected,
                'replied': self.leads_replied,
                'booked': self.leads_booked,
                'closed': self.leads_closed,
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_templates:
            d['templates'] = {
                'connection_msg': self.connection_msg,
                'dm_1': self.dm_template_1,
                'dm_2': self.dm_template_2,
                'dm_3': self.dm_template_3,
                'loom_script': self.loom_script,
            }
        return d


class OutreachLead(db.Model):
    __tablename__ = 'agency_leads'

    id            = db.Column(db.String(36), primary_key=True,
                              default=lambda: str(uuid.uuid4()))
    campaign_id   = db.Column(db.String(36), db.ForeignKey('agency_campaigns.id'),
                              nullable=False, index=True)

    # Minimal PII — only what is operationally needed
    first_name    = db.Column(db.String(100))
    business_name = db.Column(db.String(255))
    linkedin_url  = db.Column(db.String(500))
    city          = db.Column(db.String(100))

    stage         = db.Column(db.String(50), default='imported')
    # imported | connection_sent | connected | dm_sent | replied | booked | closed | rejected

    notes         = db.Column(db.Text)
    added_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    campaign = db.relationship('OutreachCampaign', back_populates='leads')

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'first_name': self.first_name,
            'business_name': self.business_name,
            'linkedin_url': self.linkedin_url,
            'city': self.city,
            'stage': self.stage,
            'notes': self.notes,
            'added_at': self.added_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
