# Views Package - Cleaned for Website & Manage Website architecture

from .auth import (
    login_view,
    logout_view,
    inactive_view,
    maintenance_view,
    api_check_maintenance,
    api_check_email,
    api_login,
    api_forgot_password,
    api_verify_otp,
    api_reset_password,
    api_impersonate_start,
    api_impersonate_stop,
    api_impersonate_users,
)

from .base import (
    dashboard,
    api_recent_activity,
    api_health,
    api_debug_permissions,
)

from .settings_api import (
    api_get_profile,
    api_update_profile,
    api_change_password,
)

from .user_api import (
    api_user_list,
    api_user_create,
    api_user_update,
    api_user_delete,
    api_get_me,
)

from . import errors
