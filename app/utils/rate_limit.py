"""
Rate limiting utility for preventing spam and abuse
"""

from fastapi import HTTPException, status
from app.utils.redis_client import RedisClient
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis for distributed rate limiting"""
    
    @staticmethod
    def check_rate_limit(
        key: str,
        max_requests: int = 5,
        window_seconds: int = 3600
    ) -> bool:
        """
        Check if request exceeds rate limit.
        
        Args:
            key: Unique identifier (e.g., email, IP address)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if within limit, raises HTTPException if exceeded
            
        Raises:
            HTTPException: 429 Too Many Requests if limit exceeded
        """
        try:
            client = RedisClient.get_client()
            current = client.incr(key)
            
            # Set expiration on first request
            if current == 1:
                client.expire(key, window_seconds)
            
            if current > max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Please try again in {window_seconds // 60} minutes."
                )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open - don't block legitimate requests if Redis is down
            return True


def rate_limit_signup(email: str) -> bool:
    """
    Rate limit signup attempts per email.
    Max 5 signup attempts per email per hour.
    """
    return RateLimiter.check_rate_limit(
        key=f"signup:{email}",
        max_requests=5,
        window_seconds=3600  # 1 hour
    )


def rate_limit_ip(ip_address: str) -> bool:
    """
    Rate limit signup attempts per IP address.
    Max 20 signup attempts per IP per hour.
    """
    return RateLimiter.check_rate_limit(
        key=f"signup_ip:{ip_address}",
        max_requests=20,
        window_seconds=3600  # 1 hour
    )
