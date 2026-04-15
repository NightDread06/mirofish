"""
Agency Publisher — Buffer API integration.

Pushes approved client posts to Buffer so they get published automatically
on their scheduled dates.

Buffer setup:
  1. Go to buffer.com/developers/apps — create a personal access app
  2. Get your access token and set BUFFER_ACCESS_TOKEN in .env
  3. Find your profile IDs at buffer.com/app/profile/:id/tab/stream
  4. Set BUFFER_PROFILE_IDS as JSON: {"linkedin":"...", "instagram":"...", "facebook":"..."}

Buffer free tier: 3 channels, 10 scheduled posts per channel.
"""

import json
from datetime import datetime, date, timedelta

import requests

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.publisher')

_BUFFER_API = 'https://api.bufferapp.com/1'


class AgencyPublisher:
    """Posts approved content to Buffer for automatic social media publishing."""

    def __init__(self):
        self._token = Config.BUFFER_ACCESS_TOKEN
        try:
            self._profile_ids: dict = json.loads(Config.BUFFER_PROFILE_IDS)
        except (json.JSONDecodeError, TypeError):
            self._profile_ids = {}

    # ── Public interface ──────────────────────────────────────────────────────

    def push_post_to_buffer(
        self,
        post,
        profile_id: str,
        scheduled_at: datetime | None = None,
    ) -> str | None:
        """
        Push a single ContentPost to Buffer.
        Returns the Buffer update_id on success, None on failure.
        Updates post.buffer_update_id and post.buffer_scheduled_at in place
        (caller must commit the DB session).
        """
        if not self._token:
            logger.warning('BUFFER_ACCESS_TOKEN not configured')
            return None

        text = _build_post_text(post)

        payload = {
            'access_token':   self._token,
            'profile_ids[]':  profile_id,
            'text':           text,
        }
        if scheduled_at:
            payload['scheduled_at'] = int(scheduled_at.timestamp())

        try:
            resp = requests.post(
                f'{_BUFFER_API}/updates/create.json',
                data=payload,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get('success'):
                update_id = (data.get('updates') or [{}])[0].get('id', '')
                post.buffer_update_id    = update_id
                post.buffer_scheduled_at = scheduled_at or datetime.utcnow()
                logger.info(f'Post {post.id} pushed to Buffer (update_id={update_id})')
                return update_id
            else:
                logger.error(f'Buffer API error for post {post.id}: {data}')
                return None

        except Exception as exc:
            logger.error(f'push_post_to_buffer failed for post {post.id}: {exc}')
            return None

    def push_approved_posts(self, lookahead_days: int = 1) -> dict:
        """
        Push all approved posts scheduled for tomorrow (lookahead_days=1) that
        haven't been pushed to Buffer yet.
        Returns {"pushed": int, "failed": int}.
        Caller must commit the DB session.
        """
        from ..models.agency_content import ContentPost

        if not self._token:
            logger.warning('Buffer not configured — skipping push_approved_posts()')
            return {'pushed': 0, 'failed': 0}

        target_date = (date.today() + timedelta(days=lookahead_days))

        posts = ContentPost.query.filter(
            ContentPost.is_approved == True,          # noqa: E712
            ContentPost.buffer_update_id == None,     # noqa: E711  not yet pushed
            ContentPost.scheduled_date == target_date,
        ).all()

        pushed, failed = 0, 0
        for post in posts:
            profile_id = self._profile_ids.get(post.platform)
            if not profile_id:
                logger.warning(f'No Buffer profile ID for platform "{post.platform}" — skipping post {post.id}')
                failed += 1
                continue

            # Schedule for 10:00 AM on the post's date
            scheduled_dt = datetime.combine(post.scheduled_date, datetime.min.time()).replace(hour=10)
            result = self.push_post_to_buffer(post, profile_id, scheduled_dt)
            if result:
                pushed += 1
            else:
                failed += 1

        logger.info(f'Buffer push complete: {pushed} pushed, {failed} failed for {target_date}')
        return {'pushed': pushed, 'failed': failed}

    @staticmethod
    def is_configured() -> bool:
        return bool(Config.BUFFER_ACCESS_TOKEN)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_post_text(post) -> str:
    """Combine post copy and hashtags into the Buffer text field."""
    parts = []
    if post.post_copy:
        parts.append(post.post_copy)
    if post.hashtags:
        parts.append(post.hashtags)
    return '\n\n'.join(parts)[:2000]
