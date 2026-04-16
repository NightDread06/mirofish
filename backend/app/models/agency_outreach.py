"""
Outreach campaign and lead models.
Campaigns hold AI-generated message templates (LinkedIn + email sequences).
Leads track the automated outreach funnel stages.
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

    # AI-generated LinkedIn templates (plain text, ready to copy-paste)
    connection_msg  = db.Column(db.Text)   # ≤ 300 chars LinkedIn connection note
    dm_template_1   = db.Column(db.Text)   # Initial DM after connecting
    dm_template_2   = db.Column(db.Text)   # Follow-up #1 (day 3)
    dm_template_3   = db.Column(db.Text)   # Follow-up #2 (day 7)
    loom_script     = db.Column(db.Text)   # 60-second video pitch script

    # AI-generated email sequence templates
    email_template_1_subject = db.Column(db.Text)
    email_template_1_body    = db.Column(db.Text)
    email_template_2_subject = db.Column(db.Text)
    email_template_2_body    = db.Column(db.Text)
    email_template_3_subject = db.Column(db.Text)
    email_template_3_body    = db.Column(db.Text)

    # Funnel metrics (updated automatically by scheduler)
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
            d['email_templates'] = {
                'step1': {
                    'subject': self.email_template_1_subject,
                    'body': self.email_template_1_body,
                },
                'step2': {
                    'subject': self.email_template_2_subject,
                    'body': self.email_template_2_body,
                },
                'step3': {
                    'subject': self.email_template_3_subject,
                    'body': self.email_template_3_body,
                },
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
    email         = db.Column(db.String(255))          # for automated email sequence

    # Lead source
    source        = db.Column(db.String(50), default='manual')
    # manual | google_maps | linkedin_script

    stage         = db.Column(db.String(50), default='imported')
    # imported | queued_message | connection_sent | connected | dm_sent
    # email_sequence | replied | booked | closed | rejected

    # Email sequence tracking
    email_sequence_step = db.Column(db.Integer, default=0)
    # 0=not started, 1=day0 sent, 2=day3 sent, 3=day7 sent
    email_sent_at       = db.Column(db.DateTime)

    notes         = db.Column(db.Text)
    added_at      = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    campaign      = db.relationship('OutreachCampaign', back_populates='leads')
    conversations = db.relationship('AgencyConversation', back_populates='lead',
                                    cascade='all, delete-orphan', lazy='dynamic')

    def to_dict(self, include_email: bool = False):
        d = {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'first_name': self.first_name,
            'business_name': self.business_name,
            'linkedin_url': self.linkedin_url,
            'city': self.city,
            'source': self.source,
            'stage': self.stage,
            'email_sequence_step': self.email_sequence_step,
            'email_sent_at': self.email_sent_at.isoformat() if self.email_sent_at else None,
            'notes': self.notes,
            'added_at': self.added_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
        if include_email:
            d['email'] = self.email
        return d
