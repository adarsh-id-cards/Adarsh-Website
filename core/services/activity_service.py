"""
Activity Logging Service
Simplified for Website Management.
"""
import logging
import ipaddress
from django.conf import settings
from django.utils import timezone
from django.utils.timesince import timesince
from core.models import ActivityLog

logger = logging.getLogger(__name__)

class ActivityService:
    @staticmethod
    def _get_ip(request):
        if request is None: return None
        try:
            from accounts.rate_limit import _get_client_ip
            return _get_client_ip(request)
        except ImportError:
            return request.META.get('HTTP_X_REAL_IP') or request.META.get('REMOTE_ADDR')

    @classmethod
    def log(cls, action, description, user=None, request=None, target_model='', target_id=None, target_name=''):
        try:
            if user is None and request is not None:
                user = getattr(request, 'user', None)
                if user and not user.is_authenticated: user = None
            ActivityLog.objects.create(
                user=user, action=action, description=description,
                target_model=target_model, target_id=target_id, target_name=target_name,
                ip_address=cls._get_ip(request)
            )
        except Exception:
            logger.exception('Failed to write activity log')

    @classmethod
    def log_login(cls, request, user):
        from accounts.services import AuthService
        description = f'{user.username} logged in'
        if request is not None:
            ua = request.META.get('HTTP_USER_AGENT', '')
            lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            current_fp = AuthService.build_browser_fingerprint(ua, lang)
            current_session_key = getattr(getattr(request, 'session', None), 'session_key', '') or ''
            inspection = AuthService.inspect_active_sessions_for_user(
                user.id,
                browser_fingerprint=current_fp,
                exclude_session_key=current_session_key
            )
            if inspection.get('has_different_browser'):
                description = f'{user.username} logged in from a different browser'
        cls.log('login', description, user=user, request=request)

    @classmethod
    def log_logout(cls, request, user):
        cls.log('logout', f'{user.username} logged out', user=user, request=request)

    @classmethod
    def log_website_update(cls, request, description):
        """Log a website content update action from the manage_website dashboard."""
        user = getattr(request, 'user', None)
        cls.log('website_update', description, user=user, request=request, target_model='website')

    @classmethod
    def get_recent(cls, limit=8, hours=None, user=None):
        qs = ActivityLog.objects.select_related('user').order_by('-created_at')
        if hours:
            cutoff = timezone.now() - timezone.timedelta(hours=hours)
            qs = qs.filter(created_at__gte=cutoff)
        
        now = timezone.now()
        results = []
        for entry in qs[:limit]:
            results.append({
                'id': entry.pk,
                'actor': (entry.user.get_full_name() or entry.user.username) if entry.user else 'System',
                'action': entry.action,
                'description': entry.description,
                'icon_class': entry.icon_class,
                'icon_color': entry.icon_color,
                'time_ago': timesince(entry.created_at, now),
                'created_at': entry.created_at.isoformat(),
            })
        return results

    @classmethod
    def cleanup_old(cls, days=30):
        cutoff = timezone.now() - timezone.timedelta(days=days)
        deleted, _ = ActivityLog.objects.filter(created_at__lt=cutoff).delete()
        return deleted
