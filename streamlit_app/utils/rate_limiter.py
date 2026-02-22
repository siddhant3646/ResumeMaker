"""
Rate Limiter - Token bucket implementation for API rate limiting
Handles Mistral API 1 RPS limit
"""

import time
import threading
from typing import Optional
from datetime import datetime


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for controlling API request rates
    Perfect for Mistral API's 1 request per second limit
    """
    
    def __init__(
        self,
        rate_per_second: float = 1.0,
        burst_size: int = 1,
        redis_client=None
    ):
        """
        Initialize rate limiter
        
        Args:
            rate_per_second: Number of requests allowed per second
            burst_size: Maximum burst of requests allowed
            redis_client: Optional Redis client for distributed rate limiting
        """
        self.rate = rate_per_second
        self.burst_size = burst_size
        self.tokens = burst_size
        self.last_update = time.time()
        self.lock = threading.Lock()
        self.redis = redis_client
        self.enabled = True
        
        # Redis key for distributed rate limiting
        self.redis_key = "mistral_api_rate_limit"
    
    def _add_tokens(self):
        """Add tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_update
        tokens_to_add = elapsed * self.rate
        
        self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
        self.last_update = now
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token to make a request
        
        Args:
            timeout: Maximum time to wait for a token (None = wait forever)
            
        Returns:
            bool: True if token acquired, False if timeout
        """
        if not self.enabled:
            return True
        
        start_time = time.time()
        
        while True:
            with self.lock:
                self._add_tokens()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            # Wait a bit before trying again
            time.sleep(0.1)
    
    def try_acquire(self) -> bool:
        """
        Try to acquire a token without waiting
        
        Returns:
            bool: True if token acquired, False otherwise
        """
        if not self.enabled:
            return True
        
        with self.lock:
            self._add_tokens()
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            return False
    
    def get_wait_time(self) -> float:
        """
        Get estimated wait time for next token
        
        Returns:
            float: Seconds to wait
        """
        if not self.enabled:
            return 0.0
        
        with self.lock:
            self._add_tokens()
            
            if self.tokens >= 1:
                return 0.0
            
            # Calculate time needed for next token
            tokens_needed = 1 - self.tokens
            return tokens_needed / self.rate


class UserRateLimiter:
    """
    Per-user rate limiting
    Prevents abuse from individual users
    """
    
    def __init__(
        self,
        max_requests_per_hour: int = 10,
        redis_client=None
    ):
        """
        Initialize user rate limiter
        
        Args:
            max_requests_per_hour: Maximum requests per user per hour
            redis_client: Redis client for distributed tracking
        """
        self.max_requests = max_requests_per_hour
        self.redis = redis_client
        self.enabled = redis_client is not None
        self.window_seconds = 3600  # 1 hour
    
    def _get_key(self, user_id: str) -> str:
        """Get Redis key for user"""
        return f"user_rate_limit:{user_id}"
    
    def can_make_request(self, user_id: str) -> bool:
        """
        Check if user can make a request
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            bool: True if request allowed
        """
        if not self.enabled or not user_id:
            return True
        
        try:
            key = self._get_key(user_id)
            current_count = self.redis.get(key)
            
            if current_count is None:
                return True
            
            return int(current_count) < self.max_requests
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    def record_request(self, user_id: str):
        """
        Record a request from user
        
        Args:
            user_id: User's unique identifier
        """
        if not self.enabled or not user_id:
            return
        
        try:
            key = self._get_key(user_id)
            
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window_seconds)
            pipe.execute()
        except Exception as e:
            print(f"Error recording request: {e}")
    
    def get_remaining_requests(self, user_id: str) -> int:
        """
        Get remaining requests for user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            int: Number of remaining requests
        """
        if not self.enabled or not user_id:
            return self.max_requests
        
        try:
            key = self._get_key(user_id)
            current_count = self.redis.get(key)
            
            if current_count is None:
                return self.max_requests
            
            return max(0, self.max_requests - int(current_count))
        except Exception as e:
            print(f"Error getting remaining requests: {e}")
            return self.max_requests
    
    def get_reset_time(self, user_id: str) -> Optional[datetime]:
        """
        Get when rate limit resets for user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            datetime or None
        """
        if not self.enabled or not user_id:
            return None
        
        try:
            key = self._get_key(user_id)
            ttl = self.redis.ttl(key)
            
            if ttl > 0:
                return datetime.now() + __import__('datetime').timedelta(seconds=ttl)
            
            return None
        except:
            return None


class GlobalRateLimiter:
    """
    Global rate limiting across all users
    Prevents overwhelming external APIs
    """
    
    def __init__(
        self,
        max_requests_per_minute: int = 50,
        redis_client=None
    ):
        """
        Initialize global rate limiter
        
        Args:
            max_requests_per_minute: Maximum requests across all users per minute
            redis_client: Redis client for distributed tracking
        """
        self.max_requests = max_requests_per_minute
        self.redis = redis_client
        self.enabled = redis_client is not None
        self.window_seconds = 60  # 1 minute
        self.key = "global_rate_limit"
    
    def can_make_request(self) -> bool:
        """Check if global rate limit allows request"""
        if not self.enabled:
            return True
        
        try:
            current_count = self.redis.get(self.key)
            
            if current_count is None:
                return True
            
            return int(current_count) < self.max_requests
        except:
            return True
    
    def record_request(self):
        """Record a global request"""
        if not self.enabled:
            return
        
        try:
            pipe = self.redis.pipeline()
            pipe.incr(self.key)
            pipe.expire(self.key, self.window_seconds)
            pipe.execute()
        except:
            pass
    
    def get_current_count(self) -> int:
        """Get current global request count"""
        if not self.enabled:
            return 0
        
        try:
            count = self.redis.get(self.key)
            return int(count) if count else 0
        except:
            return 0


# Singleton instances
_api_rate_limiter = None
_user_rate_limiter = None
_global_rate_limiter = None

def get_api_rate_limiter(redis_client=None) -> TokenBucketRateLimiter:
    """Get API rate limiter singleton (1 RPS for Mistral)"""
    global _api_rate_limiter
    if _api_rate_limiter is None:
        _api_rate_limiter = TokenBucketRateLimiter(
            rate_per_second=1.0,  # 1 request per second
            burst_size=1,
            redis_client=redis_client
        )
    return _api_rate_limiter

def get_user_rate_limiter(redis_client=None) -> UserRateLimiter:
    """Get user rate limiter singleton (10 requests/hour)"""
    global _user_rate_limiter
    if _user_rate_limiter is None:
        _user_rate_limiter = UserRateLimiter(
            max_requests_per_hour=10,
            redis_client=redis_client
        )
    return _user_rate_limiter

def get_global_rate_limiter(redis_client=None) -> GlobalRateLimiter:
    """Get global rate limiter singleton (50 requests/minute)"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = GlobalRateLimiter(
            max_requests_per_minute=50,
            redis_client=redis_client
        )
    return _global_rate_limiter
