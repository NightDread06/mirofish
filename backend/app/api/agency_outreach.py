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
    'imported', 'connection_sent', 'connected',
    'dm_sent', 'replied', 'booked', 'closed', 'rejected',
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

    # Generate templates via Claude
    try:
        manager   = AgencyOutreachManager()
        templates = manager.generate_linkedin_sequence(business_type, target_city)
        campaign.connection_msg = templates.get('connection_request', '')[:300]
        campaign.dm_template_1  = templates.get('dm_1', '')
        campaign.dm_template_2  = templates.get('dm_2', '')
        campaign.dm_template_3  = templates.get('dm_3', '')
        campaign.loom_script    = templates.get('loom_script', '')
    except Exception as exc:
        logger.warning(f'Template generation failed for campaign {campaign.id}: {exc}')
        # Save campaign anyway — admin can retry template generation later

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
    # Manual metric updates (agency owner tracks their own outreach)
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
    for raw in leads[:500]:   # hard cap to prevent abuse
        if not isinstance(raw, dict):
            continue
        lead = OutreachLead(
            campaign_id=campaign_id,
            first_name=sanitize_text(str(raw.get('first_name', '')))[:100],
            business_name=sanitize_text(str(raw.get('business_name', '')))[:255],
            linkedin_url=sanitize_text(str(raw.get('linkedin_url', '')))[:500],
            city=sanitize_text(str(raw.get('city', '')))[:100],
            stage='imported',
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
    return jsonify({'success': True, 'data': [l.to_dict() for l in leads], 'count': len(leads)})


# ── Update lead stage ─────────────────────────────────────────────────────────

@agency_outreach_bp.route('/leads/<lead_id>', methods=['PATCH'])
@require_admin
def update_lead(lead_id: str):
    lead = OutreachLead.query.filter_by(id=lead_id).first()
    if not lead:
        return jsonify({'success': False, 'error': 'Lead not found'}), 404

    data = request.get_json(silent=True) or {}
    if 'stage' in data and data['stage'] in _VALID_STAGES:
        lead.stage = data['stage']
        # Sync campaign connected count
        if data['stage'] == 'connected':
            campaign = OutreachCampaign.query.get(lead.campaign_id)
            if campaign:
                campaign.leads_connected = (campaign.leads_connected or 0) + 1
        elif data['stage'] == 'replied':
            campaign = OutreachCampaign.query.get(lead.campaign_id)
            if campaign:
                campaign.leads_replied = (campaign.leads_replied or 0) + 1
        elif data['stage'] == 'booked':
            campaign = OutreachCampaign.query.get(lead.campaign_id)
            if campaign:
                campaign.leads_booked = (campaign.leads_booked or 0) + 1
        elif data['stage'] == 'closed':
            campaign = OutreachCampaign.query.get(lead.campaign_id)
            if campaign:
                campaign.leads_closed = (campaign.leads_closed or 0) + 1

    if 'notes' in data:
        lead.notes = sanitize_text(str(data['notes']))[:2000]
    db.session.commit()
    return jsonify({'success': True, 'data': lead.to_dict()})


# ── Personalised opener ───────────────────────────────────────────────────────

@agency_outreach_bp.route('/personalise', methods=['POST'])
@require_admin
@limiter.limit('30 per hour')
def personalise_opener():
    """Generate a hyper-personalised opening line for a specific lead."""
    data = request.get_json(silent=True) or {}
    manager = AgencyOutreachManager()
    opener  = manager.generate_personalised_opener(
        first_name=data.get('first_name', ''),
        business_name=data.get('business_name', ''),
        business_type=data.get('business_type', 'local business'),
        observation=data.get('observation', ''),
    )
    return jsonify({'success': True, 'data': {'opener': opener}})
