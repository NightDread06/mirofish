"""
AI Chat Closer API.

POST /api/agency/chat/lead/<lead_id>/start       — Start a conversation with a lead
POST /api/agency/chat/conversation/<id>/reply    — Inject inbound message, get AI reply
GET  /api/agency/chat/lead/<lead_id>             — List conversations for a lead
GET  /api/agency/chat/conversation/<id>          — Get full conversation with messages
"""

from flask import Blueprint, request, jsonify
from flask import current_app

from ..extensions import db, limiter
from ..middleware.auth import require_admin
from ..middleware.sanitize import sanitize_text
from ..models.agency_outreach import OutreachLead
from ..models.agency_conversation import AgencyConversation
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.chat')
agency_chat_bp = Blueprint('agency_chat', __name__)


# ── Start a new conversation ──────────────────────────────────────────────────

@agency_chat_bp.route('/lead/<lead_id>/start', methods=['POST'])
@require_admin
@limiter.limit('20 per hour')
def start_conversation(lead_id: str):
    """Create a new AgencyConversation and generate the first discovery email."""
    from ..services.agency_chat_manager import AgencyChatManager

    lead = OutreachLead.query.get(lead_id)
    if not lead:
        return jsonify({'success': False, 'error': 'Lead not found'}), 404

    campaign = lead.campaign
    if not campaign:
        return jsonify({'success': False, 'error': 'Lead has no associated campaign'}), 400

    try:
        flask_app = current_app._get_current_object()
        mgr  = AgencyChatManager()
        conv = mgr.start_conversation(lead, campaign, flask_app)
        return jsonify({'success': True, 'data': conv.to_dict()}), 201
    except Exception as exc:
        logger.error(f'start_conversation failed for lead {lead_id}: {exc}')
        return jsonify({'success': False, 'error': 'Failed to start conversation'}), 500


# ── Inject an inbound reply ───────────────────────────────────────────────────

@agency_chat_bp.route('/conversation/<conv_id>/reply', methods=['POST'])
@require_admin
@limiter.limit('60 per hour')
def inject_reply(conv_id: str):
    """
    Simulate or process an inbound message from the lead.
    Used for: scheduler-driven email replies and manual testing from the admin UI.
    Returns the AI reply text.
    """
    from ..services.agency_chat_manager import AgencyChatManager

    conv = AgencyConversation.query.get(conv_id)
    if not conv:
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404

    data    = request.get_json(silent=True) or {}
    message = sanitize_text(str(data.get('message', ''))).strip()
    if not message:
        return jsonify({'success': False, 'error': 'message is required'}), 400

    try:
        flask_app  = current_app._get_current_object()
        mgr        = AgencyChatManager()
        reply_text = mgr.process_reply(conv, message, flask_app)

        # Reload conv after process_reply (it commits internally)
        conv = AgencyConversation.query.get(conv_id)
        return jsonify({
            'success': True,
            'data': {
                'reply':        reply_text,
                'stage':        conv.stage,
                'conversation': conv.to_dict(include_messages=False),
            },
        })
    except Exception as exc:
        logger.error(f'inject_reply failed for conversation {conv_id}: {exc}')
        return jsonify({'success': False, 'error': 'Failed to process reply'}), 500


# ── List conversations for a lead ─────────────────────────────────────────────

@agency_chat_bp.route('/lead/<lead_id>', methods=['GET'])
@require_admin
def list_conversations(lead_id: str):
    lead = OutreachLead.query.get(lead_id)
    if not lead:
        return jsonify({'success': False, 'error': 'Lead not found'}), 404

    convs = (AgencyConversation.query
             .filter_by(lead_id=lead_id)
             .order_by(AgencyConversation.created_at.desc())
             .all())
    return jsonify({
        'success': True,
        'data': [c.to_dict(include_messages=False) for c in convs],
        'count': len(convs),
    })


# ── Get single conversation with full message history ─────────────────────────

@agency_chat_bp.route('/conversation/<conv_id>', methods=['GET'])
@require_admin
def get_conversation(conv_id: str):
    conv = AgencyConversation.query.get(conv_id)
    if not conv:
        return jsonify({'success': False, 'error': 'Conversation not found'}), 404
    return jsonify({'success': True, 'data': conv.to_dict(include_messages=True)})
