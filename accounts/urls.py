"""
Accounts URL Configuration

URL patterns for authentication and password reset.

NOTE: The primary auth API routes are in core/urls.py (/panel/api/auth/...)
which are the ones used by the login template. These accounts/ routes are
kept only for the login/logout page views and the dashboard redirect.
"""
from django.urls import path
from . import views
from .session_refresh import api_session_refresh

app_name = 'accounts'

urlpatterns = [
    # ==========================================================================
    # PAGE VIEWS (Template-based)
    # ==========================================================================
    
    # Login page (multi-step: email → password)
    path('login/', views.LoginPageView.as_view(), name='login'),
    
    # CSRF token acquisition
    path('csrf/', views.GetCSRFTokenView.as_view(), name='get_csrf_token'),
    
    # Logout
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Redirect to appropriate dashboard
    path('dash/', views.redirect_to_dashboard, name='dashboard_redirect'),
    
    # Secure Credential Vault (opened via email link)
    path('secure-view/<str:token>/', views.SecureCredentialVaultView.as_view(), name='secure_credential_vault'),
    
    
    # ==========================================================================
    # API ENDPOINTS (JSON responses for AJAX)
    # Canonical routes are at /panel/api/auth/ via core/urls.py
    # These /panel/auth/api/auth/ aliases kept for backward compatibility.
    # ==========================================================================
    
    path('api/auth/check-email/', views.CheckEmailAPIView.as_view(), name='api_check_email'),
    path('api/auth/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('api/auth/forgot-password/', views.ForgotPasswordAPIView.as_view(), name='api_forgot_password'),
    path('api/auth/verify-otp/', views.VerifyOTPAPIView.as_view(), name='api_verify_otp'),
    path('api/auth/reset-password/', views.ResetPasswordAPIView.as_view(), name='api_reset_password'),

    # Session refresh (silent keepalive for active users)
    path('api/auth/session-refresh/', api_session_refresh, name='api_session_refresh'),
]
