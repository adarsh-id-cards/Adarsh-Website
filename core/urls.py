from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    # ==================== AUTHENTICATION ====================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('inactive/', views.inactive_view, name='inactive'),
    path('maintenance/', views.maintenance_view, name='maintenance'),
    
    path('api/auth/check-email/', csrf_exempt(views.api_check_email), name='api_check_email'),
    path('api/auth/login/', csrf_exempt(views.api_login), name='api_login'),
    path('api/auth/forgot-password/', csrf_exempt(views.api_forgot_password), name='api_forgot_password'),
    path('api/auth/verify-otp/', csrf_exempt(views.api_verify_otp), name='api_verify_otp'),
    path('api/auth/reset-password/', csrf_exempt(views.api_reset_password), name='api_reset_password'),
    path('api/auth/impersonate/start/', csrf_exempt(views.api_impersonate_start), name='api_impersonate_start'),
    path('api/auth/impersonate/stop/', csrf_exempt(views.api_impersonate_stop), name='api_impersonate_stop'),
    path('api/auth/impersonate/users/', csrf_exempt(views.api_impersonate_users), name='api_impersonate_users'),
    path('api/auth/me/', views.api_get_me, name='api_get_me'),
    
    # ==================== USER MANAGEMENT API ====================
    path('api/users/', views.api_user_list, name='api_user_list'),
    path('api/users/create/', views.api_user_create, name='api_user_create'),
    path('api/users/<int:pk>/update/', views.api_user_update, name='api_user_update'),
    path('api/users/<int:pk>/delete/', views.api_user_delete, name='api_user_delete'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Activity & Health
    path('api/recent-activity/', views.api_recent_activity, name='api_recent_activity'),
    path('api/health/', views.api_health, name='api_health'),
    
    # Profile APIs
    path('api/profile/', views.api_get_profile, name='api_get_profile'),
    path('api/profile/update/', views.api_update_profile, name='api_update_profile'),
    path('api/profile/change-password/', views.api_change_password, name='api_change_password'),
]

# Debug endpoints
from django.conf import settings as _settings
if _settings.DEBUG:
    urlpatterns += [
        path('api/debug/permissions/', views.api_debug_permissions, name='api_debug_permissions'),
    ]
