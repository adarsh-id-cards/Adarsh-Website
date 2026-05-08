"""
Core Services Registry
Cleaned for Website & Manage Website.
"""
from .permission_service import PermissionService
from .activity_service import ActivityService
from .cache_version_service import CacheVersionService

# UserProfileService logic is often small enough to be in its own file
# but we'll import it if it exists.
try:
    from .user_profile_service import UserProfileService
except ImportError:
    UserProfileService = None

__all__ = [
    'PermissionService',
    'ActivityService',
    'UserProfileService',
    'CacheVersionService',
]
