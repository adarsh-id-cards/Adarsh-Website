"""
Email Utility Functions
Simplified for Website Management.
"""
import logging
from html import escape
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from core.utils.threaded_email import send_html_email_async

logger = logging.getLogger(__name__)

def _get_panel_login_url(request=None):
    """Build the panel login URL."""
    panel_url = getattr(settings, 'PANEL_URL', '')
    if panel_url:
        return f'{panel_url}/auth/login/'
    elif request:
        return request.build_absolute_uri('/auth/login/')
    return f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/panel/auth/login/"

def build_unified_email_html(theme='system', title='Notification', body_html='', cta_label='', cta_url='', request=None):
    """Minimal email template shell."""
    return f"""
    <html>
    <body style="font-family: sans-serif; padding: 20px;">
        <h2 style="color: #2563eb;">{escape(title)}</h2>
        <div style="margin-top: 10px;">{body_html}</div>
        {f'<div style="margin-top: 20px;"><a href="{escape(cta_url)}" style="background: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">{escape(cta_label)}</a></div>' if cta_label else ''}
        <hr style="margin-top: 30px; border: 0; border-top: 1px solid #eee;">
        <p style="font-size: 12px; color: #666;">This is an automated message from Adarsh Website Management.</p>
    </body>
    </html>
    """

def send_password_reset_otp_email(user_name, email, otp, expiry_minutes, request=None):
    """Send OTP reset email."""
    body_html = f"<p>Hello {escape(user_name)},</p><p>Your OTP for password reset is: <strong>{escape(str(otp))}</strong></p><p>Valid for {expiry_minutes} minutes.</p>"
    html_content = build_unified_email_html(title='Password Reset OTP', body_html=body_html, request=request)
    send_html_email_async('Password Reset OTP', f'Your OTP is: {otp}', html_content, settings.DEFAULT_FROM_EMAIL, [email])

def send_emergency_panel_access_email(target_email, request=None, issued_by=None):
    """Send emergency access link."""
    login_url = _get_panel_login_url(request)
    body_html = f"<p>A secure panel login link has been shared with you.</p>"
    html_content = build_unified_email_html(title='Secure Panel Login Link', body_html=body_html, cta_label='Login Now', cta_url=login_url, request=request)
    send_html_email_async('Emergency Panel Access', 'Access link: ' + login_url, html_content, settings.DEFAULT_FROM_EMAIL, [target_email])
    return True, "Access link sent"

def get_password_reset_otp_email_template(name, otp, expiry_minutes=10):
    """Satisfy legacy accounts import."""
    body_html = f"<p>Hello {escape(name)},</p><p>Your OTP for password reset is: <strong>{escape(str(otp))}</strong></p><p>Valid for {expiry_minutes} minutes.</p>"
    html_content = build_unified_email_html(title='Password Reset OTP', body_html=body_html)
    return html_content, f"Your OTP for password reset is: {otp}"

def get_security_alert_email_template(name, attempts):
    """Satisfy legacy accounts import."""
    body_html = f"<p>Hello {escape(name)},</p><p>Multiple failed login attempts ({attempts}) were detected on your account.</p>"
    html_content = build_unified_email_html(title='Security Alert', body_html=body_html)
    return html_content, f"Security Alert: Multiple failed login attempts ({attempts})"

def send_not_found_mode_enabled_broadcast(request=None, enabled_by=None):
    """Notify admins that Not Found mode has been enabled."""
    body_html = f"<p>Website 'Not Found' mode has been enabled by {escape(str(enabled_by or 'System'))}.</p>"
    html_content = build_unified_email_html(title='Website Not Found Mode Enabled', body_html=body_html)
    logger.info("Not Found mode enabled broadcast triggered.")
    return True, "Broadcast logged"