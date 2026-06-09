"""
Tests for core app.
Covers: User model, SystemSettings, middleware, permissions, subdomain routing, and retry callbacks.
"""
from django.test import TestCase, SimpleTestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.core.signing import Signer, TimestampSigner
from django.http import Http404
import time

User = get_user_model()


# ── User Model Tests ──
class UserModelTests(TestCase):
    def test_create_user_default_role(self):
        user = User.objects.create_user(
            username='u1@test.com', email='u1@test.com', password='pass1234',
        )
        self.assertEqual(user.role, 'operator')

    def test_admin_role_sets_superuser_flags(self):
        user = User.objects.create_user(
            username='admin@test.com', email='admin@test.com', password='pass1234',
            role='admin'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_operator_role_clears_superuser(self):
        user = User.objects.create_user(
            username='op@test.com', email='op@test.com', password='pass1234',
            role='operator'
        )
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_staff)


# ── System Settings Tests ──
class SystemSettingsTests(TestCase):
    def setUp(self):
        from core.models import SystemSettings
        cache.clear()
        SystemSettings.objects.all().delete()

    def tearDown(self):
        cache.clear()

    def test_system_settings_get_value_returns_default(self):
        from core.models import SystemSettings
        value = SystemSettings.get_value('custom_key', default='initial')
        self.assertEqual(value, 'initial')

    def test_system_settings_set_value_persists(self):
        from core.models import SystemSettings
        SystemSettings.set_value('custom_key', 'updated', description='test')
        value = SystemSettings.get_value('custom_key', default='fallback')
        self.assertEqual(value, 'updated')


# ── Permission & Decorator Tests ──
class PermissionTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import AnonymousUser
        self.factory = RequestFactory()
        self.anon = AnonymousUser()
        self.super_admin = User.objects.create_user(
            username='admin@test.com', email='admin@test.com', password='adminpass1', role='admin'
        )
        self.operator = User.objects.create_user(
            username='operator@test.com', email='operator@test.com', password='op-pass', role='operator'
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_permission_service_is_admin(self):
        from core.services.permission_service import PermissionService
        self.assertTrue(PermissionService.is_admin(self.super_admin))
        self.assertFalse(PermissionService.is_admin(self.operator))

    def test_permission_service_is_super_admin(self):
        from core.services.permission_service import PermissionService
        self.assertTrue(PermissionService.is_super_admin(self.super_admin))
        self.assertFalse(PermissionService.is_super_admin(self.operator))

    def test_require_any_admin_decorator_allows_admin(self):
        from core.services.permission_service import require_any_admin
        
        @require_any_admin
        def dummy_view(request):
            return HttpResponse('ok')

        request = self.factory.get('/dash/')
        request.user = self.super_admin
        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)


# ── Threaded Email Callback Retry Tests ──
class ThreadedEmailCallbackRetryTests(TestCase):
    def test_retries_transient_db_lock_then_succeeds(self):
        from core.utils.threaded_email import _run_callback_with_retry

        state = {'count': 0}

        def callback():
            state['count'] += 1
            if state['count'] < 3:
                raise Exception('database table is locked')

        _run_callback_with_retry(callback, 'test callback', max_attempts=3, base_delay=0)
        self.assertEqual(state['count'], 3)
