"""
Outreach campaign management API.

POST /api/agency/outreach/campaign                           — Create campaign + generate templates
GET  /api/agency/outreach/campaign/<id>                      — Get campaign details + templates
PATCH /api/agency/outreach/campaign/<id>                     — Update campaign status / metrics
POST /api/agency/outreach/campaign/<id>/leads                — Import leads (from CSV data)
GET  /api/agency/outreach/campaign/<id>/leads                — List leads for a campaign
PATCH /api/agency/outreach/leads/<lead_id>                   — Update lead stage / notes
GET  /api/agency/outreach/campaigns                          — List all campaigns (admin)
POST /api/agency/outreach/personalise                        — Generate personalised opener for a lead
POST /api/agency/outreach/campaign/<id>/scout                — Run Google Maps scout immediately
POST /api/agency/outreach/campaign/<id>/email-sequence/start — Start email sequence for leads
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt

from ..extensions import db, limiter
from ..middleware.auth import require_auth, require_admin
from ..middleware.sanitize import sanitize_text, sanitize_dict
from ..models.agency_outreach import OutreachCampaign, OutreachLead
from ..services.agency_outreach_manager import AgencyOutreachManager
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.outreach')
agency_outreach_bp = Blueprint('agency_outreach', __name__)

_VALID_STATUSES = {'draft', 'active', 'paused', 'completed'}
_VALID_STAGES   = {
    'imported', 'queued_message', 'connection_sent', 'connected',
    'dm_sent', 'email_sequence', 'replied', 'booked', 'closed', 'rejected',
}


# ── Create campaign ────────────────────────────────────────────────────────────

@agency_outreach_bp.route('/campaign', methods=['POST'])
@require_admin
@limiter.limit('10 per hour')
def create_campaign():
    """
    Create a new outreach campaign and generate LinkedIn DM + email templates.
    Template generation calls Claude — takes a few seconds.
    """
    data = request.get_json(silent=True) or {}

    name          = sanitize_text(str(data.get('name', ''))).strip()
    business_type = sanitize_text(str(data.get('business_type', 'local business')))
    target_city   = sanitize_text(str(data.get('target_city', '')))

    if not name:
        return jsonify({'success': False, 'error': 'name is required'}), 400

    campaign = OutreachCampaign(
        name=name,
        business_type=business_type,
        target_city=target_city,
        status='draft',
    )
    db.session.add(campaign)
    db.session.flush()  # get the ID before committing

    manager = AgencyOutreachManager()

    # Generate LinkedIn templates
    try:
        linkedin = manager.generate_linkedin_sequence(business_type, target_city)
        campaign.connection_msg = linkedin.get('connection_request', '')[:300]
        campaign.dm_template_1  = linkedin.get('dm_1', '')
        campaign.dm_template_2  = linkedin.get('dm_2', '')
        campaign.dm_template_3  = linkedin.get('dm_3', '')
        campaign.loom_script    = linkedin.get('loom_script', '')
    except Exception as exc:
        logger.warning(f'LinkedIn template generation failed for campaign {campaign.id}: {exc}')

    # Generate email sequence templates
    try:
        emails = manager.generate_email_sequence(business_type, target_city)
        campaign.email_template_1_subject = emails.get('email_1_subject', '')
        campaign.email_template_1_body    = emails.get('email_1_body', '')
        campaign.email_template_2_subject = emails.get('email_2_subject', '')
        campaign.email_template_2_body    = emails.get('email_2_body', '')
        campaign.email_template_3_subject = emails.get('email_3_subject', '')
        campaign.email_template_3_body    = emails.get('email_3_body', '')
    except Exception as exc:
        logger.warning(f'Email template generation failed for campaign {campaign.id}: {exc}')

    db.session.commit()
    return jsonify({'success': True, 'data': campaign.to_dict()}), 201


# ── Get campaign ───────────────────────────────────────────────────────────────

@agency_outreach_bp.route('/campaign/<campaign_id>', methods=['GET'])
@require_admin
def get_campaign(campaign_id: str):
    campaign = OutreachCampaign.query.filter_by(id=campaign_id).first()
    if not campaign:
        return jsonify({'success': False, 'error': 'Campaign not found'}), 404
    return jsonify({'success': True, 'data': campaign.to_dict(include_templates=True)})


# ── List all campaigns ─────────────────────────────────────────────────────────

@agency_outreach_bp.route('/campaigns', methods=['GET'])
@require_admin
def list_campaigns():
    campaigns = (OutreachCampaign.query
                 .order_by(OutreachCampaign.created_at.desc())
                 .limit(100).all())
    return jsonify({
        'success': True,
        'data': [c.to_dict(include_templates=False) for c in campaigns],
        'count': len(campaigns),
    })


# ── Update campaign status / metrics ──────────────────────────────────────────

@agency_outreach_bp.route('/campaign/<campaign_id>', methods=['PATCH'])
@require_admin
def update_campaign(campaign_id: str):
    campaign = OutreachCampaign.query.filter_by(id=campaign_id).first()
    if not campaign:
        return jsonify({'success': False, 'error': 'Campaign not found'}), 404

    data = request.get_json(silent=True) or {}
    if 'status' in data and data['status'] in _VALID_STATUSES:
        campaign.status = data['status']
    for metric in ('leads_total', 'leads_connected', 'leads_replied',
                   'leads_booked', 'leads_closed'):
        if metric in data and isinstance(data[metric], int) and data[metric] >= 0:
            setattr(campaign, metric, data[metric])
    db.session.commit()
    return jsonify({'success': True, 'data': campaign.to_dict(include_templates=False)})


# ── Import leads ───────────────────────────────────────────────────────────────

@agency_outreach_bp.route('/campaign/<campaign_id>/leads', methods=['POST'])
@require_admin
def import_leads(campaign_id: str):
    """Import a list of leads from the admin portal (CSV uploaded as JSON array)."""
    campaign = OutreachCampaign.query.filter_by(id=campaign_id).first()
    if not campaign:
        return jsonify({'success': False, 'error': 'Campaign not found'}), 404

    data  = request.get_json(silent=True) or {}
    leads = data.get('leads', [])
    if not isinstance(leads, list):
        return jsonify({'success': False, 'error': 'leads must be a JSON array'}), 400

    created = 0
    for raw in leads[:500]:
        if not isinstance(raw, dict):
            continue
        lead = OutreachLead(
            campaign_id=campaign_id,
            first_name   =sanitize_text(str(raw.get('first_name', '')))[:100],
            business_name=sanitize_text(str(raw.get('business_name', '')))[:255],
            linkedin_url =sanitize_text(str(raw.get('linkedin_url', '')))[:500],
            city         =sanitize_text(str(raw.get('city', '')))[:100],
            email        =sanitize_text(str(raw.get('email', '')))[:255] or None,
            source       =raw.get('source', 'manual')[:50],
            stage        ='imported',
        )
        db.session.add(lead)
        created += 1

    if created:
        campaign.leads_total = (campaign.leads_total or 0) + created
        db.session.commit()

    return jsonify({'success': True, 'data': {'created': created}}), 201


# ── List leads ─────────────────────────────────────────────────────────────────

@agency_outreach_bp.route('/campaign/<campaign_id>/leads', methods=['GET'])
@require_admin
def list_leads(campaign_id: str):
    campaign = OutreachCampaign.query.filter_by(id=campaign_id).first()
    if not campaign:
        return jsonify({'success': False, 'error': 'Campaign not found'}), 404

    stage  = request.args.get('stage')
    limit  = min(request.args.get('limit', 200, type=int), 500)
    q = OutreachLead.query.filter_by(campaign_id=campaign_id)
    if stage:
        q = q.filter_by(stage=stage)
    leads = q.order_by(OutreachLead.added_at.desc()).limit(limit).all()
    return jsonify({
        'success': True,
        'data': [l.to_dict(include_email=True) for l in leads],
        'count': len(leads),
    })


# ── Update lead stage ─────────────────────────────────────────────────────────

@agency_outreach_bp.route('/leads/<lead_id>', methods=['PATCH'])
@require_admin
def update_lead(lead_id: str):
    lead = OutreachLead.query.filter_by(id=lead_id).first()
    if not lead:
        return jsonify({'success': False, 'error': 'Lead not found'}), 404

    data = request.get_json(silent=True) or {}
    if 'stage' in data and data['stage'] in _VALID_STAGES:
        new_stage = data['stage']
        lead.stage = new_stage
        campaign = OutreachCampaign.query.get(lead.campaign_id)
        if campaign:
            if new_stage == 'connected':
                campaign.leads_connected = (campaign.leads_connected or 0) + 1
            elif new_stage == 'replied':
                campaign.leads_replied = (campaign.leads_replied or 0) + 1
            elif new_stage == 'booked':
                campaign.leads_booked = (campaign.leads_booked or 0) + 1
            elif new_stage == 'closed':
                campaign.leads_closed = (campaign.leads_closed or 0) + 1

    if 'notes' in data:
        lead.notes = sanitize_text(str(data['notes']))[:2000]
    if 'email' in data:
        lead.email = sanitize_text(str(data['email']))[:255] or None

    db.session.commit()
    return jsonify({'success': True, 'data': lead.to_dict(include_email=True)})


# ── Personalised opener ───────────────────────────────────────────────────────

@agency_outreach_bp.route('/personalise', methods=['POST'])
@require_admin
@limiter.limit('30 per hour')
def personalise_opener():
    """Generate a hyper-personalised opening line for a specific lead."""
    data    = request.get_json(silent=True) or {}
    manager = AgencyOutreachManager()
    opener  = manager.generate_personalised_opener(
        first_name=data.get('first_name', ''),
        business_name=data.get('business_name', ''),
        business_type=data.get('business_type', 'local business'),
        observation=data.get('observation', ''),
    )
    return jsonify({'success': True, 'data': {'opener': opener}})


# ── Scout: run Google Maps import now ─────────────────────────────────────────

@agency_outreach_bp.route('/campaign/<campaign_id>/scout', methods=['POST'])
@require_admin
@limiter.limit('5 per hour')
def scout_campaign(campaign_id: str):
    """Immediately run Google Maps scouting for this campaign."""
    from ..services.agency_scout import AgencyScout

    campaign = OutreachCampaign.query.filter_by(id=campaign_id).first()
    if not campaign:
        return jsonify({'success': False, 'error': 'Campaign not found'}), 404

    if not AgencyScout.is_configured():
        return jsonify({'success': False, 'error': 'GOOGLE_MAPS_API_KEY not configured'}), 503

    data  = request.get_json(silent=True) or {}
    limit = min(int(data.get('limit', 20)), 50)

    try:
        scout   = AgencyScout()
        created = scout.import_leads_for_campaign(campaign, limit=limit)
        db.session.commit()
        return jsonify({'success': True, 'data': {'created': created}})
    except Exception as exc:
        logger.error(f'Scout failed for campaign {campaign_id}: {exc}')
        return jsonify({'success': False, 'error': 'Scout failed — check server logs'}), 500


# ── Email sequence: start for selected leads ──────────────────────────────────

@agency_outreach_bp.route('/campaign/<campaign_id>/email-sequence/start', methods=['POST'])
@require_admin
@limiter.limit('10 per hour')
def start_email_sequence(campaign_id: str):
    """
    Start the Day-0 email for selected (or all imported) leads.
    Body: {"lead_ids": ["...", "..."]}  — omit to start all 'imported' leads.
    """
    from .agency_email_service import AgencyEmailService  # local import to avoid circulars

    campaign = OutreachCampaign.query.filter_by(id=campaign_id).first()
    if not campaign:
        return jsonify({'success': False, 'error': 'Campaign not found'}), 404

    # Lazy import here to keep top-level imports clean
    from ..services.agency_email_service import AgencyEmailService as _EmailSvc

    if not _EmailSvc.is_configured():
        return jsonify({'success': False, 'error': 'SMTP not configured in .env'}), 503

    data     = request.get_json(silent=True) or {}
    lead_ids = data.get('lead_ids')

    q = OutreachLead.query.filter_by(campaign_id=campaign_id)
    if lead_ids and isinstance(lead_ids, list):
        q = q.filter(OutreachLead.id.in_(lead_ids))
    else:
        q = q.filter_by(stage='imported')

    leads = q.filter_by(email_sequence_step=0).all()

    svc     = _EmailSvc()
    started = 0
    for lead in leads:
        if not lead.email:
            continue
        ok = svc.send_sequence_email(lead, step=1, campaign=campaign)
        if ok:
            lead.stage = 'email_sequence'
            started += 1

    db.session.commit()
    return jsonify({'success': True, 'data': {'started': started}})
