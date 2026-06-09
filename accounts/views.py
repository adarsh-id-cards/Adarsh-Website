"""
Accounts Views Module
Simplified for Website Management.
"""
import json
import logging
import re
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import login, logout, get_user_model
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from core.services.activity_service import ActivityService
from .services import AuthService, OTPService, DASHBOARD_URLS
from .rate_limit import rate_limit, _get_client_ip

logger = logging.getLogger(__name__)
User = get_user_model()

@method_decorator(ensure_csrf_cookie, name='dispatch')
class GetCSRFTokenView(View):
    """
    Endpoint to ensure CSRF cookie is set for the client.
    """
    def get(self, request):
        return JsonResponse({'success': True, 'message': 'CSRF cookie set'})

@login_required
def redirect_to_dashboard(request):
    """
    Redirect authenticated users to their appropriate dashboard.
    """
    return redirect(AuthService.get_dashboard_url(request.user))

class SecureCredentialVaultView(View):
    """
    Secure Credential Vault View.
    Original implementation was removed during cleanup.
    """
    def get(self, request, token):
        return render(request, 'errors/error.html', {
            'status_code': 403,
            'title': 'Vault Access Disabled',
            'message': 'This vault has been deactivated or moved.'
        }, status=403)

@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoginPageView(View):
    template_name = 'auth/login.html'
    def get(self, request):
        if request.user.is_authenticated:
            next_url = request.GET.get('next', '')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect(AuthService.get_dashboard_url(request.user))
        return render(request, self.template_name)

def _mask_login_identifier(identifier: str) -> str:
    if not identifier:
        return ""
    if "@" in identifier:
        parts = identifier.split("@", 1)
        local, domain = parts[0], parts[1]
        masked_local = (local[0] + "***") if len(local) > 1 else (local + "***")
        return f"{masked_local}@{domain}"
    return (identifier[0] + "***") if len(identifier) > 1 else (identifier + "***")

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    def get(self, request):
        return self.post(request)

    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        
        if request.user.is_authenticated:
            ActivityService.log_logout(request, request.user)
        logout(request)
        target = '/'
        if is_ajax: return JsonResponse({'success': True, 'redirect': target})
        return redirect(target)

class StaffDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        return redirect('/dash/')

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(rate_limit(max_requests=10, window_seconds=60), name='dispatch')
class CheckEmailAPIView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            res = AuthService.check_user_exists(data.get('email', '').strip())
            return JsonResponse(res)
        except: return JsonResponse({'success': False, 'message': 'Error'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(rate_limit(max_requests=5, window_seconds=60), name='dispatch')
class LoginAPIView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            res = AuthService.authenticate_user(data.get('email', '').strip(), data.get('password', ''))
            if res['success']:
                user = res['user']
                login(request, user)
                from core.middleware import PermissionValidationMiddleware
                PermissionValidationMiddleware.seed_session_fingerprint(request)
                AuthService.apply_session_auth_context(request, ip_address=_get_client_ip(request))
                ActivityService.log_login(request, user)
                return JsonResponse({'success': True, 'redirect_url': res['redirect_url']})
            return JsonResponse({'success': False, 'message': res['message']})
        except Exception as e:
            logger.exception("Login error")
            return JsonResponse({'success': False, 'message': 'Error'}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ForgotPasswordAPIView(View):
    def post(self, request):
        data = json.loads(request.body)
        res = OTPService.send_otp(data.get('email', '').strip())
        res.pop('dev_otp', None)
        return JsonResponse(res)

@method_decorator(csrf_exempt, name='dispatch')
class VerifyOTPAPIView(View):
    def post(self, request):
        data = json.loads(request.body)
        res = OTPService.verify_otp(data.get('email', '').strip(), data.get('otp', '').strip())
        return JsonResponse(res)

@method_decorator(csrf_exempt, name='dispatch')
class ResetPasswordAPIView(View):
    def post(self, request):
        data = json.loads(request.body)
        res = OTPService.reset_password(data.get('email', '').strip(), data.get('reset_token', '').strip(), data.get('new_password', ''))
        return JsonResponse(res)


