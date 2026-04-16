"""
LinkedIn Sender — local Playwright script.
Fetches leads with stage='queued_message' from the platform API,
opens each LinkedIn profile, and sends a connection request with a
personalised note (stored in lead.notes by the platform).

Includes 30–90 s random delays between sends and caps at 20 sends per session
to avoid triggering LinkedIn's automation detection.

Usage:
    python linkedin_sender.py --campaign-id <uuid> [--max 20] [--headless] [--dry-run]

Requirements:
    pip install -r requirements.txt
    playwright install chromium

Env vars (from .env in this directory or parent):
    LINKEDIN_EMAIL     your LinkedIn login email
    LINKEDIN_PASSWORD  your LinkedIn login password
    API_BASE_URL       e.g. http://localhost:3000
    API_TOKEN          admin JWT (copy from browser localStorage after login)
"""

import argparse
import json
import os
import random
import sys
import time

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# Load .env from script directory, then project root
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

LINKEDIN_EMAIL    = os.getenv('LINKEDIN_EMAIL', '')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD', '')
API_BASE_URL      = os.getenv('API_BASE_URL', 'http://localhost:3000')
API_TOKEN         = os.getenv('API_TOKEN', '')

MAX_NOTE_LENGTH = 300  # LinkedIn connection note limit

LINKEDIN_LOGIN_URL = 'https://www.linkedin.com/login'


def pause(min_s=30, max_s=90):
    """Human-paced delay between actions to avoid detection."""
    delay = random.uniform(min_s, max_s)
    print(f'    [~] Waiting {delay:.0f}s…')
    time.sleep(delay)


def short_pause(min_s=2, max_s=6):
    time.sleep(random.uniform(min_s, max_s))


def linkedin_login(page):
    print('[*] Logging in to LinkedIn…')
    page.goto(LINKEDIN_LOGIN_URL, wait_until='domcontentloaded')
    short_pause(1, 3)
    page.fill('#username', LINKEDIN_EMAIL)
    short_pause(0.5, 1.5)
    page.fill('#password', LINKEDIN_PASSWORD)
    short_pause(0.5, 1.5)
    page.click('button[type="submit"]')
    try:
        page.wait_for_url('**/feed/**', timeout=20_000)
        print('[+] Logged in')
    except PWTimeout:
        print('[!] Login redirect timeout — check for 2FA or CAPTCHA challenge')
        print('    Current URL:', page.url)
        input('    Solve manually then press Enter to continue…')


