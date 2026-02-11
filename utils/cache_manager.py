"""
Cache Manager - Redis-based caching for AI API responses
Reduces API costs and improves performance
"""

import json
import hashlib
import time
from typing import Optional, Dict, Any, Union
from datetime import datetime


class CacheManager:
    """
    Manages caching of AI API responses using Redis
    
    Cache Strategy:
    - Job Analysis: 24 hours TTL (JD doesn't change often)
    - Resume Generation: 7 days TTL (same resume + JD = same result)
    - ATS Scores: 24 hours TTL
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize cache manager
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.enabled = redis_client is not None
        
        # TTL configurations (in seconds)
        self.ttl_config = {
            "job_analysis": 86400,      # 24 hours
            "resume_generation": 604800, # 7 days
            "ats_score": 86400,         # 24 hours
            "bullet_enhancement": 3600,  # 1 hour
        }
    
    def _generate_key(
        self,
        cache_type: str,
        data: Union[str, Dict, Any],
        additional_context: str = ""
    ) -> str:
        """
        Generate cache key from data
        
        Args:
            cache_type: Type of cache entry
            data: Data to hash for key
            additional_context: Additional context for key
            
        Returns:
            str: Cache key
        """
        # Convert data to string if dict
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Create hash
        key_content = f"{cache_type}:{data_str}:{additional_context}"
        hash_value = hashlib.md5(key_content.encode()).hexdigest()
        
        return f"cache:{cache_type}:{hash_value}"
    
    def get(
        self,
        cache_type: str,
        data: Union[str, Dict, Any],
        additional_context: str = ""
    ) -> Optional[Any]:
        """
        Get cached value
        
        Args:
            cache_type: Type of cache entry
            data: Data used to generate key
            additional_context: Additional context for key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_key(cache_type, data, additional_context)
            cached_data = self.redis.get(key)
            
            if cached_data:
                return json.loads(cached_data)
            
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(
        self,
        cache_type: str,
        data: Union[str, Dict, Any],
        value: Any,
        additional_context: str = "",
        custom_ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached value
        
        Args:
            cache_type: Type of cache entry
            data: Data used to generate key
            value: Value to cache
            additional_context: Additional context for key
            custom_ttl: Custom TTL in seconds (optional)
            
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(cache_type, data, additional_context)
            ttl = custom_ttl or self.ttl_config.get(cache_type, 3600)
            
            self.redis.setex(
                key,
                ttl,
                json.dumps(value)
            )
            
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(
        self,
        cache_type: str,
        data: Union[str, Dict, Any],
        additional_context: str = ""
    ) -> bool:
        """
        Delete cached value
        
        Args:
            cache_type: Type of cache entry
            data: Data used to generate key
            additional_context: Additional context for key
            
        Returns:
            bool: True if successful
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(cache_type, data, additional_context)
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def exists(
        self,
        cache_type: str,
        data: Union[str, Dict, Any],
        additional_context: str = ""
    ) -> bool:
        """
        Check if key exists in cache
        
        Args:
            cache_type: Type of cache entry
            data: Data used to generate key
            additional_context: Additional context for key
            
        Returns:
            bool: True if exists
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(cache_type, data, additional_context)
            return self.redis.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    def get_ttl(
        self,
        cache_type: str,
        data: Union[str, Dict, Any],
        additional_context: str = ""
    ) -> int:
        """
        Get remaining TTL for key
        
        Returns:
            int: Seconds remaining, -1 if no TTL, -2 if not found
        """
        if not self.enabled:
            return -2
        
        try:
            key = self._generate_key(cache_type, data, additional_context)
            return self.redis.ttl(key)
        except Exception as e:
            print(f"Cache TTL error: {e}")
            return -2
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            # Count cache keys by type
            stats = {"enabled": True, "by_type": {}}
            
            for cache_type in self.ttl_config.keys():
                pattern = f"cache:{cache_type}:*"
                count = len(list(self.redis.scan_iter(pattern)))
                stats["by_type"][cache_type] = count
            
            stats["total_cached"] = sum(stats["by_type"].values())
            
            return stats
        except Exception as e:
            return {"enabled": True, "error": str(e)}
    
    def clear_all(self, cache_type: Optional[str] = None) -> int:
        """
        Clear all cache entries
        
        Args:
            cache_type: Specific type to clear (optional)
            
        Returns:
            int: Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            if cache_type:
                pattern = f"cache:{cache_type}:*"
            else:
                pattern = "cache:*"
            
            keys = list(self.redis.scan_iter(pattern))
            if keys:
                self.redis.delete(*keys)
            
            return len(keys)
        except Exception as e:
            print(f"Cache clear error: {e}")
            return 0
    
    def clear_expired(self) -> int:
        """Clear expired keys (Redis does this automatically, but can force)"""
        # Redis handles expiration automatically
        # This method is for manual cleanup if needed
        return 0


# Decorator for caching function results
def cached(
    cache_type: str,
    ttl: Optional[int] = None,
    key_func: Optional[callable] = None
):
    """
    Decorator to cache function results
    
    Usage:
        @cached("job_analysis", ttl=86400)
        def analyze_job(job_description):
            # Expensive operation
            return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get cache manager instance
            from utils.cache_manager import get_cache_manager
            cache = get_cache_manager()
            
            if not cache.enabled:
                return func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key_data = key_func(*args, **kwargs)
            else:
                # Use function name and arguments
                cache_key_data = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
            
            # Try to get from cache
            cached_value = cache.get(cache_type, cache_key_data)
            if cached_value is not None:
                print(f"Cache hit for {func.__name__}")
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_type, cache_key_data, result, custom_ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# Singleton instance
_cache_manager = None

def get_cache_manager(redis_client=None) -> CacheManager:
    """Get or create CacheManager singleton"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(redis_client)
    return _cache_manager
