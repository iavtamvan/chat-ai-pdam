"""
Redis Caching Service
Critical for achieving < 10 second response time
"""

import json
import hashlib
import asyncio
from typing import Optional, Any, List
from datetime import timedelta
import redis.asyncio as redis
from contextlib import asynccontextmanager

from app.core.config import settings


class CacheService:
    """High-performance Redis caching for AI responses"""
    
    _instance: Optional['CacheService'] = None
    _pool: Optional[redis.ConnectionPool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def init(self):
        """Initialize Redis connection pool"""
        if self._pool is None:
            self._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=50,
                decode_responses=True
            )
        return self
    
    @asynccontextmanager
    async def get_connection(self):
        """Get Redis connection from pool"""
        conn = redis.Redis(connection_pool=self._pool)
        try:
            yield conn
        finally:
            await conn.close()
    
    def _generate_key(self, prefix: str, data: str) -> str:
        """Generate cache key from data"""
        hash_val = hashlib.md5(data.encode()).hexdigest()[:16]
        return f"pdam:{prefix}:{hash_val}"
    
    # === Response Caching ===
    
    async def get_cached_response(self, question: str, context_hash: str = "") -> Optional[str]:
        """Get cached AI response for a question"""
        if not settings.CACHE_ENABLED:
            return None
        
        try:
            key = self._generate_key("response", f"{question}:{context_hash}")
            async with self.get_connection() as conn:
                cached = await conn.get(key)
                if cached:
                    data = json.loads(cached)
                    return data.get("answer")
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    async def set_cached_response(
        self, 
        question: str, 
        answer: str, 
        context_hash: str = "",
        sources: List = None
    ):
        """Cache AI response"""
        if not settings.CACHE_ENABLED:
            return
        
        try:
            key = self._generate_key("response", f"{question}:{context_hash}")
            data = {
                "answer": answer,
                "sources": sources or [],
                "cached": True
            }
            async with self.get_connection() as conn:
                await conn.setex(
                    key,
                    settings.REDIS_TTL_RESPONSES,
                    json.dumps(data, ensure_ascii=False)
                )
        except Exception as e:
            print(f"Cache set error: {e}")
    
    # === Embedding Caching ===
    
    async def get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding vector"""
        if not settings.CACHE_ENABLED:
            return None
        
        try:
            key = self._generate_key("embed", text[:500])  # Limit key length
            async with self.get_connection() as conn:
                cached = await conn.get(key)
                if cached:
                    return json.loads(cached)
        except Exception:
            pass
        return None
    
    async def set_cached_embedding(self, text: str, embedding: List[float]):
        """Cache embedding vector"""
        if not settings.CACHE_ENABLED:
            return
        
        try:
            key = self._generate_key("embed", text[:500])
            async with self.get_connection() as conn:
                await conn.setex(
                    key,
                    settings.REDIS_TTL_EMBEDDINGS,
                    json.dumps(embedding)
                )
        except Exception:
            pass
    
    # === Batch Embedding Cache ===
    
    async def get_cached_embeddings_batch(
        self, 
        texts: List[str]
    ) -> tuple[List[Optional[List[float]]], List[int]]:
        """Get cached embeddings for batch of texts"""
        results = [None] * len(texts)
        missing_indices = []
        
        if not settings.CACHE_ENABLED:
            return results, list(range(len(texts)))
        
        try:
            async with self.get_connection() as conn:
                pipe = conn.pipeline()
                keys = [self._generate_key("embed", t[:500]) for t in texts]
                
                for key in keys:
                    pipe.get(key)
                
                cached_values = await pipe.execute()
                
                for i, cached in enumerate(cached_values):
                    if cached:
                        results[i] = json.loads(cached)
                    else:
                        missing_indices.append(i)
        except Exception:
            missing_indices = list(range(len(texts)))
        
        return results, missing_indices
    
    async def set_cached_embeddings_batch(
        self, 
        texts: List[str], 
        embeddings: List[List[float]]
    ):
        """Cache batch of embeddings"""
        if not settings.CACHE_ENABLED:
            return
        
        try:
            async with self.get_connection() as conn:
                pipe = conn.pipeline()
                
                for text, embedding in zip(texts, embeddings):
                    key = self._generate_key("embed", text[:500])
                    pipe.setex(
                        key,
                        settings.REDIS_TTL_EMBEDDINGS,
                        json.dumps(embedding)
                    )
                
                await pipe.execute()
        except Exception:
            pass
    
    # === Document Search Cache ===
    
    async def get_cached_search(self, query: str, top_k: int) -> Optional[List[dict]]:
        """Get cached document search results"""
        if not settings.CACHE_ENABLED:
            return None
        
        try:
            key = self._generate_key("search", f"{query}:{top_k}")
            async with self.get_connection() as conn:
                cached = await conn.get(key)
                if cached:
                    return json.loads(cached)
        except Exception:
            pass
        return None
    
    async def set_cached_search(self, query: str, top_k: int, results: List[dict]):
        """Cache document search results"""
        if not settings.CACHE_ENABLED:
            return
        
        try:
            key = self._generate_key("search", f"{query}:{top_k}")
            async with self.get_connection() as conn:
                await conn.setex(
                    key,
                    settings.REDIS_TTL_DOCUMENTS,
                    json.dumps(results, ensure_ascii=False)
                )
        except Exception:
            pass
    
    # === Cache Management ===
    
    async def clear_all(self):
        """Clear all cache"""
        try:
            async with self.get_connection() as conn:
                keys = await conn.keys("pdam:*")
                if keys:
                    await conn.delete(*keys)
        except Exception:
            pass
    
    async def clear_responses(self):
        """Clear response cache only"""
        try:
            async with self.get_connection() as conn:
                keys = await conn.keys("pdam:response:*")
                if keys:
                    await conn.delete(*keys)
        except Exception:
            pass
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            async with self.get_connection() as conn:
                info = await conn.info("stats")
                keys_response = await conn.keys("pdam:response:*")
                keys_embed = await conn.keys("pdam:embed:*")
                keys_search = await conn.keys("pdam:search:*")
                
                return {
                    "total_keys": await conn.dbsize(),
                    "response_cache": len(keys_response),
                    "embedding_cache": len(keys_embed),
                    "search_cache": len(keys_search),
                    "hits": info.get("keyspace_hits", 0),
                    "misses": info.get("keyspace_misses", 0),
                    "memory_used_mb": round(
                        (await conn.info("memory")).get("used_memory", 0) / 1024 / 1024, 2
                    )
                }
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
cache_service = CacheService()


async def get_cache() -> CacheService:
    """Get initialized cache service"""
    await cache_service.init()
    return cache_service
