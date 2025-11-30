"""
Caching utilities for the Planning Intelligence Agent.
Implements multi-layer caching with Redis and local fallback.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, TypeVar

import structlog

from app.core.config import settings

logger = structlog.get_logger()

T = TypeVar("T")


class CacheManager:
    """
    Multi-layer cache manager with Redis primary and local fallback.
    Supports TTL, cache invalidation, and key prefixing.
    """

    def __init__(self):
        self._redis = None
        self._local_cache: dict[str, tuple[Any, datetime]] = {}
        self._initialized = False
        self._max_local_size = 1000

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._initialized:
            return self._redis

        try:
            import redis.asyncio as redis

            self._redis = await redis.from_url(
                settings.redis_url,
                password=settings.redis_password or None,
                db=settings.redis_db,
                decode_responses=True,
            )
            await self._redis.ping()
            self._initialized = True
            logger.info("Cache: Redis connection established")
        except Exception as e:
            logger.warning("Cache: Redis unavailable, using local cache", error=str(e))
            self._redis = None
            self._initialized = True

        return self._redis

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from prefix and arguments."""
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"cache:{prefix}:{key_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        redis = await self._get_redis()

        if redis:
            try:
                value = await redis.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning("Cache get error", key=key, error=str(e))

        # Fallback to local cache
        if key in self._local_cache:
            value, expires = self._local_cache[key]
            if expires > datetime.utcnow():
                return value
            else:
                del self._local_cache[key]

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600,
    ) -> bool:
        """Set value in cache with TTL."""
        redis = await self._get_redis()
        serialized = json.dumps(value)

        if redis:
            try:
                await redis.setex(key, ttl_seconds, serialized)
                return True
            except Exception as e:
                logger.warning("Cache set error", key=key, error=str(e))

        # Fallback to local cache
        self._cleanup_local_cache()
        expires = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._local_cache[key] = (value, expires)
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        redis = await self._get_redis()

        if redis:
            try:
                await redis.delete(key)
            except Exception as e:
                logger.warning("Cache delete error", key=key, error=str(e))

        if key in self._local_cache:
            del self._local_cache[key]

        return True

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        redis = await self._get_redis()
        count = 0

        if redis:
            try:
                cursor = 0
                while True:
                    cursor, keys = await redis.scan(cursor, match=pattern)
                    if keys:
                        await redis.delete(*keys)
                        count += len(keys)
                    if cursor == 0:
                        break
            except Exception as e:
                logger.warning("Cache delete pattern error", pattern=pattern, error=str(e))

        # Clean local cache
        keys_to_delete = [
            k for k in self._local_cache.keys()
            if self._matches_pattern(k, pattern)
        ]
        for key in keys_to_delete:
            del self._local_cache[key]
            count += 1

        return count

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches Redis-style pattern."""
        import fnmatch
        redis_pattern = pattern.replace("*", "*")
        return fnmatch.fnmatch(key, redis_pattern)

    def _cleanup_local_cache(self):
        """Remove expired entries and enforce size limit."""
        now = datetime.utcnow()

        # Remove expired entries
        expired = [k for k, (_, exp) in self._local_cache.items() if exp <= now]
        for key in expired:
            del self._local_cache[key]

        # Enforce size limit (remove oldest entries)
        if len(self._local_cache) >= self._max_local_size:
            sorted_keys = sorted(
                self._local_cache.keys(),
                key=lambda k: self._local_cache[k][1]
            )
            for key in sorted_keys[: len(sorted_keys) // 2]:
                del self._local_cache[key]

    async def cached(
        self,
        prefix: str,
        ttl_seconds: int = 3600,
    ):
        """Decorator for caching function results."""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            async def wrapper(*args, **kwargs) -> T:
                key = self._generate_key(prefix, *args, **kwargs)

                # Try to get from cache
                cached_value = await self.get(key)
                if cached_value is not None:
                    logger.debug("Cache hit", key=key, prefix=prefix)
                    return cached_value

                # Execute function and cache result
                logger.debug("Cache miss", key=key, prefix=prefix)
                result = await func(*args, **kwargs)

                if result is not None:
                    await self.set(key, result, ttl_seconds)

                return result

            return wrapper
        return decorator


# Global cache manager instance
cache = CacheManager()


# ==================== Query Response Cache ====================

class QueryCache:
    """
    Specialized cache for query responses.
    Implements semantic similarity caching.
    """

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.ttl = 3600 * 24  # 24 hours for query responses

    def _normalize_query(self, query: str) -> str:
        """Normalize query for caching."""
        # Basic normalization: lowercase, strip whitespace
        normalized = query.lower().strip()
        # Remove extra whitespace
        normalized = " ".join(normalized.split())
        return normalized

    def _hash_query(self, query: str, borough: Optional[str] = None) -> str:
        """Generate hash for query + borough combination."""
        normalized = self._normalize_query(query)
        key_data = f"{normalized}:{borough or 'all'}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def get_response(
        self,
        query: str,
        borough: Optional[str] = None,
    ) -> Optional[dict]:
        """Get cached response for query."""
        query_hash = self._hash_query(query, borough)
        key = f"query_response:{query_hash}"
        return await self.cache.get(key)

    async def set_response(
        self,
        query: str,
        response: dict,
        borough: Optional[str] = None,
    ) -> bool:
        """Cache response for query."""
        query_hash = self._hash_query(query, borough)
        key = f"query_response:{query_hash}"
        return await self.cache.set(key, response, self.ttl)

    async def invalidate_borough(self, borough: str) -> int:
        """Invalidate all cached queries for a borough."""
        # Note: This is a best-effort operation
        # In production, consider using a more sophisticated invalidation strategy
        return await self.cache.delete_pattern(f"query_response:*:{borough}")


# ==================== Embedding Cache ====================

class EmbeddingCache:
    """Cache for text embeddings to reduce API calls."""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.ttl = 3600 * 24 * 7  # 7 days for embeddings

    def _hash_text(self, text: str) -> str:
        """Generate hash for text."""
        return hashlib.sha256(text.encode()).hexdigest()

    async def get_embedding(self, text: str) -> Optional[list[float]]:
        """Get cached embedding for text."""
        text_hash = self._hash_text(text)
        key = f"embedding:{text_hash}"
        return await self.cache.get(key)

    async def set_embedding(self, text: str, embedding: list[float]) -> bool:
        """Cache embedding for text."""
        text_hash = self._hash_text(text)
        key = f"embedding:{text_hash}"
        return await self.cache.set(key, embedding, self.ttl)

    async def get_batch(self, texts: list[str]) -> dict[str, Optional[list[float]]]:
        """Get cached embeddings for multiple texts."""
        results = {}
        for text in texts:
            results[text] = await self.get_embedding(text)
        return results


# Global cache instances
query_cache = QueryCache(cache)
embedding_cache = EmbeddingCache(cache)
