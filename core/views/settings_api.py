"""
Settings API Views
==================
Profile management views for all user roles.
"""
import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash

from core.services.user_profile_service import UserProfileService

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET"])
def api_get_profile(request):
    """Get current user's profile data."""
    user = request.user
    security_settings = UserProfileService.get_security_settings(user)
    return JsonResponse({
        'success': True,
        'profile': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username,
            'phone': getattr(user, 'phone', '') or '',
            'role': user.role,
            'role_display': user.get_role_display() if hasattr(user, 'get_role_display') else user.role,
            'member_since': user.date_joined.strftime('%b %Y') if user.date_joined else '',
            'security_settings': security_settings,
        }
    })

@login_required
@require_http_methods(["POST"])
def api_update_profile(request):
    """Update current user's profile data."""
    try:
        data = json.loads(request.body)
        success, message, profile_data = UserProfileService.update_profile(request.user, data)
        return JsonResponse({
            'success': success,
            'message': message,
            'profile': profile_data if success else None,
        })
    except Exception as e:
        logger.exception("Settings API error (update_profile): %s", e)
        return JsonResponse({'success': False, 'message': 'An error occurred'})

@login_required
@require_http_methods(["POST"])
def api_change_password(request):
    """Change current user's password."""
    try:
        data = json.loads(request.body)
        success, message = UserProfileService.change_password(
            request.user,
            data.get('current_password'),
            data.get('new_password'),
            current_session_key=request.session.session_key,
        )
        if success:
            update_session_auth_hash(request, request.user)
        return JsonResponse({'success': success, 'message': message})
    except Exception as e:
        logger.exception("Settings API error (change_password): %s", e)
        return JsonResponse({'success': False, 'message': 'An error occurred'})
