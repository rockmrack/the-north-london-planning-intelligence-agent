"""Caching service using Redis for performance optimization."""

import hashlib
import json
from typing import Any, List, Optional

from app.core.config import settings


class CacheService:
    """Service for caching query results and embeddings."""

    def __init__(self):
        self._redis = None
        self._local_cache: dict = {}  # Fallback for development

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = await redis.from_url(
                    settings.redis_url,
                    password=settings.redis_password or None,
                    db=settings.redis_db,
                    decode_responses=True,
                )
            except Exception:
                # Fallback to local cache if Redis not available
                self._redis = None
        return self._redis

    def _generate_key(self, prefix: str, data: str) -> str:
        """Generate a cache key from data."""
        hash_value = hashlib.md5(data.encode()).hexdigest()
        return f"{prefix}:{hash_value}"

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        redis = await self._get_redis()
        if redis:
            try:
                value = await redis.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass

        # Fallback to local cache
        return self._local_cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,  # 1 hour default
    ) -> bool:
        """Set a value in cache with TTL."""
        serialized = json.dumps(value)

        redis = await self._get_redis()
        if redis:
            try:
                await redis.setex(key, ttl, serialized)
                return True
            except Exception:
                pass

        # Fallback to local cache (no TTL)
        self._local_cache[key] = value
        return True

    async def delete(self, key: str) -> bool:
        """Delete a value from cache."""
        redis = await self._get_redis()
        if redis:
            try:
                await redis.delete(key)
            except Exception:
                pass

        if key in self._local_cache:
            del self._local_cache[key]
        return True

    # ==================== Specialized Cache Methods ====================

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding for text."""
        key = self._generate_key("emb", text)
        return await self.get(key)

    async def set_embedding(
        self,
        text: str,
        embedding: List[float],
        ttl: int = 86400 * 7,  # 7 days
    ) -> bool:
        """Cache an embedding for text."""
        key = self._generate_key("emb", text)
        return await self.set(key, embedding, ttl)

    async def get_query_result(
        self,
        query: str,
        borough: Optional[str] = None,
    ) -> Optional[dict]:
        """Get cached query result."""
        cache_key = f"{query}:{borough or 'all'}"
        key = self._generate_key("query", cache_key)
        return await self.get(key)

    async def set_query_result(
        self,
        query: str,
        result: dict,
        borough: Optional[str] = None,
        ttl: int = 3600,  # 1 hour
    ) -> bool:
        """Cache a query result."""
        cache_key = f"{query}:{borough or 'all'}"
        key = self._generate_key("query", cache_key)
        return await self.set(key, result, ttl)

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get cached session data."""
        key = f"session:{session_id}"
        return await self.get(key)

    async def set_session(
        self,
        session_id: str,
        data: dict,
        ttl: int = 86400,  # 24 hours
    ) -> bool:
        """Cache session data."""
        key = f"session:{session_id}"
        return await self.set(key, data, ttl)

    async def increment_query_count(self, session_id: str) -> int:
        """Increment and return query count for a session."""
        redis = await self._get_redis()
        key = f"qcount:{session_id}"

        if redis:
            try:
                count = await redis.incr(key)
                await redis.expire(key, 86400)  # 24 hour expiry
                return count
            except Exception:
                pass

        # Fallback
        current = self._local_cache.get(key, 0) + 1
        self._local_cache[key] = current
        return current

    async def get_query_count(self, session_id: str) -> int:
        """Get query count for a session."""
        redis = await self._get_redis()
        key = f"qcount:{session_id}"

        if redis:
            try:
                count = await redis.get(key)
                return int(count) if count else 0
            except Exception:
                pass

        return self._local_cache.get(key, 0)

    async def clear_session_cache(self, session_id: str) -> bool:
        """Clear all cache entries for a session."""
        await self.delete(f"session:{session_id}")
        await self.delete(f"qcount:{session_id}")
        return True


# Global instance
cache_service = CacheService()