def fetch_queued_leads(campaign_id: str) -> list[dict]:
    url = f'{API_BASE_URL}/api/agency/outreach/campaign/{campaign_id}/leads'
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    resp = requests.get(url, params={'stage': 'queued_message', 'limit': 100}, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get('data', [])


def update_lead_stage(lead_id: str, stage: str, notes: str = None):
    url = f'{API_BASE_URL}/api/agency/outreach/leads/{lead_id}'
    headers = {'Authorization': f'Bearer {API_TOKEN}', 'Content-Type': 'application/json'}
    payload = {'stage': stage}
    if notes:
        payload['notes'] = notes
    resp = requests.patch(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()


def send_connection_request(page, linkedin_url: str, note: str) -> bool:
    """
    Visit a LinkedIn profile and send a connection request with the given note.
    Returns True if sent successfully, False otherwise.
    """
    print(f'    [*] Opening: {linkedin_url}')
    page.goto(linkedin_url, wait_until='domcontentloaded')
    short_pause(3, 6)

    # Try to find the Connect button on the profile
    connect_btn = None

    # Primary location: main action buttons
    for selector in [
        'button.pvs-profile-actions__action:has-text("Connect")',
        'button[aria-label*="Connect with"]',
        'button:has-text("Connect")',
    ]:
        try:
            btn = page.wait_for_selector(selector, timeout=5_000)
            if btn and btn.is_visible():
                connect_btn = btn
                break
        except PWTimeout:
            continue

    # Fallback: check "More" dropdown
    if not connect_btn:
        try:
            more_btn = page.query_selector('button[aria-label="More actions"]')
            if more_btn:
                more_btn.click()
                short_pause(1, 2)
                connect_btn = page.wait_for_selector('div[aria-label*="Connect"]', timeout=4_000)
        except (PWTimeout, Exception):
            pass

    if not connect_btn:
        print('    [!] Connect button not found — may already be connected or profile unavailable')
        return False

    connect_btn.click()
    short_pause(1, 2)

    # Add a note if the dialog appears
    try:
        add_note_btn = page.wait_for_selector('button[aria-label="Add a note"]', timeout=5_000)
        add_note_btn.click()
        short_pause(0.5, 1.5)

        note_input = page.wait_for_selector('textarea[name="message"]', timeout=5_000)
        truncated  = note[:MAX_NOTE_LENGTH]
        note_input.fill(truncated)
        short_pause(0.5, 1.0)

        send_btn = page.wait_for_selector('button[aria-label="Send now"]', timeout=5_000)
        send_btn.click()
        short_pause(1, 2)
        print('    [+] Connection request sent with note')
        return True

    except PWTimeout:
        # Some accounts show "Send without a note" flow
        try:
            send_btn = page.wait_for_selector('button[aria-label="Send without a note"]', timeout=5_000)
            send_btn.click()
            short_pause(1, 2)
            print('    [+] Connection request sent (without note)')
            return True
        except PWTimeout:
            print('    [!] Could not complete send — dialog did not appear as expected')
            return False


def main():
    parser = argparse.ArgumentParser(description='LinkedIn connection sender for queued_message leads')
    parser.add_argument('--campaign-id', required=True, help='Campaign UUID')
    parser.add_argument('--max', type=int, default=20, help='Max sends per session (default 20, LinkedIn safe limit)')
    parser.add_argument('--headless', action='store_true', help='Run browser headlessly (not recommended for LinkedIn)')
    parser.add_argument('--dry-run', action='store_true', help='Fetch leads and print, do NOT send or update')
    args = parser.parse_args()

    missing = [v for v in ('LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD', 'API_BASE_URL', 'API_TOKEN')
               if not os.getenv(v)]
    if missing and not args.dry_run:
        print(f'[!] Missing env vars: {", ".join(missing)}')
        sys.exit(1)

    print(f'[*] Fetching queued_message leads for campaign {args.campaign_id}…')
    try:
        leads = fetch_queued_leads(args.campaign_id)
    except Exception as exc:
        print(f'[!] Could not fetch leads: {exc}')
        sys.exit(1)

    if not leads:
        print('[*] No leads with stage=queued_message. Nothing to do.')
        return

    leads = leads[:args.max]
    print(f'[*] Will process {len(leads)} lead(s) (max {args.max} per session)\n')

    for i, lead in enumerate(leads, 1):
        name     = lead.get('first_name') or 'there'
        biz      = lead.get('business_name', '')
        li_url   = lead.get('linkedin_url', '')
        note_txt = (lead.get('notes') or '').strip()

        print(f'  [{i}/{len(leads)}] {name} — {biz}')

        if not li_url:
            print('    [!] No LinkedIn URL — skipping')
            continue

        if args.dry_run:
            print(f'    [DRY] Would send to: {li_url}')
            print(f'    [DRY] Note: {note_txt[:100]}…')
            continue

        # Only login once — reuse context across leads
        if i == 1:
            pw_ctx = sync_playwright().__enter__()
            browser = pw_ctx.chromium.launch(headless=args.headless, slow_mo=80)
            ctx     = browser.new_context(
                user_agent=(
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/124.0.0.0 Safari/537.36'
                )
            )
            page = ctx.new_page()
            linkedin_login(page)
            short_pause(3, 6)

        try:
            sent = send_connection_request(page, li_url, note_txt)
            new_stage = 'connection_sent' if sent else 'queued_message'
            update_lead_stage(lead['id'], new_stage)
            print(f'    → Stage updated to: {new_stage}')
        except Exception as exc:
            print(f'    [!] Error: {exc}')

        # Rate-limiting delay between sends (skip after last lead)
        if i < len(leads):
            pause(30, 90)

    if not args.dry_run and len(leads) > 0:
        try:
            browser.close()
            pw_ctx.__exit__(None, None, None)
        except Exception:
            pass

    print(f'\n[+] Session complete. Processed {len(leads)} lead(s).')
    if not args.dry_run:
        print('    Check LinkedIn for any warnings or rate-limit notifications.')


if __name__ == '__main__':
    main()
