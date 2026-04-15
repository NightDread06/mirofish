"""
Agency Email Service — SMTP sending and IMAP reply polling.

Sends outreach email sequences via smtplib (no third-party service needed).
Polls the inbox via imaplib for replies from leads.
Uses X-MiroFish-Lead-ID header to match replies back to leads.

Gmail setup:
  1. Enable 2-FA on your Google account
  2. Go to myaccount.google.com → Security → App Passwords
  3. Generate an app password for "Mail"
  4. Set SMTP_PASSWORD and IMAP_PASSWORD to that 16-char app password
"""

import email
import imaplib
import re
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.email')


class AgencyEmailService:
    """SMTP send + IMAP reply detection for the autonomous outreach sequence."""

    def __init__(self):
        self._smtp_host     = Config.SMTP_HOST
        self._smtp_port     = Config.SMTP_PORT
        self._smtp_user     = Config.SMTP_USER
        self._smtp_password = Config.SMTP_PASSWORD
        self._from_name     = Config.SMTP_FROM_NAME
        self._imap_host     = Config.IMAP_HOST
        self._imap_user     = Config.IMAP_USER
        self._imap_password = Config.IMAP_PASSWORD

    # ── Sending ───────────────────────────────────────────────────────────────

    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        reply_to: str | None = None,
        lead_id: str | None = None,
    ) -> bool:
        """
        Send a plain-text email via SMTP STARTTLS.
        Adds X-MiroFish-Lead-ID header so IMAP polling can match replies.
        Returns True on success, False on failure.
        """
        if not self._smtp_user or not self._smtp_password:
            logger.warning('SMTP not configured — skipping send_email()')
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From']    = f'{self._from_name} <{self._smtp_user}>'
            msg['To']      = to_address
            if reply_to:
                msg['Reply-To'] = reply_to
            if lead_id:
                msg['X-MiroFish-Lead-ID'] = lead_id

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            context = ssl.create_default_context()
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(self._smtp_user, self._smtp_password)
                server.sendmail(self._smtp_user, to_address, msg.as_string())

            logger.info(f'Email sent to {to_address} | lead_id={lead_id}')
            return True

        except Exception as exc:
            logger.error(f'send_email failed to {to_address}: {exc}')
            return False

    def send_sequence_email(self, lead, step: int, campaign) -> bool:
        """
        Send the correct sequence step email for a lead.
        step=1 → Day 0 (initial), step=2 → Day 3 follow-up, step=3 → Day 7 close.
        Updates lead.email_sequence_step and email_sent_at on success.
        Caller must commit the DB session.
        """
        if not lead.email:
            logger.warning(f'Lead {lead.id} has no email — skipping sequence email')
            return False

        templates = {
            1: (campaign.email_template_1_subject, campaign.email_template_1_body),
            2: (campaign.email_template_2_subject, campaign.email_template_2_body),
            3: (campaign.email_template_3_subject, campaign.email_template_3_body),
        }
        subject_tpl, body_tpl = templates.get(step, (None, None))
        if not subject_tpl or not body_tpl:
            logger.warning(f'Campaign {campaign.id} has no email template for step {step}')
            return False

        first_name = (lead.first_name or 'there').split()[0]
        subject = subject_tpl.replace('{first_name}', first_name)
        body    = body_tpl.replace('{first_name}', first_name)

        sent = self.send_email(
            to_address=lead.email,
            subject=subject,
            body=body,
            lead_id=lead.id,
        )
        if sent:
            lead.email_sequence_step = step
            lead.email_sent_at       = datetime.utcnow()
        return sent

    # ── Receiving ─────────────────────────────────────────────────────────────

    def check_replies(self, since_hours: int = 1) -> list[dict]:
        """
        Connect to IMAP, fetch UNSEEN messages from the last `since_hours`.
        Match each message to a lead via X-MiroFish-Lead-ID header or sender email.
        Returns list of {lead_id, from_email, subject, body}.
        Marks matched messages as SEEN.
        """
        if not self._imap_user or not self._imap_password:
            logger.warning('IMAP not configured — skipping check_replies()')
            return []

        replies = []
        try:
            mail = imaplib.IMAP4_SSL(self._imap_host)
            mail.login(self._imap_user, self._imap_password)
            mail.select('INBOX')

            # Search for UNSEEN messages
            _, data = mail.search(None, 'UNSEEN')
            msg_ids = data[0].split()
            if not msg_ids:
                mail.logout()
                return []

            # Lazy import to avoid circular at module load time
            from ..models.agency_outreach import OutreachLead

            for num in msg_ids:
                _, msg_data = mail.fetch(num, '(RFC822)')
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                from_email = email.utils.parseaddr(msg.get('From', ''))[1]
                subject    = msg.get('Subject', '')
                lead_id    = msg.get('X-MiroFish-Lead-ID', '')

                # Extract plain text body
                body = ''
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == 'text/plain':
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode('utf-8', errors='replace')
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='replace')

                # Resolve lead_id by header or sender email
                if not lead_id and from_email:
                    lead = OutreachLead.query.filter_by(email=from_email).first()
                    if lead:
                        lead_id = lead.id

                if lead_id:
                    replies.append({
                        'lead_id':    lead_id,
                        'from_email': from_email,
                        'subject':    subject,
                        'body':       body[:4000],  # cap to avoid huge prompts
                    })
                    mail.store(num, '+FLAGS', '\\Seen')
                    logger.info(f'Reply matched to lead {lead_id} from {from_email}')
                else:
                    logger.debug(f'IMAP message from {from_email} not matched to any lead')

            mail.logout()

        except Exception as exc:
            logger.error(f'check_replies failed: {exc}')

        return replies

    # ── Helper ────────────────────────────────────────────────────────────────

    @staticmethod
    def is_configured() -> bool:
        return bool(Config.SMTP_USER and Config.SMTP_PASSWORD)
