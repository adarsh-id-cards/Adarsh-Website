"""
Impersonation Service — Pro User only.
Simplified for Website Management.
"""
import logging
from django.contrib.auth import get_user_model, login

logger = logging.getLogger(__name__)
User = get_user_model()

class ImpersonateService:
    SESSION_KEY = '_pro_original_user_id'
    SESSION_NAME_KEY = '_pro_original_user_name'

    @classmethod
    def can_impersonate(cls, user) -> bool:
        return user.is_authenticated and user.role == 'pro_user'

    @classmethod
    def is_impersonating(cls, request) -> bool:
        return bool(request.session.get(cls.SESSION_KEY))

    @classmethod
    def start(cls, request, target_user_id: int) -> dict:
        current_user = request.user
        if not cls.can_impersonate(current_user):
            return {'success': False, 'message': 'Permission denied.'}
        if current_user.pk == target_user_id:
            return {'success': False, 'message': 'Cannot impersonate yourself.'}
        if cls.is_impersonating(request):
            return {'success': False, 'message': 'Already impersonating.'}

        try:
            target_user = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return {'success': False, 'message': 'User not found.'}

        if not target_user.is_active:
            return {'success': False, 'message': 'User is inactive.'}

        oid, oname = current_user.pk, (current_user.get_full_name() or current_user.username)
        request._skip_device_session_enforcement = True
        login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')
        request.session[cls.SESSION_KEY] = oid
        request.session[cls.SESSION_NAME_KEY] = oname

        try:
            from core.middleware import PermissionValidationMiddleware
            PermissionValidationMiddleware.seed_session_fingerprint(request)
        except: pass

        from .services import DASHBOARD_URLS
        return {
            'success': True,
            'message': f'Impersonating {target_user.get_full_name() or target_user.username}',
            'redirect_url': DASHBOARD_URLS.get(target_user.role, '/panel/'),
        }

    @classmethod
    def stop(cls, request, next_url: str = '') -> dict:
        oid = request.session.get(cls.SESSION_KEY)
        if not oid:
            return {'success': False, 'message': 'Not impersonating.'}
        try:
            original_user = User.objects.get(pk=oid, role='pro_user')
        except User.DoesNotExist:
            return {'success': False, 'message': 'Original account not found.'}

        request._skip_device_session_enforcement = True
        login(request, original_user, backend='django.contrib.auth.backends.ModelBackend')
        try:
            from core.middleware import PermissionValidationMiddleware
            PermissionValidationMiddleware.seed_session_fingerprint(request)
        except: pass

        from .services import DASHBOARD_URLS
        redirect_url = next_url if (next_url and next_url.startswith('/')) else DASHBOARD_URLS.get('pro_user', '/panel/')
        return {'success': True, 'message': 'Stopped impersonation.', 'redirect_url': redirect_url}

    @classmethod
    def get_impersonation_targets(cls, request) -> list:
        if not cls.can_impersonate(request.user):
            return []
        users = User.objects.filter(is_active=True).exclude(pk=request.user.pk).order_by('role', 'username')
        return [{
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'email': u.email,
            'role': u.role,
            'role_display': dict(User.ROLE_CHOICES).get(u.role, u.role),
        } for u in users]
