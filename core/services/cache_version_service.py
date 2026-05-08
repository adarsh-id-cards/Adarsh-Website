import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

class CacheVersionService:
    """
    Service to manage cache versioning for invalidation.
    """
    
    @staticmethod
    def get(key: str, scope: str = 'global') -> int:
        """
        Get the current version for a given key and scope.
        """
        cache_key = f'cache_version:{scope}:{key}'
        return cache.get(cache_key, 1)

    @staticmethod
    def bump(key: str, scope: str = 'global') -> int:
        """
        Increment the version for a given key and scope.
        """
        cache_key = f'cache_version:{scope}:{key}'
        try:
            new_version = cache.get(cache_key, 1) + 1
            cache.set(cache_key, new_version, None)  # Persistent until manual clear
            logger.debug(f"Bumped cache version for {scope}:{key} to {new_version}")
            return new_version
        except Exception as e:
            logger.error(f"Failed to bump cache version for {scope}:{key}: {e}")
            return 1
