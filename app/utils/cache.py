"""
Caching utilities and decorators for FastAPI
"""

from functools import wraps
from typing import Callable, Optional, Any
import hashlib
import json
from app.utils.redis_client import cache_get, cache_set, cache_delete_pattern
import logging

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from function arguments
    
    Args:
        prefix: Cache key prefix
        *args: Positional arguments
        **kwargs: Keyword arguments
    
    Returns:
        Hashed cache key
    """
    # Create a string representation of arguments
    key_data = {
        "args": args,
        "kwargs": kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"{prefix}:{key_hash}"


def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable] = None
):
    """
    Decorator to cache function results in Redis
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds (None = use default)
        key_builder: Custom function to build cache key
    
    Example:
        @cached(prefix="properties", ttl=600)
        def get_all_properties(db: Session):
            return db.query(Property).all()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cached_value
            
            # Execute function
            logger.debug(f"Cache MISS for key: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate all cache keys matching a pattern
    
    Args:
        pattern: Key pattern (e.g., 'properties:*')
    
    Returns:
        Number of keys deleted
    
    Example:
        # After updating a property, invalidate all property caches
        invalidate_cache("properties:*")
    """
    deleted = cache_delete_pattern(pattern)
    logger.info(f"Invalidated {deleted} cache keys matching pattern: {pattern}")
    return deleted


# Common cache key builders for API endpoints

def user_cache_key(user_id: int, *args, **kwargs) -> str:
    """Build cache key for user-specific data"""
    return f"user:{user_id}:{generate_cache_key('data', *args, **kwargs)}"


def property_cache_key(property_id: int, *args, **kwargs) -> str:
    """Build cache key for property-specific data"""
    return f"property:{property_id}:{generate_cache_key('data', *args, **kwargs)}"


def list_cache_key(resource: str, page: int = 1, page_size: int = 10, **filters) -> str:
    """Build cache key for paginated list endpoints"""
    filter_hash = hashlib.md5(
        json.dumps(filters, sort_keys=True, default=str).encode()
    ).hexdigest()
    return f"{resource}:list:p{page}:s{page_size}:{filter_hash}"
