"""
Redis Cache Manager for Spotify Clone Backend
Handles both TTL-based caching and active cache invalidation
"""

import json
import redis.asyncio as redis
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manages Redis caching for the application.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis connection"""
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Establish Redis connection"""
        try:
            self.client = await redis.from_url(self.redis_url)
            await self.client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis disconnected")
    #TTL caching
    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Retrieve cached data
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized cached data or None
        """
        if not self.client:
            return None
        
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache retrieval failed for {key}: {e}")
        
        return None
    
    async def set_cache(self, key: str, value: Any, ttl: int = 300):
        """
        Store data in cache with TTL
        
        Args:
            key: Cache key
            value: Data to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        if not self.client:
            return
        
        try:
            serialized = json.dumps(value)
            await self.client.setex(key, ttl, serialized)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")
    
    async def delete_cache(self, key: str):
        """Delete a specific cache entry"""
        if not self.client:
            return
        
        try:
            await self.client.delete(key)
            logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.warning(f"Cache deletion failed for {key}: {e}")
    
    async def delete_pattern(self, pattern: str):
        """
        Delete cache entries matching a pattern (e.g., "song:*")
        """
        if not self.client:
            return
        
        try:
            cursor = 0
            count = 0
            
            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern)
                if keys:
                    await self.client.delete(*keys)
                    count += len(keys)
                
                if cursor == 0:
                    break
            
            logger.debug(f"Cache deleted: {count} keys matching pattern '{pattern}'")
        except Exception as e:
            logger.warning(f"Pattern deletion failed for {pattern}: {e}")

    async def invalidate_aggregations(self):
        """
        Invalidate all aggregation caches
        Used when data mutates (create/update/delete)
        """
        patterns = [
            "aggregation:*",  # All aggregations
            "artists:*",      # Artist groupings
            "list:*"          # List caches
        ]
        
        for pattern in patterns:
            await self.delete_pattern(pattern)
    
    async def invalidate_album_cache(self, album_id: str):
        """Invalidate specific album caches"""
        await self.delete_cache(f"album:song_count:{album_id}")
        # invalidate artist aggregation
        await self.delete_pattern("artists:*")
    
    async def invalidate_song_cache(self, song_id: str):
        """Invalidate specific song caches"""
        # Invalidate artist aggregation
        await self.delete_pattern("artists:*")
        # Invalidate playlist aggregations
        await self.delete_pattern("playlist:*")
        # Invalidate album song count
        await self.delete_pattern("album:song_count:*")
    
    async def invalidate_playlist_cache(self, playlist_id: str):
        """Invalidate specific playlist caches"""
        await self.delete_cache(f"playlist:songs:{playlist_id}")
        await self.delete_cache(f"playlist:aggregation:{playlist_id}")


# Global cache manager instance
cache_manager = None

async def get_cache_manager() -> CacheManager:
    """Get or create the global cache manager"""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager()
        await cache_manager.connect()
    return cache_manager
