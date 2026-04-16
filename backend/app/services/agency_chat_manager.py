"""
Agency Chat Manager — Claude Sonnet AI closer.

Manages multi-turn email conversations with leads, autonomously progressing
through stages: discovery → qualifying → pitching → objections → closing → won/lost.

Claude returns JSON: {"reply": "...", "next_stage": "..."} on every turn.
The reply is emailed back to the lead by the scheduler.
"""

import json
from datetime import datetime

import anthropic

from ..config import Config
from ..middleware.sanitize import sanitize_text
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.chat')

_SYSTEM_PROMPT_TEMPLATE = """You are a professional sales consultant for {agency_name}.
You help local {business_type} businesses get more customers with AI-powered social media content.

You are emailing {first_name} at {business_name} in {city}.

YOUR OBJECTIVE: Qualify the lead and close them on a pilot or retainer package via email.

PRICING:
- Pilot: €500/month — 30 AI-generated social posts, 3 platforms, 1 revision round
- Retainer: €1,500/month — Full service, unlimited revisions, analytics, priority support

STAGE PROGRESSION (advance in order, do not skip stages):
1. discovery    — Ask 2 open questions about their current social media pain points
2. qualifying   — Assess budget readiness and whether they are the decision-maker
3. pitching     — Present the specific package that fits their situation
4. objections   — Handle price/trust/timing objections using the scripts below
5. closing      — Send the payment link and ask them to get started today

OBJECTION HANDLING SCRIPTS:
- "Too expensive" → "A freelance social media manager costs €2,000–4,000/month. Our pilot at €500 gives you a full month of content to see results first."
- "Need to think about it" → "Of course — to make it easier, I can do a free content audit of your current social pages so you can see exactly what's missing. Would that help?"
- "Not sure it will work" → "I completely understand. That's why we offer a pilot month at €500 — if you don't see improvement in engagement within 30 days, we'll refund you."

RULES:
- Keep each email under 150 words. One key point per email.
- Never be pushy. One ask or question per email, maximum.
- Sound natural and human. No corporate buzzwords.
- When stage is 'closing', include this payment link naturally: {payment_link}
- Always end with a clear question or next step.

RESPONSE FORMAT — always return valid JSON:
{{"reply": "the email body to send", "next_stage": "one of the 6 stage names above or the current stage if no change"}}

Current conversation stage: {current_stage}"""

_STAGES = ['discovery', 'qualifying', 'pitching', 'objections', 'closing', 'won', 'lost']


class AgencyChatManager:
    """AI conversation closer using Claude Sonnet with persistent message history."""

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)
        self._model  = Config.CLAUDE_SONNET_MODEL
        # Default payment link — override via env or admin setting
        self._payment_link = 'https://buy.stripe.com/your-link'

    # ── Public interface ──────────────────────────────────────────────────────

    def start_conversation(self, lead, campaign, flask_app) -> 'AgencyConversation':
        """
        Create a new AgencyConversation and generate the first discovery email.
        Returns the saved conversation.
        """
        from ..models.agency_conversation import AgencyConversation
        from ..extensions import db

        system_prompt = self._build_system_prompt(lead, campaign, 'discovery')
        first_reply   = self._call_claude(system_prompt, [], 'discovery')

        conv = AgencyConversation(
            lead_id  = lead.id,
            messages = [{
                'role':      'assistant',
                'content':   first_reply['reply'],
                'timestamp': datetime.utcnow().isoformat(),
            }],
            stage = first_reply.get('next_stage', 'discovery'),
        )

        with flask_app.app_context():
            db.session.add(conv)
            db.session.commit()

        logger.info(f'Started conversation {conv.id} for lead {lead.id}')
        return conv

    def process_reply(self, conversation, incoming_message: str, flask_app) -> str:
        """
        Append the inbound message to the conversation, call Claude for a reply,
        advance stage if indicated, persist changes, and return the reply text.
        """
        from ..models.agency_outreach import OutreachLead
        from ..models.agency_conversation import AgencyConversation
        from ..extensions import db

        # Append inbound message
        messages = list(conversation.messages or [])
        messages.append({
            'role':      'user',
            'content':   sanitize_text(incoming_message),
            'timestamp': datetime.utcnow().isoformat(),
        })

        with flask_app.app_context():
            # Reload within context to avoid detached-instance errors
            conv = db.session.get(AgencyConversation, conversation.id)
            lead = db.session.get(OutreachLead, conv.lead_id)
            campaign = lead.campaign

            system_prompt = self._build_system_prompt(lead, campaign, conv.stage)
            claude_msgs   = self._to_claude_messages(messages)
            result        = self._call_claude(system_prompt, claude_msgs, conv.stage)

            reply_text  = result['reply']
            next_stage  = result.get('next_stage', conv.stage)
            if next_stage not in _STAGES:
                next_stage = conv.stage

            messages.append({
                'role':      'assistant',
                'content':   reply_text,
                'timestamp': datetime.utcnow().isoformat(),
            })

            conv.messages = messages
            conv.stage    = next_stage

            # Sync lead stage
            if next_stage == 'won':
                lead.stage = 'closed'
            elif next_stage == 'lost':
                lead.stage = 'rejected'
            elif lead.stage not in ('closed', 'rejected'):
                lead.stage = 'replied'

            db.session.commit()
            logger.info(f'Conversation {conv.id} advanced to stage={next_stage}')

        return reply_text

    # ── Internals ─────────────────────────────────────────────────────────────

    def _build_system_prompt(self, lead, campaign, current_stage: str) -> str:
        return _SYSTEM_PROMPT_TEMPLATE.format(
            agency_name   = Config.SMTP_FROM_NAME or 'ContentAgency.ai',
            business_type = sanitize_text(campaign.business_type or 'business'),
            first_name    = sanitize_text(lead.first_name or 'there'),
            business_name = sanitize_text(lead.business_name or 'your business'),
            city          = sanitize_text(lead.city or 'your city'),
            payment_link  = self._payment_link,
            current_stage = current_stage,
        )

    def _call_claude(
        self,
        system_prompt: str,
        messages: list[dict],
        current_stage: str,
    ) -> dict:
        """Call Claude Sonnet with prompt caching on the system prompt."""
        try:
            # Seed with an empty user turn if no history yet
            if not messages:
                messages = [{'role': 'user', 'content': 'Please start the conversation.'}]

            response = self._client.messages.create(
                model      = self._model,
                max_tokens = 512,
                system     = [{
                    'type':          'text',
                    'text':          system_prompt,
                    'cache_control': {'type': 'ephemeral'},
                }],
                messages = messages,
            )
            raw = response.content[0].text.strip()

            # Parse JSON response
            try:
                # Handle markdown code fences if present
                if raw.startswith('```'):
                    raw = raw.split('```')[1]
                    if raw.startswith('json'):
                        raw = raw[4:]
                return json.loads(raw)
            except json.JSONDecodeError:
                # Fallback: use raw text as reply, keep current stage
                return {'reply': raw, 'next_stage': current_stage}

        except Exception as exc:
            logger.error(f'Claude chat call failed: {exc}')
            return {
                'reply': "Thank you for your message — I'll get back to you shortly.",
                'next_stage': current_stage,
            }

    @staticmethod
    def _to_claude_messages(messages: list[dict]) -> list[dict]:
        """Convert stored message history to Claude API format."""
        return [
            {'role': m['role'], 'content': m['content']}
            for m in messages
            if m.get('role') in ('user', 'assistant') and m.get('content')
        ]
