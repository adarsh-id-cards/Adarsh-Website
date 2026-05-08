from django.contrib import admin
from django.urls import path, include, reverse
from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from website import seo
from core.views.health import health_check
from core import views as core_views



def _protected_media_serve(request, path, document_root=None):
    """
    Serve media files with access control for sensitive directories.

    In production (DEBUG=False), protected files are served by Nginx via
    X-Accel-Redirect — Django only performs the auth check then hands off.
    Nginx must have the `location /protected-media/` block marked `internal;`
    (see deployment/nginx_example.conf).

    In development (DEBUG=True), Django's `serve()` is used as a fallback.
    """
    from django.http import HttpResponse
    from django.views.static import serve

    def _normalize_media_path(raw_path):
        parts = []
        for part in str(raw_path or '').replace('\\', '/').split('/'):
            part = part.strip()
            if not part or part == '.':
                continue
            if part == '..':
                return ''
            parts.append(part)
        return '/'.join(parts)

    rel_path = _normalize_media_path(path)
    if not rel_path:
        return HttpResponse(status=404)

    # 'adarshimg/'    - client ID card photos (personal data, most sensitive)
    # 'exports/'      - generated PDF/Excel/Word/ZIP exports
    # 'clients_imgs/' - client profile images
    # 'staff_imgs/'   - staff profile images
    # 'temp/'         - temporary upload holding area
    PROTECTED_PREFIXES = (
        'adarshimg/',
        'exports/',
        'clients_imgs/',
        'staff_imgs/',
        'temp/',
    )
    if any(rel_path.startswith(p) for p in PROTECTED_PREFIXES):
        if not request.user.is_authenticated:
            # Redirect to login, preserving the original URL in ?next=
            # so the user is returned here after successful authentication.
            login_url = reverse('login')
            return redirect_to_login(request.get_full_path(), login_url=login_url)

        from core.services.permission_service import PermissionService

        # Super admin/pro_user keeps unrestricted access to protected media.
        if not PermissionService.is_super_admin(request.user):
            # For all protected folders, keep access to admins only.
            if not PermissionService.is_any_admin(request.user):
                return HttpResponse(status=404)

    # Production with Nginx: serve via X-Accel-Redirect (zero-copy, non-blocking).
    # Requires MEDIA_USE_XACCEL=true in env AND the Nginx internal
    # /protected-media/ location block (see deployment/nginx_example.conf).
    if getattr(settings, 'MEDIA_USE_XACCEL', False):
        response = HttpResponse()
        response['X-Accel-Redirect'] = f'/protected-media/{rel_path}'
        response['Content-Type'] = ''  # let Nginx detect from file extension
        return response

    # Fallback: Django serves the file directly (dev + prod without X-Accel)
    response = serve(request, rel_path, document_root=document_root)

    # Super Mode can use larger stream blocks for protected downloads.
    if hasattr(response, 'block_size') and getattr(request, 'user', None) and request.user.is_authenticated:
        try:
            from core.services.super_mode_service import SuperModeService

            response.block_size = SuperModeService.download_block_size_bytes(request.user)
        except Exception:
            pass

    return response


urlpatterns = [
    # Health check — no auth, used by load balancers / CI/CD
    path('api/health/', health_check, name='health_check'),

    # SEO — served at root, only for public website (with error handling & caching)
    path('robots.txt', seo.robots_txt, name='robots_txt'),
    path('sitemap.xml', seo.sitemap_xml, name='sitemap_view'),

    # Django admin
    path('admin/', admin.site.urls),

    # Local-only debug toolbar route.
    # Debug Toolbar is enabled in DEBUG mode only and helps inspect SQL/query
    # behavior without affecting production routing.
    # NOTE: the toolbar package is optional in production. Register its
    # URLs only when DEBUG is enabled and the package is importable.

    # Local-only Sentry test route. Only registered in DEBUG to avoid accidental exposure.
    # Visit /sentry-debug/ in local dev to trigger a test exception (1/0) for verification.
]

# Register debug-only routes (debug_toolbar, sentry test) only when DEBUG.
if getattr(settings, 'DEBUG', False):
    # Debug toolbar: optional dependency; import only if installed.
    try:
        import debug_toolbar  # noqa: F401
    except Exception:
        pass
    else:
        urlpatterns += [
            path('__debug__/', include('debug_toolbar.urls')),
        ]

    from django.urls import path as _path

    def _trigger_error(request):
        division_by_zero = 1 / 0

    urlpatterns += [
        _path('sentry-debug/', _trigger_error),
        _path('error/400/', core_views.errors.error_400),
        _path('error/403/', core_views.errors.error_403),
        _path('error/404/', core_views.errors.error_404),
        _path('error/500/', core_views.errors.error_500),
        _path('error/csrf/', core_views.errors.csrf_failure),
    ]

# re-open urlpatterns list continuation
urlpatterns += [

    # ==================== API COMPATIBILITY (ROOT /api/*) ====================

    # ==================== ADMIN PANEL (/panel/) ====================
    # All internal/admin routes live under /panel/
    path('panel/', include('core.urls')),
    path('panel/auth/', include('accounts.urls')),

    # ==================== MANAGE WEBSITE (/dashboard) ====================
    # Website management dashboard on main domain (adarshbhopal.in/dashboard)
    path('dashboard/', include('manage_website.urls')),

    # ==================== PUBLIC WEBSITE (/) ====================
    # Public-facing website at root — must be LAST to avoid catching /panel/ routes
    path('', include('website.urls')),
]

# Media file serving — always register the route so uploaded images/exports
# are accessible.  In production with Nginx, the reverse proxy should serve
# /media/ directly; this Django view acts as a safe fallback.
urlpatterns += [
    path('media/<path:path>', _protected_media_serve, {'document_root': settings.MEDIA_ROOT}),
]

handler400 = 'core.views.errors.error_400'
handler403 = 'core.views.errors.error_403'
handler404 = 'core.views.errors.error_404'
handler500 = 'core.views.errors.error_500'


