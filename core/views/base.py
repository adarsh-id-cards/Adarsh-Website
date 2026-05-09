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
    from website.models import Testimonial, PortfolioItem, ContactSubmission, Feature, WebsiteStatus
    from website.services import WebsiteClientLogoService
    from core.models import SystemSettings
    
    context = PermissionService.get_permission_context(request.user)
    context['active_page'] = 'dashboard'
    
    # Fetch Stats for Dashboard
    # 1. Reviews
    all_reviews = Testimonial.objects.all()
    context['total_reviews'] = all_reviews.count()
    context['active_reviews'] = all_reviews.filter(is_active=True).count()
    
    # 2. Clients (via Bridge or Local if not bridged)
    clients = WebsiteClientLogoService.list_all()
    context['total_clients'] = len(clients)
    context['active_clients'] = len([c for c in clients if getattr(c, 'website_is_visible', False)])
    
    # 3. Portfolio
    all_portfolio = PortfolioItem.objects.all()
    context['total_portfolio'] = all_portfolio.count()
    context['active_portfolio'] = all_portfolio.filter(is_active=True).count()
    
    # 4. Features & Contacts
    context['total_features'] = Feature.objects.filter(is_active=True).count()
    
    all_contacts = ContactSubmission.objects.all()
    context['total_contacts'] = all_contacts.count()
    context['new_contacts'] = all_contacts.filter(status='new').count()
    
    # 5. Website Status
    context['website_status'] = WebsiteStatus.get_status()
    context['website_not_found_mode'] = SystemSettings.get_value('website_not_found_mode', 'false') == 'true'
    
    # Permissions for UI toggles
    context['perm_website_publish'] = PermissionService.has(request.user, 'perm_website_publish')
    context['is_pro'] = PermissionService.is_pro(request.user)
    context['is_admin'] = PermissionService.is_admin(request.user)
    
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
