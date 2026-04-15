"""
Outreach template generation and campaign management service.

Important: This service generates TEXT TEMPLATES only.
No LinkedIn/email credentials are stored or used for automated sending.
All outreach is performed manually by the agency owner using the generated templates.
"""

from typing import Dict

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger
from ..middleware.sanitize import sanitize_text

logger = get_logger('mirofish.agency.outreach_manager')


_DM_SEQUENCE_PROMPT = """You are a LinkedIn outreach specialist for a boutique AI social media agency.

The agency offers: AI-powered 30-day social media content calendars at €500/month for the pilot.
Target: {business_type} business owners in {city}.

Write a 3-touch outreach sequence that is:
- Concise and value-first (lead with the outcome, not the technology)
- Reference the local area for hyper-personalisation
- No pressure or aggressive sales language
- Each message shorter than the previous one

Also write a 60-second Loom video pitch script that:
- Opens with a specific observation about their business/industry
- Shows 3 concrete pain points solved by the service
- Ends with a clear, low-risk CTA (free content audit)

Return ONLY a valid JSON object with these keys:
{{
  "connection_request": "<LinkedIn connection note, strictly under 280 characters>",
  "dm_1": "<Initial DM after connecting, under 300 words>",
  "dm_2": "<Follow-up 3 days later if no reply, under 200 words>",
  "dm_3": "<Final value-add follow-up day 7, under 150 words>",
  "loom_script": "<60-second video script with opening hook, 3 pain points, CTA>"
}}"""

_COLD_EMAIL_PROMPT = """You are an email copywriter specialising in cold B2B outreach for local service businesses.

Agency offer: AI-powered social media content packages at €500/month.
Target: {business_type} businesses in {city}.

Write a 3-email cold email sequence (plain text, no HTML):
- Email 1: Subject line + 4-sentence body. Timeline hook: reference something observable about their business.
- Email 2 (follow-up, 3 days): 3 sentences maximum. Different angle.
- Email 3 (final, day 7): 2 sentences. Soft break-up + offer to share a 2-min video.

Research shows emails of 50-125 words get 50%+ higher reply rates. Keep each tight.

Return ONLY a valid JSON object:
{{
  "email_1": {{"subject": "...", "body": "..."}},
  "email_2": {{"subject": "...", "body": "..."}},
  "email_3": {{"subject": "...", "body": "..."}}
}}"""


class AgencyOutreachManager:

    def __init__(self):
        # Use existing LLM client pointing at Claude API
        self._llm = LLMClient(
            api_key=Config.CLAUDE_API_KEY,
            base_url=Config.CLAUDE_BASE_URL,
            model=Config.CLAUDE_HAIKU_MODEL,
        )

    def generate_linkedin_sequence(self, business_type: str, city: str) -> Dict:
        """Generate a 3-touch LinkedIn DM sequence + Loom script for a campaign."""
        prompt = _DM_SEQUENCE_PROMPT.format(
            business_type=sanitize_text(business_type),
            city=sanitize_text(city),
        )
        try:
            result = self._llm.chat_json(
                [{'role': 'user', 'content': prompt}],
                temperature=0.65,
                max_tokens=2048,
            )
            return result
        except Exception as exc:
            logger.error(f'LinkedIn sequence generation failed: {exc}')
            raise

    def generate_email_sequence(self, business_type: str, city: str) -> Dict:
        """Generate a 3-email cold email sequence for a campaign."""
        prompt = _COLD_EMAIL_PROMPT.format(
            business_type=sanitize_text(business_type),
            city=sanitize_text(city),
        )
        try:
            result = self._llm.chat_json(
                [{'role': 'user', 'content': prompt}],
                temperature=0.65,
                max_tokens=2048,
            )
            return result
        except Exception as exc:
            logger.error(f'Email sequence generation failed: {exc}')
            raise

    def generate_personalised_opener(self, first_name: str, business_name: str,
                                     business_type: str, observation: str) -> str:
        """
        Generate a hyper-personalised opening line for a specific lead.
        'observation' is a 1-sentence note about something the agency owner noticed
        (e.g. 'they just opened a second location', 'their Instagram hasn't posted in 3 weeks').
        """
        prompt = (
            f"Write a single conversational opening sentence for a LinkedIn DM to "
            f"{sanitize_text(first_name)} at {sanitize_text(business_name)} "
            f"({sanitize_text(business_type)}). "
            f"Context: {sanitize_text(observation)}. "
            f"Under 30 words. Natural, not salesy. Return only the sentence."
        )
        try:
            return self._llm.chat(
                [{'role': 'user', 'content': prompt}],
                temperature=0.8,
                max_tokens=80,
            ).strip()
        except Exception as exc:
            logger.error(f'Personalised opener generation failed: {exc}')
            return f"Hey {sanitize_text(first_name)}, noticed your work at {sanitize_text(business_name)}."
