"""
Permission Service Module — SINGLE AUTHORITY FOR ALL PERMISSION DECISIONS.
Simplified for Website Management.
"""
import logging
from typing import Dict, List
from functools import wraps

from django.core.cache import cache as _cache
from django.http import JsonResponse
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

class PermissionService:
    """
    Single authority for all permission decisions.
    Roles: admin, pro, operator
    """

    PERMISSION_CONTEXT_CACHE_TTL = 30

    WEBSITE_PERMISSIONS = [
        'perm_website_view', 'perm_website_add', 'perm_website_edit',
        'perm_website_delete', 'perm_website_publish',
    ]

    MANAGE_PANEL_PERMISSIONS = [
        'perm_manage_panel_email',
    ]

    ACCOUNT_SECURITY_PERMISSIONS = [
        'perm_set_temp_password',
    ]
    
    PRO_ONLY_PERMISSIONS = [
        'perm_pro_extra_features',
    ]

    ALL_PERMISSION_KEYS: List[str] = (
        WEBSITE_PERMISSIONS
        + MANAGE_PANEL_PERMISSIONS
        + ACCOUNT_SECURITY_PERMISSIONS
        + PRO_ONLY_PERMISSIONS
    )

    @staticmethod
    def is_pro(user) -> bool:
        return user.is_authenticated and user.role == 'pro'

    @staticmethod
    def is_admin(user) -> bool:
        # Admin has all rights
        return user.is_authenticated and (user.is_superuser or user.role == 'admin')

    @staticmethod
    def is_operator(user) -> bool:
        return user.is_authenticated and user.role == 'operator'

    @staticmethod
    def is_any_admin(user) -> bool:
        if not user.is_authenticated:
            return False
        # All 3 roles are considered "admin" in terms of panel access
        return user.role in ('admin', 'pro', 'operator')

    @classmethod
    def has(cls, user, perm_key: str) -> bool:
        if not user.is_authenticated or not user.is_active:
            return False
        
        # Admin has absolute access
        if cls.is_admin(user):
            return True
            
        # Pro has everything except maybe some system-level things, but per user request "same as admin"
        if cls.is_pro(user):
            return True
            
        # Operator has only permitted features
        if cls.is_operator(user):
            # Operators can manage website content
            if perm_key in cls.WEBSITE_PERMISSIONS:
                return True
                
        return False

    has_permission = has

    @classmethod
    def get_permission_context(cls, user) -> Dict[str, bool]:
        if not user.is_authenticated:
            ctx = {
                'is_pro': False,
                'is_admin': False,
                'is_operator': False,
                'user_role': None,
            }
            for perm in cls.ALL_PERMISSION_KEYS:
                ctx[perm] = False
            ctx['user_permissions'] = {p: False for p in cls.ALL_PERMISSION_KEYS}
            return ctx

        cache_key = f'perm:ctx:v3:{user.pk}:{user.role}'
        cached = _cache.get(cache_key)
        if isinstance(cached, dict):
            return cached

        ctx = {
            'is_pro': cls.is_pro(user),
            'is_admin': cls.is_admin(user),
            'is_operator': cls.is_operator(user),
            'user_role': user.role,
        }
        for perm in cls.ALL_PERMISSION_KEYS:
            ctx[perm] = cls.has(user, perm)
        ctx['user_permissions'] = {p: ctx[p] for p in cls.ALL_PERMISSION_KEYS}

        _cache.set(cache_key, ctx, cls.PERMISSION_CONTEXT_CACHE_TTL)
        return ctx

    @classmethod
    def debug_permissions(cls, user) -> dict:
        return {
            'user_id': user.pk if user.is_authenticated else None,
            'username': user.username if user.is_authenticated else None,
            'role': getattr(user, 'role', None),
            'is_admin': cls.is_admin(user),
            'is_operator': cls.is_operator(user),
            'effective_permissions': {p: cls.has(user, p) for p in cls.ALL_PERMISSION_KEYS},
        }

# Decorators
def _permission_denied_response(request, message='Permission denied', status=403):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or '/api/' in request.path:
        return JsonResponse({'success': False, 'message': message}, status=status)
    return redirect('accounts:login')

def require_any_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _permission_denied_response(request, status=401)
        if not PermissionService.is_any_admin(request.user):
            return _permission_denied_response(request, 'Admin access required')
        return view_func(request, *args, **kwargs)
    return wrapper

def api_require_any_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
        if not PermissionService.is_any_admin(request.user):
            return JsonResponse({'success': False, 'message': 'Admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

def api_require_super_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
        if not PermissionService.is_admin(request.user):
            return JsonResponse({'success': False, 'message': 'Super admin access required'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
