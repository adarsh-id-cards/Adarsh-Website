"""
Core Base Views
Cleaned for Website & Manage Website.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.services.activity_service import ActivityService
from core.services.permission_service import PermissionService

@login_required
def dashboard(request):
    """Main administrative dashboard."""
    context = PermissionService.get_permission_context(request.user)
    context['active_page'] = 'dashboard'
    # For now, just a placeholder or redirect to website management
    return render(request, 'core/dashboard.html', context)

@login_required
def api_recent_activity(request):
    """Recent activity log API."""
    limit = int(request.GET.get('limit', 8))
    activities = ActivityService.get_recent(limit=limit)
    return JsonResponse({'success': True, 'activities': activities})

def api_health(request):
    """Health check endpoint."""
    return JsonResponse({'status': 'ok', 'version': '1.0.0'})

@login_required
def api_debug_permissions(request):
    """Debug permissions API."""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Forbidden'}, status=403)
    perms = PermissionService.get_permission_context(request.user)
    return JsonResponse({'success': True, 'permissions': perms})
