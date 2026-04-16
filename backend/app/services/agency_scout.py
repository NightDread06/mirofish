"""
Agency Scout — Google Maps Places API prospect discovery.

Searches for local businesses by type and city, deduplicates against
existing leads, and imports new prospects into the campaign automatically.
Uses the existing AgencyOutreachManager to generate personalised openers.

Google Maps setup:
  1. Go to console.cloud.google.com
  2. Enable "Places API"
  3. Create an API key and set GOOGLE_MAPS_API_KEY in .env
  Free tier: 28,500 requests/month
"""

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.scout')

# Maps agency business_type values to Google Places query terms
_SEARCH_QUERIES = {
    'gym':         ['gym', 'fitness studio', 'crossfit', 'personal trainer'],
    'salon':       ['hair salon', 'beauty salon', 'barber shop'],
    'restaurant':  ['restaurant', 'cafe', 'bistro'],
    'clinic':      ['dental clinic', 'medical clinic', 'physio clinic'],
    'real_estate': ['estate agent', 'real estate agency'],
    'other':       ['local business'],
}


class AgencyScout:
    """Automated prospect discovery via Google Maps Places API."""

    def __init__(self):
        if not Config.GOOGLE_MAPS_API_KEY:
            raise RuntimeError('GOOGLE_MAPS_API_KEY not configured')
        import googlemaps
        self._gmaps = googlemaps.Client(key=Config.GOOGLE_MAPS_API_KEY)

    def search_businesses(
        self,
        business_type: str,
        city: str,
        limit: int = 20,
    ) -> list[dict]:
        """
        Search Google Maps Places for businesses of the given type in the city.
        Returns up to `limit` results as dicts with name, address, website, phone, rating.
        """
        queries = _SEARCH_QUERIES.get(business_type, [business_type])
        results = []
        seen_ids = set()

        for query_term in queries:
            if len(results) >= limit:
                break
            try:
                response = self._gmaps.places(
                    query=f'{query_term} in {city}',
                    type='establishment',
                )
                for place in response.get('results', []):
                    pid = place.get('place_id', '')
                    if pid in seen_ids or len(results) >= limit:
                        continue
                    seen_ids.add(pid)

                    # Fetch details for phone + website
                    details = {}
                    try:
                        det = self._gmaps.place(
                            place_id=pid,
                            fields=['formatted_phone_number', 'website'],
                        )
                        details = det.get('result', {})
                    except Exception:
                        pass

                    results.append({
                        'name':            place.get('name', ''),
                        'address':         place.get('formatted_address', ''),
                        'website':         details.get('website'),
                        'phone':           details.get('formatted_phone_number'),
                        'rating':          place.get('rating'),
                        'google_place_id': pid,
                    })

            except Exception as exc:
                logger.error(f'Google Maps search failed for "{query_term}" in {city}: {exc}')

        logger.info(f'Scout found {len(results)} businesses for {business_type} in {city}')
        return results

    def import_leads_for_campaign(self, campaign, limit: int = 20) -> int:
        """
        Search for businesses matching the campaign's type and city.
        Deduplicate against existing leads (case-insensitive business_name match).
        Create OutreachLead rows for new prospects.
        Generate a personalised opener for each and store in lead.notes.
        Returns count of new leads created (caller must db.session.commit()).
        """
        from ..models.agency_outreach import OutreachLead
        from ..extensions import db
        from .agency_outreach_manager import AgencyOutreachManager

        businesses = self.search_businesses(campaign.business_type, campaign.target_city, limit)
        if not businesses:
            return 0

        # Load existing business names for deduplication
        existing_names = {
            r.business_name.lower()
            for r in OutreachLead.query.filter_by(campaign_id=campaign.id)
            .with_entities(OutreachLead.business_name).all()
            if r.business_name
        }

        outreach_mgr = AgencyOutreachManager()
        created = 0

        for biz in businesses:
            name = biz['name']
            if not name or name.lower() in existing_names:
                continue

            # Generate a personalised opener
            opener = ''
            try:
                opener = outreach_mgr.generate_personalised_opener({
                    'business_name': name,
                    'business_type': campaign.business_type,
                    'city': campaign.target_city,
                    'observation': f'Found on Google Maps — rated {biz["rating"]}' if biz.get('rating') else '',
                })
            except Exception as exc:
                logger.warning(f'Opener generation failed for {name}: {exc}')
                opener = f'Found via Google Maps in {campaign.target_city}.'

            lead = OutreachLead(
                campaign_id   = campaign.id,
                business_name = name[:255],
                city          = campaign.target_city,
                source        = 'google_maps',
                stage         = 'imported',
                notes         = opener[:2000] if opener else '',
            )
            db.session.add(lead)
            existing_names.add(name.lower())
            created += 1

        if created:
            campaign.leads_total = (campaign.leads_total or 0) + created
            logger.info(f'Scout imported {created} new leads for campaign {campaign.id}')

        return created

    @staticmethod
    def is_configured() -> bool:
        return bool(Config.GOOGLE_MAPS_API_KEY)
