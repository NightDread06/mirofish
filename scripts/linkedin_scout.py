"""
LinkedIn Scout — local Playwright script.
Searches LinkedIn for prospects matching the campaign's business_type + target_city,
then POSTs them to the platform API as leads.

Usage:
    python linkedin_scout.py --campaign-id <uuid> [--limit 20] [--headless] [--dry-run]

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

LINKEDIN_LOGIN_URL  = 'https://www.linkedin.com/login'
LINKEDIN_SEARCH_URL = 'https://www.linkedin.com/search/results/companies/'


def pause(min_s=2, max_s=6):
    time.sleep(random.uniform(min_s, max_s))


def linkedin_login(page):
    print('[*] Logging in to LinkedIn…')
    page.goto(LINKEDIN_LOGIN_URL, wait_until='domcontentloaded')
    pause(1, 3)
    page.fill('#username', LINKEDIN_EMAIL)
    pause(0.5, 1.5)
    page.fill('#password', LINKEDIN_PASSWORD)
    pause(0.5, 1.5)
    page.click('button[type="submit"]')
    try:
        page.wait_for_url('**/feed/**', timeout=15_000)
        print('[+] Logged in successfully')
    except PWTimeout:
        # May land on checkpoint or 2-FA page
        print('[!] Login redirect timeout — check for 2FA or CAPTCHA challenge')
        print('    Current URL:', page.url)
        input('    Solve manually then press Enter to continue…')


def search_companies(page, business_type: str, city: str, limit: int) -> list[dict]:
    """Scrape LinkedIn company search results."""
    query = f'{business_type} {city}'
    url = f'{LINKEDIN_SEARCH_URL}?keywords={requests.utils.quote(query)}&origin=GLOBAL_SEARCH_HEADER'
    print(f'[*] Searching: {query}')
    page.goto(url, wait_until='domcontentloaded')
    pause(3, 6)

    results = []
    page_num = 1

    while len(results) < limit:
        # Scroll to load lazy content
        for _ in range(3):
            page.evaluate('window.scrollBy(0, 600)')
            pause(0.8, 1.5)

        cards = page.query_selector_all('li.reusable-search__result-container')
        print(f'    Page {page_num}: found {len(cards)} cards')

        for card in cards:
            if len(results) >= limit:
                break
            try:
                name_el = card.query_selector('span.entity-result__title-text a span[aria-hidden="true"]')
                link_el = card.query_selector('span.entity-result__title-text a')
                sub_el  = card.query_selector('div.entity-result__primary-subtitle')
                loc_el  = card.query_selector('div.entity-result__secondary-subtitle')

                name    = name_el.inner_text().strip() if name_el else None
                profile = link_el.get_attribute('href').split('?')[0] if link_el else None
                industry = sub_el.inner_text().strip() if sub_el else ''
                location = loc_el.inner_text().strip() if loc_el else city

                if not name or not profile:
                    continue

                results.append({
                    'business_name': name,
                    'linkedin_url': profile,
                    'city': location or city,
                    'notes': industry,
                    'source': 'linkedin_script',
                })
            except Exception as exc:
                print(f'    [!] Card parse error: {exc}')

        # Next page
        next_btn = page.query_selector('button[aria-label="Next"]')
        if next_btn and len(results) < limit:
            next_btn.click()
            pause(3, 7)
            page_num += 1
        else:
            break

    return results[:limit]


def post_leads(campaign_id: str, leads: list[dict]) -> dict:
    url = f'{API_BASE_URL}/api/agency/outreach/campaign/{campaign_id}/leads'
    headers = {'Authorization': f'Bearer {API_TOKEN}', 'Content-Type': 'application/json'}
    resp = requests.post(url, json={'leads': leads}, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_campaign(campaign_id: str) -> dict:
    url = f'{API_BASE_URL}/api/agency/outreach/campaign/{campaign_id}'
    headers = {'Authorization': f'Bearer {API_TOKEN}'}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get('data', {})


def main():
    parser = argparse.ArgumentParser(description='LinkedIn company scout → platform leads')
    parser.add_argument('--campaign-id', required=True, help='Campaign UUID')
    parser.add_argument('--limit', type=int, default=20, help='Max prospects to collect (default 20)')
    parser.add_argument('--headless', action='store_true', help='Run browser headlessly')
    parser.add_argument('--dry-run', action='store_true', help='Print results, do NOT post to API')
    args = parser.parse_args()

    # Validate env
    missing = [v for v in ('LINKEDIN_EMAIL', 'LINKEDIN_PASSWORD', 'API_BASE_URL', 'API_TOKEN')
               if not os.getenv(v)]
    if missing and not args.dry_run:
        print(f'[!] Missing env vars: {", ".join(missing)}')
        print('    Set them in your .env file (see .env.example)')
        sys.exit(1)

    # Fetch campaign info
    if not args.dry_run:
        try:
            campaign = get_campaign(args.campaign_id)
            business_type = campaign.get('business_type', 'gym')
            city          = campaign.get('target_city', 'Dublin')
            print(f'[*] Campaign: {campaign.get("name")} | {business_type} | {city}')
        except Exception as exc:
            print(f'[!] Could not fetch campaign: {exc}')
            sys.exit(1)
    else:
        business_type = 'gym'
        city          = 'Dublin'
        print('[DRY RUN] Using dummy business_type=gym, city=Dublin')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=args.headless, slow_mo=50)
        ctx     = browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            )
        )
        page = ctx.new_page()

        try:
            if not args.dry_run:
                linkedin_login(page)
                pause(2, 4)

            leads = search_companies(page, business_type, city, args.limit)

        finally:
            browser.close()

    print(f'\n[*] Collected {len(leads)} leads:')
    for i, lead in enumerate(leads, 1):
        print(f'  {i:2}. {lead["business_name"]:40} {lead.get("city", ""):<20} {lead.get("linkedin_url", "")[:60]}')

    if args.dry_run:
        print('\n[DRY RUN] Not posting to API.')
        return

    if not leads:
        print('[*] No leads to import.')
        return

    try:
        result = post_leads(args.campaign_id, leads)
        created = result.get('data', {}).get('created', 0)
        print(f'\n[+] Imported {created} new leads into campaign.')
    except requests.HTTPError as exc:
        print(f'[!] API error: {exc.response.status_code} {exc.response.text}')
        sys.exit(1)


if __name__ == '__main__':
    main()
