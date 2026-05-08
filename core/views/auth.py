"""
Authentication Views
Simplified for Website Management.
"""
from accounts.views import (
    LoginPageView,
    LogoutView,
    CheckEmailAPIView,
    LoginAPIView,
    ForgotPasswordAPIView,
    VerifyOTPAPIView,
    ResetPasswordAPIView,
    ImpersonateStartAPIView,
    ImpersonateStopAPIView,
    ImpersonateListAPIView,
)

login_view = LoginPageView.as_view()
logout_view = LogoutView.as_view()
api_check_email = CheckEmailAPIView.as_view()
api_login = LoginAPIView.as_view()
api_forgot_password = ForgotPasswordAPIView.as_view()
api_verify_otp = VerifyOTPAPIView.as_view()
api_reset_password = ResetPasswordAPIView.as_view()

api_impersonate_start = ImpersonateStartAPIView.as_view()
api_impersonate_stop = ImpersonateStopAPIView.as_view()
api_impersonate_users = ImpersonateListAPIView.as_view()

def inactive_view(request):
    from django.shortcuts import render
    reason = request.GET.get('reason', '')
    return render(request, 'auth/inactive.html', {'reason': reason})

def maintenance_view(request):
    from django.shortcuts import render, redirect
    if not request.user.is_authenticated:
        return redirect('inactive')
    reason = request.GET.get('reason', '')
    return render(request, 'auth/maintenance.html', {'reason': reason})

def api_check_maintenance(request):
    from django.http import JsonResponse
    return JsonResponse({'active': True})
