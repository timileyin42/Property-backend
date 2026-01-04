"""
Redis client utility for caching and session management
"""

import redis
from redis.connection import ConnectionPool
from typing import Optional, Any
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with connection pooling"""
    
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    
    @classmethod
    def get_pool(cls) -> ConnectionPool:
        """Get or create Redis connection pool"""
        if cls._pool is None:
            try:
                cls._pool = redis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                logger.info("Redis connection pool created")
            except Exception as e:
                logger.error(f"Failed to create Redis pool: {e}")
                raise
        return cls._pool
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """Get or create Redis client"""
        if cls._client is None:
            try:
                pool = cls.get_pool()
                cls._client = redis.Redis(connection_pool=pool)
                # Test connection
                cls._client.ping()
                logger.info("Redis client connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return cls._client
    
    @classmethod
    def close(cls):
        """Close Redis connection"""
        if cls._client:
            cls._client.close()
            cls._client = None
        if cls._pool:
            cls._pool.disconnect()
            cls._pool = None
        logger.info("Redis connection closed")


# Convenience functions
def get_redis() -> redis.Redis:
    """Get Redis client instance"""
    return RedisClient.get_client()


def cache_set(key: str, value: Any, ttl: int = None) -> bool:
    """
    Set a value in Redis cache
    
    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default: from settings)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis()
        serialized_value = json.dumps(value) if not isinstance(value, str) else value
        ttl = ttl or settings.REDIS_CACHE_TTL
        client.setex(key, ttl, serialized_value)
        return True
    except Exception as e:
        logger.error(f"Redis cache_set error for key '{key}': {e}")
        return False


def cache_get(key: str, default=None) -> Any:
    """
    Get a value from Redis cache
    
    Args:
        key: Cache key
        default: Default value if key not found
    
    Returns:
        Cached value or default
    """
    try:
        client = get_redis()
        value = client.get(key)
        if value is None:
            return default
        
        # Try to deserialize JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    except Exception as e:
        logger.error(f"Redis cache_get error for key '{key}': {e}")
        return default


def cache_delete(key: str) -> bool:
    """
    Delete a key from Redis cache
    
    Args:
        key: Cache key to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis()
        client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Redis cache_delete error for key '{key}': {e}")
        return False


def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching a pattern
    
    Args:
        pattern: Key pattern (e.g., 'user:*')
    
    Returns:
        Number of keys deleted
    """
    try:
        client = get_redis()
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Redis cache_delete_pattern error for pattern '{pattern}': {e}")
        return 0


def cache_exists(key: str) -> bool:
    """
    Check if a key exists in Redis
    
    Args:
        key: Cache key
    
    Returns:
        True if key exists, False otherwise
    """
    try:
        client = get_redis()
        return bool(client.exists(key))
    except Exception as e:
        logger.error(f"Redis cache_exists error for key '{key}': {e}")
        return False


def increment(key: str, amount: int = 1, ttl: int = None) -> Optional[int]:
    """
    Increment a counter in Redis
    
    Args:
        key: Counter key
        amount: Amount to increment by
        ttl: Time to live in seconds (optional)
    
    Returns:
        New value after increment, or None on error
    """
    try:
        client = get_redis()
        new_value = client.incrby(key, amount)
        if ttl:
            client.expire(key, ttl)
        return new_value
    except Exception as e:
        logger.error(f"Redis increment error for key '{key}': {e}")
        return None


def health_check() -> dict:
    """
    Check Redis connection health
    
    Returns:
        Dictionary with health status
    """
    try:
        client = get_redis()
        client.ping()
        info = client.info()
        return {
            "status": "healthy",
            "connected": True,
            "version": info.get("redis_version"),
            "used_memory": info.get("used_memory_human"),
            "connected_clients": info.get("connected_clients")
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }
