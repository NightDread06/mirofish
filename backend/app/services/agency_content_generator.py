"""
Agency Content Generator Service

Generates 30-day social media content calendars using Claude API
with prompt caching for 90%+ cost reduction on repeated client calls.

Model selection:
  - Pilot clients  → claude-haiku-4-5   (~€0.003 per 30-post package)
  - Retainer clients → claude-sonnet-4-6 (higher quality, ~€0.05 per package)

Async pattern mirrors report_agent.py: TaskManager for progress tracking,
background thread with explicit Flask app context for DB writes.
"""

import json
import re
import threading
import time
from datetime import date, timedelta
from typing import Dict, List

import anthropic

from ..config import Config
from ..models.task import TaskManager, TaskStatus
from ..middleware.sanitize import wrap_for_prompt, sanitize_text
from ..utils.logger import get_logger
from ..utils.retry import retry_with_backoff

logger = get_logger('mirofish.agency.content_generator')


# ── Business-type persona library ────────────────────────────────────────────

BUSINESS_PERSONAS: Dict[str, Dict] = {
    'gym': {
        'voice': 'Motivational, energetic, community-focused. Celebrate member wins.',
        'content_mix': {'educational': 0.30, 'promotional': 0.20,
                        'engagement': 0.30, 'story': 0.20},
        'platform': {
            'linkedin':  'Thought leadership on wellness culture, B2B partnerships.',
            'instagram': 'Transformation stories, workout tips, class previews.',
            'facebook':  'Community events, local promotions, member spotlights.',
        },
    },
    'salon': {
        'voice': 'Warm, aspirational, trend-aware. Show the craft.',
        'content_mix': {'educational': 0.25, 'promotional': 0.25,
                        'engagement': 0.25, 'story': 0.25},
        'platform': {
            'linkedin':  'Team expertise, award wins, business growth story.',
            'instagram': 'Before/after transformations, technique videos, products.',
            'facebook':  'Booking CTAs, seasonal offers, client testimonials.',
        },
    },
    'restaurant': {
        'voice': 'Warm, inviting, food-passionate. Tell the story behind each dish.',
        'content_mix': {'educational': 0.15, 'promotional': 0.35,
                        'engagement': 0.30, 'story': 0.20},
        'platform': {
            'linkedin':  'Supplier partnerships, sustainability story, team culture.',
            'instagram': 'Dish photography direction, chef stories, behind-the-scenes.',
            'facebook':  'Daily specials, event bookings, local community tie-ins.',
        },
    },
    'clinic': {
        'voice': 'Professional, empathetic, trustworthy. NEVER reference patient data.',
        'content_mix': {'educational': 0.50, 'promotional': 0.10,
                        'engagement': 0.25, 'story': 0.15},
        'platform': {
            'linkedin':  'Clinical thought leadership, service updates, team expertise.',
            'instagram': 'Health tips, awareness campaigns, team introductions.',
            'facebook':  'FAQ posts, appointment booking, health awareness days.',
        },
    },
    'real_estate': {
        'voice': 'Authoritative, data-driven, local market expert. Build trust.',
        'content_mix': {'educational': 0.40, 'promotional': 0.20,
                        'engagement': 0.25, 'story': 0.15},
        'platform': {
            'linkedin':  'Market analysis, investment insights, developer partnerships.',
            'instagram': 'Property tours, neighbourhood guides, lifestyle content.',
            'facebook':  'New listings, open days, first-buyer tips.',
        },
    },
}

_DEFAULT_PERSONA = BUSINESS_PERSONAS['gym']


# ── Prompt builders ───────────────────────────────────────────────────────────

def _build_system_prompt(client: Dict) -> str:
    """
    Build the cacheable system prompt for this client.
    All user-supplied values are XML-wrapped to prevent prompt injection.
    This large block is cached by Claude after the first call.
    """
    btype = sanitize_text(client.get('business_type', 'local business'))
    persona = BUSINESS_PERSONAS.get(btype, _DEFAULT_PERSONA)
    mix = persona['content_mix']

    return f"""You are a professional social media content strategist specialising in \
hyper-local content for {btype} businesses.

BUSINESS PROFILE:
- Name: {wrap_for_prompt('business_name', client.get('business_name', ''))}
- Type: {btype}
- Location: {wrap_for_prompt('city', client.get('city', ''))}, \
{sanitize_text(client.get('country', 'IE'))}
- Target audience: {wrap_for_prompt('target_audience', client.get('target_audience', 'local community'))}
- Brand tone: {wrap_for_prompt('tone', client.get('tone', 'friendly and professional'))}
- Brand keywords: {wrap_for_prompt('brand_keywords', client.get('brand_keywords', ''))}
- Competitors to differentiate from: \
{wrap_for_prompt('competitors', client.get('competitors', 'N/A'))}

VOICE GUIDANCE: {persona['voice']}

PLATFORM STRATEGY:
- LinkedIn: {persona['platform']['linkedin']}
- Instagram: {persona['platform']['instagram']}
- Facebook: {persona['platform']['facebook']}

CONTENT MIX TARGET:
- Educational: {int(mix['educational'] * 100)}%
- Promotional: {int(mix['promotional'] * 100)}%
- Engagement (questions/polls): {int(mix['engagement'] * 100)}%
- Story/behind-the-scenes: {int(mix['story'] * 100)}%

OUTPUT RULES:
1. Write in the specified brand tone — not generic corporate language.
2. Reference the specific city/area for hyper-local relevance.
3. Platform character limits:
   - LinkedIn: 150–300 words, professional framing
   - Instagram: 50–150 words + 10–15 hashtags
   - Facebook: 75–200 words, conversational, local focus
4. Include exactly one clear call-to-action per post.
5. Provide a visual_description (1-2 sentences for a photographer or designer).
6. NEVER use real patient names, client photos, or identifiable personal data.
7. Output ONLY valid JSON with no markdown fences."""


def _build_post_prompt(day: int, platform: str, post_type: str, start: date) -> str:
    """Lightweight per-post prompt (not cached — cheap input tokens)."""
    scheduled = (start + timedelta(days=day - 1)).strftime('%A, %d %B %Y')
    return f"""Generate post #{day} of 30 for {platform}.

Post type: {post_type}
Scheduled date: {scheduled}

Return a JSON object with exactly these keys:
{{
  "post_copy": "...",
  "hashtags": "...",
  "call_to_action": "...",
  "visual_description": "..."
}}"""


# ── Main generator class ──────────────────────────────────────────────────────

