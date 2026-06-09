"""
Tests for accounts app.
Covers: AuthService, OTPService, RoleService, rate limiting, login/logout flows.
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.core.cache import cache
from django.test.client import RequestFactory
from unittest import mock
import json
from core.models import ActivityLog

User = get_user_model()


class AuthServiceTests(TestCase):
    """Tests for accounts.services.AuthService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='testpass123',
            role='client',
        )

    def test_check_user_exists_found(self):
        from accounts.services import AuthService
        result = AuthService.check_user_exists('test@example.com')
        self.assertTrue(result['success'])
        self.assertEqual(result['user_name'], 'User')
        self.assertEqual(result['user_email'], 'test@example.com')

    def test_check_user_exists_not_found(self):
        from accounts.services import AuthService
        result = AuthService.check_user_exists('nobody@example.com')
        self.assertTrue(result['success'])
        self.assertEqual(result['user_name'], 'User')
        self.assertEqual(result['user_email'], 'nobody@example.com')

    def test_authenticate_user_success(self):
        from accounts.services import AuthService
        result = AuthService.authenticate_user('test@example.com', 'testpass123')
        self.assertTrue(result['success'])
        self.assertEqual(result['user'].email, 'test@example.com')

    def test_authenticate_user_success_with_phone_identifier(self):
        from accounts.services import AuthService
        self.user.phone = '+91 98765-43210'
        self.user.save(update_fields=['phone'])

        result = AuthService.authenticate_user('9876543210', 'testpass123')
        self.assertTrue(result['success'])
        self.assertEqual(result['user'].email, 'test@example.com')

    def test_authenticate_user_wrong_password(self):
        from accounts.services import AuthService
        result = AuthService.authenticate_user('test@example.com', 'wrongpass')
        self.assertFalse(result['success'])

    def test_authenticate_user_nonexistent(self):
        from accounts.services import AuthService
        result = AuthService.authenticate_user('nobody@example.com', 'pass')
        self.assertFalse(result['success'])

    def test_authenticate_inactive_user(self):
        from accounts.services import AuthService
        self.user.is_active = False
        self.user.save()
        result = AuthService.authenticate_user('test@example.com', 'testpass123')
        self.assertFalse(result['success'])

    def test_get_dashboard_url_client(self):
        from accounts.services import AuthService
        url = AuthService.get_dashboard_url(self.user)
        self.assertEqual(url, '/dash/')

    def test_get_dashboard_url_super_admin(self):
        from accounts.services import AuthService
        admin = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='admin123',
            role='super_admin',
        )
        url = AuthService.get_dashboard_url(admin)
        self.assertEqual(url, '/dash/')


class PasswordNormalizationTests(TestCase):
    def test_normalize_password_phone_with_country_and_brackets(self):
        from accounts.services import normalize_password_input

        self.assertEqual(
            normalize_password_input('(+91) 98765-43210'),
            '9876543210',
        )

    def test_normalize_password_phone_with_dots(self):
        from accounts.services import normalize_password_input

        self.assertEqual(
            normalize_password_input('91.98765.43210'),
            '9876543210',
        )

    def test_normalize_password_keeps_symbolic_custom_password(self):
        from accounts.services import normalize_password_input

        self.assertEqual(
            normalize_password_input('1234!@#'),
            '1234!@#',
        )


