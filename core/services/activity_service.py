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
        cls.log('login', f'{user.username} logged in', user=user, request=request)

    @classmethod
    def log_logout(cls, request, user):
        cls.log('logout', f'{user.username} logged out', user=user, request=request)

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
