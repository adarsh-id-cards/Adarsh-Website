"""
URL Configuration — Admin Panel (panel.adarshbhopal.in)
Refactored for Website Management only.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET
from core.views.health import health_check
from website import views as website_views

@require_GET
@cache_page(60 * 60 * 24)
def panel_robots_txt(request):
    """Allow ALL crawlers to index the panel subdomain."""
    return HttpResponse(
        "User-agent: *\nAllow: /\n",
        content_type="text/plain",
    )

def _protected_media_serve(request, path, document_root=None):
    """Serve media files with access control."""
    from django.http import HttpResponse
    from django.views.static import serve
    from django.urls import reverse
    from django.contrib.auth.views import redirect_to_login
    from core.services.permission_service import PermissionService

    rel_path = path.replace('\\', '/').strip('/')
    if not rel_path:
        return HttpResponse(status=404)

    # Simplified protected prefixes
    PROTECTED_PREFIXES = ('exports/', 'temp/')
    if any(rel_path.startswith(p) for p in PROTECTED_PREFIXES):
        if not request.user.is_authenticated:
            login_url = reverse('accounts:login')
            return redirect_to_login(request.get_full_path(), login_url=login_url)

        if not PermissionService.is_any_admin(request.user):
            return HttpResponse(status=404)

    return serve(request, rel_path, document_root=document_root)

urlpatterns = [
    path('api/health/', health_check, name='health_check'),
    path('manifest.json', website_views.pwa_manifest, name='panel_pwa_manifest'),
    path('sw.js', website_views.pwa_service_worker, name='panel_pwa_service_worker'),
    path('robots.txt', panel_robots_txt, name='panel_robots_txt'),

    path('admin/', admin.site.urls),

    # ==================== ADMIN PANEL (root) ====================
    path('', include('core.urls')),
    path('auth/', include('accounts.urls')),
    path('manage/', include('manage_website.urls')),
]

if getattr(settings, 'DEBUG', False):
    try:
        import debug_toolbar
        urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    except ImportError:
        pass

# Media file serving
urlpatterns += [
    path('media/<path:path>', _protected_media_serve, {'document_root': settings.MEDIA_ROOT}),
]

handler400 = 'core.views.errors.error_400'
handler403 = 'core.views.errors.error_403'
handler404 = 'core.views.errors.error_404'
handler500 = 'core.views.errors.error_500'