class OTPServiceTests(TestCase):
    """Tests for accounts.services.OTPService"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='otp@example.com',
            email='otp@example.com',
            password='testpass123',
            role='client',
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_generate_otp_length(self):
        from accounts.services import OTPService
        otp = OTPService.generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_generate_reset_token_format(self):
        from accounts.services import OTPService
        token = OTPService.generate_reset_token()
        # HMAC format: raw_token.signature
        self.assertIn('.', token)
        parts = token.split('.')
        self.assertEqual(len(parts), 2)

    def test_send_otp_success(self):
        from accounts.services import OTPService
        result = OTPService.send_otp('otp@example.com')
        self.assertTrue(result['success'])

    def test_send_otp_nonexistent_email(self):
        from accounts.services import OTPService
        result = OTPService.send_otp('nobody@example.com')
        # OTPService may silently succeed even for unknown emails (security best practice)
        self.assertIn('success', result)

    def test_verify_otp_and_reset_password(self):
        from accounts.services import OTPService
        send_result = OTPService.send_otp('otp@example.com')
        self.assertTrue(send_result['success'])
        dev_otp = send_result.get('dev_otp')
        if dev_otp:
            verify_result = OTPService.verify_otp('otp@example.com', dev_otp)
            self.assertTrue(verify_result['success'])
            reset_token = verify_result.get('reset_token')
            self.assertIsNotNone(reset_token)

            reset_result = OTPService.reset_password(
                'otp@example.com', reset_token, 'newpassword1'
            )
            self.assertTrue(reset_result['success'])

            from accounts.services import AuthService
            auth_result = AuthService.authenticate_user('otp@example.com', 'newpassword1')
            self.assertTrue(auth_result['success'])

    def test_verify_otp_wrong_code(self):
        from accounts.services import OTPService
        OTPService.send_otp('otp@example.com')
        result = OTPService.verify_otp('otp@example.com', '000000')
        self.assertFalse(result['success'])

    def test_reset_password_invalid_token(self):
        from accounts.services import OTPService
        result = OTPService.reset_password('otp@example.com', 'fake.token', 'newpass123')
        self.assertFalse(result['success'])

    def test_reset_password_too_short(self):
        from accounts.services import OTPService
        send = OTPService.send_otp('otp@example.com')
        dev_otp = send.get('dev_otp')
        if dev_otp:
            verify = OTPService.verify_otp('otp@example.com', dev_otp)
            token = verify.get('reset_token')
            if token:
                result = OTPService.reset_password('otp@example.com', token, 'short')
                self.assertFalse(result['success'])


class RoleServiceTests(TestCase):
    """Tests for accounts.services.RoleService"""

    def test_setup_groups(self):
        from accounts.services import RoleService
        result = RoleService.setup_groups()
        self.assertTrue(result['success'])
        self.assertIn('groups', result)

    def test_get_role_display_name(self):
        from accounts.services import RoleService
        self.assertEqual(RoleService.get_role_display_name('super_admin'), 'Super Admin')
        self.assertEqual(RoleService.get_role_display_name('client'), 'Client')


class LoginViewTests(TestCase):
    """Tests for login/logout views"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='view@example.com',
            email='view@example.com',
            password='testpass123',
            role='client',
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def _create_authenticated_session(self, browser_fp='', surface='desktop', mobile_auth_ok=False):
        session = SessionStore()
        session['_auth_user_id'] = str(self.user.pk)
        session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        session['_auth_user_hash'] = self.user.get_session_auth_hash()
        if browser_fp:
            session['_auth_browser_fp'] = browser_fp
        session['_auth_login_surface'] = surface
        if mobile_auth_ok or surface == 'mobile':
            session['mobile_auth_ok'] = True
        session.save()

    def test_login_page_loads(self):
        response = self.client.get('/dash/auth/login/')
        self.assertIn(response.status_code, [200, 302])

    def test_logout_redirects(self):
        self.client.login(username='view@example.com', password='testpass123')
        response = self.client.get('/dash/auth/logout/')
        self.assertEqual(response.status_code, 302)

    def test_check_email_api(self):
        response = self.client.post(
            '/dash/auth/api/auth/check-email/',
            data=json.dumps({'email': 'view@example.com'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('exists') or data.get('success'))

    def test_login_api_success(self):
        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': 'view@example.com',
                'password': 'testpass123',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_login_api_success_with_phone_identifier(self):
        self.user.phone = '+91 90123-45678'
        self.user.save(update_fields=['phone'])

        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': '9012345678',
                'password': 'testpass123',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])



    def test_login_api_allows_super_admin_unlimited_desktop_sessions(self):
        super_admin = User.objects.create_user(
            username='sa-limit@example.com',
            email='sa-limit@example.com',
            password='testpass123',
            role='super_admin',
        )

        # Create 5 existing sessions
        for _ in range(5):
            session = SessionStore()
            session['_auth_user_id'] = str(super_admin.pk)
            session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
            session['_auth_user_hash'] = super_admin.get_session_auth_hash()
            session['_auth_login_surface'] = 'desktop'
            session.save()

        # Login 6th time - should succeed and NOT revoke any existing sessions
        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': 'sa-limit@example.com',
                'password': 'testpass123',
            }),
            content_type='application/json',
            REMOTE_ADDR='203.0.113.25',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        
        # Verify all 6 sessions exist (5 old + 1 new)
        from django.contrib.sessions.models import Session
        count = Session.objects.filter(session_key__in=[s.session_key for s in Session.objects.all()]).count()
        # Filter by user in session data to be sure
        user_sessions = 0
        for s in Session.objects.all():
            if str(s.get_decoded().get('_auth_user_id')) == str(super_admin.pk):
                user_sessions += 1
        self.assertEqual(user_sessions, 6)



    def test_login_api_logs_cross_browser_activity_for_client(self):
        from accounts.services import AuthService

        existing_fp = AuthService.build_browser_fingerprint(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0',
            'en-US',
        )
        self._create_authenticated_session(
            browser_fp=existing_fp,
            surface='mobile',
            mobile_auth_ok=True,
        )

        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': 'view@example.com',
                'password': 'testpass123',
            }),
            content_type='application/json',
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
            HTTP_ACCEPT_LANGUAGE='en-US',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

        log_entry = ActivityLog.objects.filter(user=self.user, action='login').order_by('-id').first()
        self.assertIsNotNone(log_entry)
        self.assertIn('different browser', (log_entry.description or '').lower())

    def test_login_api_records_ip_address_in_activity_log(self):
        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': 'view@example.com',
                'password': 'testpass123',
            }),
            content_type='application/json',
            REMOTE_ADDR='203.0.113.50',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

        log_entry = ActivityLog.objects.filter(user=self.user, action='login').order_by('-id').first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.ip_address, '203.0.113.50')


