"""
Agency client lifecycle management service.

Handles: onboarding, profile updates, GDPR erasure, inactive-client purging,
and admin dashboard metrics aggregation.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ..extensions import db
from ..models.agency_auth import AgencyUser
from ..models.agency_client import AgencyClient
from ..models.agency_content import ContentPackage
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.client_manager')


class AgencyClientManager:

    # ── Read ──────────────────────────────────────────────────────────────────

    @staticmethod
    def get_client(client_id: str) -> Optional[AgencyClient]:
        return AgencyClient.query.filter_by(id=client_id).first()

    @staticmethod
    def get_client_by_user(client_id: str, user_id: int) -> Optional[AgencyClient]:
        return AgencyClient.query.filter_by(id=client_id, user_id=user_id).first()

    @staticmethod
    def list_clients(status: Optional[str] = None, limit: int = 100) -> List[AgencyClient]:
        q = AgencyClient.query
        if status:
            q = q.filter_by(status=status)
        return q.order_by(AgencyClient.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_client_for_user(user_id: int) -> Optional[AgencyClient]:
        """Return the single client profile linked to this user account."""
        return AgencyClient.query.filter_by(user_id=user_id).first()

    # ── Create / update ───────────────────────────────────────────────────────

    @staticmethod
    def create_client(data: Dict, user_id: Optional[int] = None) -> AgencyClient:
        client = AgencyClient(
            user_id=user_id,
            business_name=data['business_name'],
            business_type=data.get('business_type', 'other'),
            city=data.get('city', ''),
            country=data.get('country', 'IE'),
            email=data['email'],
            tone=data.get('tone', 'friendly'),
            target_audience=data.get('target_audience', ''),
            competitors=data.get('competitors', ''),
            brand_keywords=data.get('brand_keywords', ''),
            linkedin_url=data.get('linkedin_url', ''),
            instagram_handle=data.get('instagram_handle', ''),
            facebook_page=data.get('facebook_page', ''),
            status='onboarding',
            plan=data.get('plan', 'pilot'),
            gdpr_consent=bool(data.get('gdpr_consent', False)),
            gdpr_consent_at=datetime.utcnow() if data.get('gdpr_consent') else None,
        )
        db.session.add(client)
        db.session.commit()
        return client

    @staticmethod
    def update_status(client_id: str, status: str) -> bool:
        client = AgencyClient.query.filter_by(id=client_id).first()
        if not client:
            return False
        client.status = status
        client.last_activity = datetime.utcnow()
        db.session.commit()
        return True

    # ── GDPR ──────────────────────────────────────────────────────────────────

    @staticmethod
    def process_gdpr_deletion(client_id: str) -> bool:
        """
        GDPR Article 17 — Right to Erasure.
        Immediately anonymises all PII fields.
        Hard-deletes all content packages.
        """
        client = AgencyClient.query.filter_by(id=client_id).first()
        if not client:
            return False

        # Anonymise PII
        client.email = f'deleted_{client_id[:8]}@deleted.invalid'
        client.target_audience = None
        client.competitors = None
        client.brand_keywords = None
        client.linkedin_url = None
        client.instagram_handle = None
        client.facebook_page = None
        client.data_deletion_requested = True
        client.status = 'churned'

        # Hard-delete content packages (cascades to posts via relationship)
        ContentPackage.query.filter_by(client_id=client_id).delete()
        db.session.commit()

        # Also unlink user account if present
        if client.user_id:
            user = AgencyUser.query.get(client.user_id)
            if user:
                user.is_active = False
                db.session.commit()

        logger.info(f'GDPR deletion processed for client {client_id[:8]}…')
        return True

    @staticmethod
    def export_client_data(client_id: str) -> Optional[Dict]:
        """GDPR Article 20 — Data portability. Returns all stored data as a dict."""
        client = AgencyClient.query.filter_by(id=client_id).first()
        if not client:
            return None

        packages = []
        for pkg in client.content_packages:
            packages.append({
                **pkg.to_dict(),
                'posts': [p.to_dict() for p in pkg.posts],
            })

        return {
            'client': client.to_dict(include_sensitive=True),
            'content_packages': packages,
        }

    # ── Auto-purge ────────────────────────────────────────────────────────────

    @staticmethod
    def purge_inactive_clients(max_age_days: int = 90) -> int:
        """
        GDPR data minimisation: erase churned clients inactive for max_age_days.
        Returns the number of clients purged.
        """
        from ..config import Config
        days = max_age_days or Config.AGENCY_MAX_CONTENT_AGE_DAYS
        cutoff = datetime.utcnow() - timedelta(days=days)
        inactive = AgencyClient.query.filter(
            AgencyClient.last_activity < cutoff,
            AgencyClient.status == 'churned',
            AgencyClient.data_deletion_requested == False,  # noqa: E712
        ).all()
        for client in inactive:
            AgencyClientManager.process_gdpr_deletion(client.id)
        if inactive:
            logger.info(f'Auto-purged {len(inactive)} inactive client records')
        return len(inactive)

    # ── Admin dashboard ───────────────────────────────────────────────────────

    @staticmethod
    def get_dashboard_metrics() -> Dict:
        total     = AgencyClient.query.filter(
            AgencyClient.status.in_(['active', 'onboarding'])
        ).count()
        active    = AgencyClient.query.filter_by(status='active').count()
        pilot     = AgencyClient.query.filter_by(plan='pilot', status='active').count()
        retainer  = AgencyClient.query.filter_by(plan='retainer', status='active').count()
        mrr       = pilot * 500 + retainer * 1500
        packages  = ContentPackage.query.filter_by(status='completed').count()

        return {
            'total_clients': total,
            'active_clients': active,
            'pilot_clients': pilot,
            'retainer_clients': retainer,
            'mrr_eur': mrr,
            'packages_generated': packages,
        }
