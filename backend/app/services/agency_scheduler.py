"""
Agency Scheduler — APScheduler background jobs.

Four autonomous jobs run inside the Flask process:
  daily_scout    08:00 Dublin  → Google Maps prospect import for active campaigns
  check_replies  every 15 min  → IMAP poll → AI chat reply → email response out
  follow_ups     every 30 min  → Day-3 and Day-7 email follow-up sequences
  publish_posts  23:00 Dublin  → Push tomorrow's approved posts to Buffer + GDPR cleanup

All jobs push an explicit Flask app context so SQLAlchemy sessions work correctly.
"""

from datetime import datetime, timedelta

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.scheduler')


def init_scheduler(flask_app) -> None:
    """Register all four jobs and start the BackgroundScheduler."""
    from ..extensions import scheduler

    scheduler.add_job(
        func=run_daily_scout,
        args=[flask_app],
        trigger=CronTrigger(hour=8, minute=0, timezone='Europe/Dublin'),
        id='daily_scout',
        name='Daily Google Maps Scout',
        replace_existing=True,
    )
    scheduler.add_job(
        func=check_email_replies,
        args=[flask_app],
        trigger=IntervalTrigger(minutes=15),
        id='check_replies',
        name='Check Email Replies',
        replace_existing=True,
    )
    scheduler.add_job(
        func=send_scheduled_follow_ups,
        args=[flask_app],
        trigger=IntervalTrigger(minutes=30),
        id='follow_ups',
        name='Send Follow-up Emails',
        replace_existing=True,
    )
    scheduler.add_job(
        func=publish_approved_posts,
        args=[flask_app],
        trigger=CronTrigger(hour=23, minute=0, timezone='Europe/Dublin'),
        id='publish_posts',
        name='Publish Approved Posts to Buffer',
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()
    logger.info('APScheduler started with 4 autonomous jobs')


# ── Job: Daily Google Maps Scout ──────────────────────────────────────────────

def run_daily_scout(flask_app) -> None:
    """08:00 — Import new prospects from Google Maps for every active campaign."""
    with flask_app.app_context():
        try:
            from ..models.agency_outreach import OutreachCampaign
            from ..extensions import db
            from .agency_scout import AgencyScout

            if not AgencyScout.is_configured():
                logger.info('Scout skipped — GOOGLE_MAPS_API_KEY not set')
                return

            campaigns = OutreachCampaign.query.filter_by(status='active').all()
            if not campaigns:
                logger.info('Scout: no active campaigns found')
                return

            scout = AgencyScout()
            total = 0
            for campaign in campaigns:
                try:
                    count = scout.import_leads_for_campaign(campaign, limit=20)
                    total += count
                except Exception as exc:
                    logger.error(f'Scout failed for campaign {campaign.id}: {exc}')

            db.session.commit()
            logger.info(f'Scout complete: {total} new leads across {len(campaigns)} campaigns')

        except Exception as exc:
            logger.error(f'run_daily_scout failed: {exc}')


# ── Job: Check Email Replies ──────────────────────────────────────────────────

def check_email_replies(flask_app) -> None:
    """Every 15 min — poll IMAP for replies, run AI chat, send AI response."""
    with flask_app.app_context():
        try:
            from ..models.agency_outreach import OutreachLead
            from ..models.agency_conversation import AgencyConversation
            from ..extensions import db
            from .agency_email_service import AgencyEmailService
            from .agency_chat_manager import AgencyChatManager

            if not AgencyEmailService.is_configured():
                return

            svc      = AgencyEmailService()
            chat_mgr = AgencyChatManager()
            replies  = svc.check_replies(since_hours=1)

            for reply in replies:
                try:
                    lead = db.session.get(OutreachLead, reply['lead_id'])
                    if not lead:
                        continue

                    # Advance stage
                    if lead.stage in ('email_sequence', 'dm_sent', 'connected', 'queued_message'):
                        lead.stage = 'replied'
                        campaign = lead.campaign
                        if campaign:
                            campaign.leads_replied = (campaign.leads_replied or 0) + 1

                    # Find or start conversation
                    conv = (
                        AgencyConversation.query
                        .filter_by(lead_id=lead.id)
                        .order_by(AgencyConversation.created_at.desc())
                        .first()
                    )
                    if not conv:
                        conv = chat_mgr.start_conversation(lead, lead.campaign, flask_app)

                    # Get AI reply and send it
                    reply_text = chat_mgr.process_reply(conv, reply['body'], flask_app)
                    if reply_text and lead.email:
                        subject = f'Re: {reply["subject"]}' if reply.get('subject') else 'Following up'
                        svc.send_email(lead.email, subject, reply_text, lead_id=lead.id)

                except Exception as exc:
                    logger.error(f'Reply processing failed for lead {reply.get("lead_id")}: {exc}')

            db.session.commit()
            if replies:
                logger.info(f'Processed {len(replies)} email replies')

        except Exception as exc:
            logger.error(f'check_email_replies failed: {exc}')


# ── Job: Send Follow-up Emails ────────────────────────────────────────────────

def send_scheduled_follow_ups(flask_app) -> None:
    """Every 30 min — send Day-3 and Day-7 follow-up emails to leads in sequence."""
    with flask_app.app_context():
        try:
            from ..models.agency_outreach import OutreachLead
            from ..extensions import db
            from .agency_email_service import AgencyEmailService

            if not AgencyEmailService.is_configured():
                return

            now  = datetime.utcnow()
            svc  = AgencyEmailService()
            sent = 0

            # Day-3 follow-ups: step==1 AND sent >= 3 days ago
            day3_leads = OutreachLead.query.filter(
                OutreachLead.stage == 'email_sequence',
                OutreachLead.email_sequence_step == 1,
                OutreachLead.email_sent_at <= now - timedelta(days=3),
            ).all()

            for lead in day3_leads:
                try:
                    ok = svc.send_sequence_email(lead, step=2, campaign=lead.campaign)
                    if ok:
                        sent += 1
                except Exception as exc:
                    logger.error(f'Day-3 follow-up failed for lead {lead.id}: {exc}')

            # Day-7 close emails: step==2 AND sent >= 7 days ago
            day7_leads = OutreachLead.query.filter(
                OutreachLead.stage == 'email_sequence',
                OutreachLead.email_sequence_step == 2,
                OutreachLead.email_sent_at <= now - timedelta(days=7),
            ).all()

            for lead in day7_leads:
                try:
                    ok = svc.send_sequence_email(lead, step=3, campaign=lead.campaign)
                    if ok:
                        sent += 1
                except Exception as exc:
                    logger.error(f'Day-7 follow-up failed for lead {lead.id}: {exc}')

            if sent:
                db.session.commit()
                logger.info(f'Sent {sent} scheduled follow-up emails')

        except Exception as exc:
            logger.error(f'send_scheduled_follow_ups failed: {exc}')


# ── Job: Publish Approved Posts to Buffer ─────────────────────────────────────

def publish_approved_posts(flask_app) -> None:
    """23:00 — Push tomorrow's approved posts to Buffer + GDPR cleanup."""
    with flask_app.app_context():
        try:
            from ..extensions import db
            from ..config import Config
            from ..models.agency_client import AgencyClient
            from ..services.agency_client_manager import AgencyClientManager
            from ..services.agency_publisher import AgencyPublisher
            from ..models.task import TaskManager

            # 1. Push to Buffer
            if AgencyPublisher.is_configured():
                publisher = AgencyPublisher()
                result    = publisher.push_approved_posts(lookahead_days=1)
                db.session.commit()
                logger.info(f'Buffer publish: {result}')
            else:
                logger.info('Buffer not configured — skipping publish step')

            # 2. GDPR auto-purge: churned clients inactive > max age who requested deletion
            cutoff = datetime.utcnow() - timedelta(days=Config.AGENCY_MAX_CONTENT_AGE_DAYS)
            old_clients = AgencyClient.query.filter(
                AgencyClient.status == 'churned',
                AgencyClient.last_activity < cutoff,
                AgencyClient.data_deletion_requested == True,  # noqa: E712
            ).all()
            for client in old_clients:
                try:
                    AgencyClientManager.process_gdpr_deletion(client.id)
                except Exception as exc:
                    logger.error(f'GDPR purge failed for client {client.id}: {exc}')

            # 3. Clean up stale in-memory tasks
            TaskManager().cleanup_old_tasks(max_age_hours=48)

            logger.info('Nightly job complete')

        except Exception as exc:
            logger.error(f'publish_approved_posts job failed: {exc}')