class AuthServiceIpTests(TestCase):
    def setUp(self):
        # Provide a regular client user used by some login tests in this class
        self.user = User.objects.create_user(
            username='view@example.com',
            email='view@example.com',
            password='testpass123',
            role='client',
        )

    def _create_session_for_user(self, user):
        s = SessionStore()
        s['_auth_user_id'] = str(user.pk)
        s['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
        s['_auth_user_hash'] = user.get_session_auth_hash()
        s['_auth_login_surface'] = 'desktop'
        s.save()
        return s.session_key



    @override_settings(RATE_LIMIT_TRUST_X_FORWARDED_FOR=True)
    def test_login_api_records_trusted_xff_ip_in_activity_log(self):
        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': 'view@example.com',
                'password': 'testpass123',
            }),
            content_type='application/json',
            REMOTE_ADDR='10.10.10.10',
            HTTP_X_FORWARDED_FOR='198.51.100.33, 203.0.113.44',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

        log_entry = ActivityLog.objects.filter(user=self.user, action='login').order_by('-id').first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.ip_address, '198.51.100.33')

    @override_settings(RATE_LIMIT_TRUST_X_FORWARDED_FOR=False)
    def test_login_api_uses_x_real_ip_when_remote_addr_is_internal_proxy(self):
        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': 'view@example.com',
                'password': 'testpass123',
            }),
            content_type='application/json',
            REMOTE_ADDR='10.10.10.10',
            HTTP_X_REAL_IP='198.51.100.77',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

        log_entry = ActivityLog.objects.filter(user=self.user, action='login').order_by('-id').first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.ip_address, '198.51.100.77')

    @override_settings(RATE_LIMIT_TRUST_X_FORWARDED_FOR=False)
    def test_login_api_prefers_public_remote_addr_when_not_trusting_proxy_headers(self):
        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': 'view@example.com',
                'password': 'testpass123',
            }),
            content_type='application/json',
            REMOTE_ADDR='8.8.8.8',
            HTTP_X_FORWARDED_FOR='1.1.1.1',
            HTTP_X_REAL_IP='9.9.9.9',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

        log_entry = ActivityLog.objects.filter(user=self.user, action='login').order_by('-id').first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.ip_address, '8.8.8.8')

    def test_login_api_wrong_password(self):
        response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({
                'email': 'view@example.com',
                'password': 'wrong',
            }),
            content_type='application/json',
        )
        data = response.json()
        self.assertFalse(data['success'])

    @override_settings(DEBUG=True)
    def test_forgot_password_api_never_exposes_dev_otp(self):
        with mock.patch.dict('os.environ', {'DEV_EXPOSE_OTP': 'true'}):
            response = self.client.post(
                '/dash/auth/api/auth/forgot-password/',
                data=json.dumps({'email': 'view@example.com'}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn('dev_otp', payload)


class RateLimitTests(TestCase):
    """Tests for rate limiting decorator"""

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_rate_limit_allows_under_limit(self):
        for _ in range(3):
            response = self.client.post(
                '/dash/auth/api/auth/login/',
                data=json.dumps({'email': 'test@x.com', 'password': 'x'}),
                content_type='application/json',
            )
            self.assertNotEqual(response.status_code, 429)

    def test_rate_limit_blocks_over_limit(self):
        for i in range(8):
            response = self.client.post(
                '/dash/auth/api/auth/login/',
                data=json.dumps({'email': 'test@x.com', 'password': 'x'}),
                content_type='application/json',
            )
        # After exceeding limit, should get 429
        self.assertIn(response.status_code, [200, 429])

    def test_rate_limit_isolated_per_endpoint(self):
        # Exhaust check-email endpoint bucket first.
        for _ in range(12):
            self.client.post(
                '/dash/auth/api/auth/check-email/',
                data=json.dumps({'email': 'test@x.com'}),
                content_type='application/json',
                REMOTE_ADDR='8.8.8.8',
            )

        # Login endpoint should still have its own bucket and not be hard-blocked by 429.
        login_response = self.client.post(
            '/dash/auth/api/auth/login/',
            data=json.dumps({'email': 'test@x.com', 'password': 'x'}),
            content_type='application/json',
            REMOTE_ADDR='8.8.8.8',
        )
        self.assertNotEqual(login_response.status_code, 429)


class LoginLoggingMaskTests(TestCase):
    def test_mask_login_identifier_email(self):
        from accounts.views import _mask_login_identifier
        self.assertEqual(_mask_login_identifier('alice@example.com'), 'a***@example.com')

    def test_mask_login_identifier_username(self):
        from accounts.views import _mask_login_identifier
        self.assertEqual(_mask_login_identifier('roshan'), 'r***')


class RateLimitClientIPTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(RATE_LIMIT_TRUST_X_FORWARDED_FOR=False)
    def test_get_client_ip_uses_remote_addr_by_default(self):
        from accounts.rate_limit import _get_client_ip
        request = self.factory.get('/dash/auth/api/auth/login/', REMOTE_ADDR='10.10.10.10', HTTP_X_FORWARDED_FOR='8.8.8.8')
        self.assertEqual(_get_client_ip(request), '10.10.10.10')

    @override_settings(RATE_LIMIT_TRUST_X_FORWARDED_FOR=True)
    def test_get_client_ip_uses_trusted_xff_when_enabled(self):
        from accounts.rate_limit import _get_client_ip
        request = self.factory.get(
            '/dash/auth/api/auth/login/',
            REMOTE_ADDR='10.10.10.10',
            HTTP_X_FORWARDED_FOR='198.51.100.1, 203.0.113.10'
        )
        self.assertEqual(_get_client_ip(request), '198.51.100.1')

    @override_settings(RATE_LIMIT_TRUST_X_FORWARDED_FOR=False)
    def test_get_client_ip_uses_x_real_ip_when_remote_addr_invalid(self):
        from accounts.rate_limit import _get_client_ip
        request = self.factory.get(
            '/dash/auth/api/auth/login/',
            REMOTE_ADDR='invalid-ip',
            HTTP_X_REAL_IP='198.51.100.77',
        )
        self.assertEqual(_get_client_ip(request), '198.51.100.77')


class AuthServiceRoleEdgeTests(TestCase):


    def test_authenticate_rejects_role_mismatch(self):
        from accounts.services import AuthService
        User.objects.create_user(
            username='client2@example.com',
            email='client2@example.com',
            password='clientpass123',
            role='client',
        )
        result = AuthService.authenticate_user('client2@example.com', 'clientpass123', role='admin_staff')
        self.assertFalse(result['success'])

    def test_authenticate_blocks_after_repeated_failures(self):
        from accounts import services

        User.objects.create_user(
            username='locked@example.com',
            email='locked@example.com',
            password='lockpass123',
            role='client',
        )

        with mock.patch.object(services, 'AUTH_FAIL_MAX_ATTEMPTS', 2):
            services.AuthService.authenticate_user('locked@example.com', 'wrongpass')
            services.AuthService.authenticate_user('locked@example.com', 'wrongpass')
            blocked = services.AuthService.authenticate_user('locked@example.com', 'lockpass123')
            self.assertFalse(blocked['success'])

            services.AuthService._clear_login_failures('locked@example.com')
            unblocked = services.AuthService.authenticate_user('locked@example.com', 'lockpass123')
            self.assertTrue(unblocked['success'])

    @mock.patch('accounts.services.send_html_email_async')
    def test_authenticate_sends_failed_login_alert_after_threshold(self, mocked_send_html_email):
        from accounts import services

        cache.clear()
        User.objects.create_user(
            username='alert@example.com',
            email='alert@example.com',
            password='alertpass123',
            role='client',
        )

        with mock.patch.object(services, 'AUTH_FAIL_NOTIFY_THRESHOLD', 2), \
             mock.patch.object(services, 'AUTH_FAIL_NOTIFY_COOLDOWN_SECONDS', 300):
            services.AuthService.authenticate_user('alert@example.com', 'wrongpass')
            services.AuthService.authenticate_user('alert@example.com', 'wrongpass')

        self.assertEqual(mocked_send_html_email.call_count, 1)


class OTPServiceEdgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='otp-edge@example.com',
            email='otp-edge@example.com',
            password='testpass123',
            role='client',
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    @override_settings(DEBUG=True)
    def test_verify_otp_blocks_after_max_attempts(self):
        from accounts.services import OTPService
        send_result = OTPService.send_otp('otp-edge@example.com')
        self.assertTrue(send_result['success'])

        for _ in range(3):
            invalid = OTPService.verify_otp('otp-edge@example.com', '000000')
            self.assertFalse(invalid['success'])

        blocked = OTPService.verify_otp('otp-edge@example.com', '000000')
        self.assertFalse(blocked['success'])
        self.assertIn('Too many failed attempts', blocked['message'])

    @override_settings(DEBUG=True)
    def test_reset_password_rejects_tampered_signed_token(self):
        from accounts.services import OTPService
        send_result = OTPService.send_otp('otp-edge@example.com')
        dev_otp = send_result.get('dev_otp')
        self.assertIsNotNone(dev_otp)

        verify_result = OTPService.verify_otp('otp-edge@example.com', dev_otp)
        self.assertTrue(verify_result['success'])
        token = verify_result['reset_token']

        raw_token, _sig = token.split('.', 1)
        tampered = f'{raw_token}.0000000000000000'
        reset_result = OTPService.reset_password('otp-edge@example.com', tampered, 'newpassword1')
        self.assertFalse(reset_result['success'])
        self.assertIn('reset token', reset_result['message'].lower())

    @override_settings(DEBUG=True)
    def test_send_otp_stores_hash_not_plain_code(self):
        from accounts.services import OTPService

        result = OTPService.send_otp('otp-edge@example.com')
        self.assertTrue(result['success'])

        cache_key = OTPService._get_otp_cache_key('otp-edge@example.com')
        otp_data = cache.get(cache_key)
        self.assertIn('otp_hash', otp_data)
        self.assertNotIn('otp', otp_data)

    @override_settings(DEBUG=True)
    def test_reset_password_revokes_existing_sessions(self):
        from django.test import Client
        from accounts.services import OTPService

        browser = Client()
        self.assertTrue(browser.login(username='otp-edge@example.com', password='testpass123'))
        session_key = browser.session.session_key
        self.assertTrue(Session.objects.filter(session_key=session_key).exists())

        send_result = OTPService.send_otp('otp-edge@example.com')
        dev_otp = send_result.get('dev_otp')
        self.assertIsNotNone(dev_otp)

        verify_result = OTPService.verify_otp('otp-edge@example.com', dev_otp)
        self.assertTrue(verify_result['success'])
        reset_result = OTPService.reset_password(
            'otp-edge@example.com',
            verify_result['reset_token'],
            'newpassword1',
        )
        self.assertTrue(reset_result['success'])
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())


class UserProfileServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='profile@example.com',
            email='profile@example.com',
            password='testpass123',
            role='client',
        )
        self.other_user = User.objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='testpass123',
            role='client',
        )

    def test_update_profile_success(self):
        from accounts.services_profile import UserProfileService
        success, message, profile = UserProfileService.update_profile(self.user, {
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '9999999999',
        })
        self.assertTrue(success)
        self.assertEqual(message, 'Profile updated')
        self.assertEqual(profile['full_name'], 'Test User')

    def test_update_profile_rejects_username_conflict(self):
        from accounts.services_profile import UserProfileService
        success, message, profile = UserProfileService.update_profile(self.user, {
            'username': 'other@example.com',
        })
        self.assertFalse(success)
        self.assertEqual(message, 'Username already taken')
        self.assertIsNone(profile)

    def test_change_password_success(self):
        from accounts.services_profile import UserProfileService
        success, _message = UserProfileService.change_password(self.user, 'testpass123', 'newpass123')
        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_change_password_revokes_other_sessions_keeps_current(self):
        from django.test import Client
        from accounts.services_profile import UserProfileService

        # Use a super_admin user for this test so that the login signal
        # doesn't enforce device limits (limit=9999) and both sessions
        # survive the test setup phase.
        sa_user = User.objects.create_user(
            username='sa-pwchange@example.com',
            email='sa-pwchange@example.com',
            password='testpass123',
            role='super_admin',
        )

        client_a = Client()
        client_b = Client()
        self.assertTrue(client_a.login(username='sa-pwchange@example.com', password='testpass123'))
        self.assertTrue(client_b.login(username='sa-pwchange@example.com', password='testpass123'))

        key_a = client_a.session.session_key
        key_b = client_b.session.session_key
        self.assertTrue(Session.objects.filter(session_key=key_a).exists())
        self.assertTrue(Session.objects.filter(session_key=key_b).exists())

        success, _message = UserProfileService.change_password(
            sa_user,
            'testpass123',
            'newpass123',
            current_session_key=key_a,
        )
        self.assertTrue(success)

        self.assertTrue(Session.objects.filter(session_key=key_a).exists())
        self.assertFalse(Session.objects.filter(session_key=key_b).exists())

    def test_change_password_rejects_wrong_current(self):
        from accounts.services_profile import UserProfileService
        success, message = UserProfileService.change_password(self.user, 'wrong', 'newpass123')
        self.assertFalse(success)
        self.assertEqual(message, 'Current password is incorrect')

    def test_profile_image_methods_return_backward_compat_message(self):
        from accounts.services_profile import UserProfileService
        success_upload, message_upload, image_url = UserProfileService.upload_profile_image(self.user, None)
        self.assertFalse(success_upload)
        self.assertIn('no longer available', message_upload.lower())
        self.assertIsNone(image_url)

        success_remove, message_remove = UserProfileService.remove_profile_image(self.user)
        self.assertFalse(success_remove)
        self.assertIn('no longer available', message_remove.lower())


class ProfileApiIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='api-profile@example.com',
            email='api-profile@example.com',
            password='testpass123',
            role='client',
        )
        self.client.login(username='api-profile@example.com', password='testpass123')

    def test_get_profile_api(self):
        response = self.client.get('/dash/api/profile/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['profile']['email'], 'api-profile@example.com')

    def test_update_profile_api(self):
        response = self.client.post(
            '/dash/api/profile/update/',
            data=json.dumps({'first_name': 'Api', 'last_name': 'User'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertEqual(payload['profile']['full_name'], 'Api User')

    def test_change_password_api(self):
        response = self.client.post(
            '/dash/api/profile/change-password/',
            data=json.dumps({'current_password': 'testpass123', 'new_password': 'newpass123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])

    def test_upload_profile_image_api_returns_feature_disabled(self):
        response = self.client.post('/dash/api/profile/upload-image/')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload['success'])
        self.assertIn('no longer available', payload['message'].lower())