class AgencyContentGenerator:
    """Generates a 30-day content calendar using Claude with prompt caching."""

    def __init__(self, use_premium: bool = False):
        self.use_premium = use_premium
        self.model = (Config.CLAUDE_SONNET_MODEL if use_premium
                      else Config.CLAUDE_HAIKU_MODEL)
        self._client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)
        self._task_manager = TaskManager()

    def generate_async(
        self,
        client_data: Dict,
        package_id: str,
        task_id: str,
        platforms: List[str],
        start_date: date,
        flask_app,            # current_app._get_current_object() — for app context
    ) -> None:
        """
        Launch async generation in a background daemon thread.
        Mirrors the threading pattern in report.py lines 124-175.
        """
        def _run():
            try:
                self._task_manager.update_task(
                    task_id, status=TaskStatus.PROCESSING,
                    progress=5, message='Building content strategy…',
                )
                posts = self._generate_all_posts(
                    client_data=client_data,
                    platforms=platforms,
                    start_date=start_date,
                    task_id=task_id,
                )
                # Persist to DB inside an explicit app context (background thread)
                with flask_app.app_context():
                    self._persist_posts(package_id, posts, flask_app)
                self._task_manager.complete_task(task_id, result={
                    'package_id': package_id,
                    'post_count': len(posts),
                })
            except Exception as exc:
                logger.error(f'Content generation failed for package {package_id}: {exc}')
                self._task_manager.fail_task(task_id, str(exc))

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def _generate_all_posts(
        self,
        client_data: Dict,
        platforms: List[str],
        start_date: date,
        task_id: str,
    ) -> List[Dict]:
        """
        Core generation loop.
        The system prompt is sent with cache_control on every call; Claude
        serves subsequent calls from cache after the first (~90% token savings).
        """
        system_prompt = _build_system_prompt(client_data)
        btype = client_data.get('business_type', 'gym')
        persona = BUSINESS_PERSONAS.get(btype, _DEFAULT_PERSONA)
        post_type_seq = self._post_type_sequence(persona['content_mix'], days=30)

        posts: List[Dict] = []
        total = 30 * len(platforms)
        done = 0

        for day in range(1, 31):
            for platform in platforms:
                post_type = post_type_seq[day - 1]
                raw = self._call_claude(system_prompt, day, platform, post_type, start_date)
                post_data = self._parse_post(raw, day, platform)
                scheduled = (start_date + timedelta(days=day - 1)).isoformat()
                posts.append({
                    'platform': platform,
                    'day_number': day,
                    'scheduled_date': scheduled,
                    'post_type': post_type,
                    **post_data,
                })
                done += 1
                progress = 5 + int(done / total * 90)
                self._task_manager.update_task(
                    task_id, progress=progress,
                    message=f'Generated day {day}/30 — {platform}',
                )
                # Polite pause to respect Anthropic rate limits
                time.sleep(0.1)

        return posts

    @retry_with_backoff(max_retries=3, initial_delay=2.0)
    def _call_claude(
        self, system_prompt: str, day: int,
        platform: str, post_type: str, start_date: date,
    ) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=[{
                'type': 'text',
                'text': system_prompt,
                'cache_control': {'type': 'ephemeral'},   # Cache the expensive system prompt
            }],
            messages=[{
                'role': 'user',
                'content': _build_post_prompt(day, platform, post_type, start_date),
            }],
        )
        return response.content[0].text

    @staticmethod
    def _parse_post(raw: str, day: int, platform: str) -> Dict:
        """Parse Claude's JSON response; fall back gracefully on parse error."""
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', raw.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
        try:
            data = json.loads(cleaned)
            return {
                'post_copy': str(data.get('post_copy', '')),
                'hashtags': str(data.get('hashtags', '')),
                'call_to_action': str(data.get('call_to_action', 'Visit us today')),
                'visual_description': str(data.get('visual_description', '')),
            }
        except json.JSONDecodeError:
            logger.warning(f'JSON parse failed for day {day}/{platform} — using raw text')
            return {
                'post_copy': raw,
                'hashtags': '',
                'call_to_action': 'Visit us today',
                'visual_description': 'Professional photo of the business',
            }

    @staticmethod
    def _post_type_sequence(mix: Dict[str, float], days: int) -> List[str]:
        """Distribute post types evenly across 30 days based on the content mix."""
        seq: List[str] = []
        for ptype, ratio in mix.items():
            seq.extend([ptype] * round(days * ratio))
        while len(seq) < days:
            seq.append('engagement')
        return seq[:days]

    @staticmethod
    def _persist_posts(package_id: str, posts: List[Dict], app) -> None:
        """Write generated posts to DB and mark package complete. Called inside app_context."""
        from datetime import datetime, date as ddate
        from ..extensions import db
        from ..models.agency_content import ContentPackage, ContentPost

        package = ContentPackage.query.filter_by(id=package_id).first()
        if not package:
            logger.error(f'Package {package_id} not found during persist')
            return

        for p in posts:
            raw_date = p.get('scheduled_date')
            scheduled = ddate.fromisoformat(raw_date) if raw_date else None
            post = ContentPost(
                package_id=package_id,
                platform=p['platform'],
                day_number=p['day_number'],
                scheduled_date=scheduled,
                post_type=p.get('post_type', 'engagement'),
                post_copy=p.get('post_copy', ''),
                hashtags=p.get('hashtags', ''),
                call_to_action=p.get('call_to_action', ''),
                visual_description=p.get('visual_description', ''),
            )
            db.session.add(post)

        package.status = 'completed'
        package.post_count = len(posts)
        package.completed_at = datetime.utcnow()
        db.session.commit()
        logger.info(f'Persisted {len(posts)} posts for package {package_id}')
