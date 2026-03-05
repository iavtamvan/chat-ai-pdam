"""
Optimized Ollama LLM Service
- Connection pooling for faster requests
- GPU acceleration support
- Caching integration
- Streaming optimization
"""

import httpx
import json
import asyncio
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import hashlib

from app.core.config import settings, SYSTEM_PROMPT
from app.services.cache_service import get_cache


class OptimizedOllamaService:
    """High-performance LLM service with caching and GPU optimization"""
    
    _instance: Optional['OptimizedOllamaService'] = None
    _client: Optional[httpx.AsyncClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL
        
        # GPU and performance options
        self.model_options = {
            "temperature": settings.OLLAMA_TEMPERATURE,
            "top_p": settings.OLLAMA_TOP_P,
            "top_k": settings.OLLAMA_TOP_K,
            "repeat_penalty": settings.OLLAMA_REPEAT_PENALTY,
            "num_ctx": settings.OLLAMA_NUM_CTX,
            "num_gpu": settings.OLLAMA_NUM_GPU,  # GPU layers
            "num_thread": settings.OLLAMA_NUM_THREAD,
            "num_predict": 512,  # Max tokens to generate
            "stop": ["</s>", "[INST]", "[/INST]"],
        }
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=settings.OLLAMA_TIMEOUT,
                    write=10.0,
                    pool=5.0
                ),
                limits=httpx.Limits(
                    max_connections=settings.HTTP_POOL_SIZE,
                    max_keepalive_connections=settings.HTTP_POOL_MAXSIZE,
                    keepalive_expiry=30.0
                ),
                http2=True  # Enable HTTP/2 for better performance
            )
        return self._client
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Ollama health and GPU status"""
        try:
            client = await self.get_client()
            response = await client.get("/api/tags")
            
            if response.status_code != 200:
                return {"healthy": False, "error": "Server not responding"}
            
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            
            # Check GPU info
            gpu_info = await self._get_gpu_info()
            
            return {
                "healthy": True,
                "server": self.base_url,
                "models": models,
                "current_model": self.model,
                "embedding_model": self.embedding_model,
                "model_loaded": any(self.model in m for m in models),
                "gpu": gpu_info
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information from Ollama"""
        try:
            client = await self.get_client()
            # Ollama shows GPU info in the model details
            response = await client.post(
                "/api/show",
                json={"name": self.model}
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "available": True,
                    "layers_gpu": self.model_options.get("num_gpu", 0),
                    "model_family": data.get("details", {}).get("family", "unknown")
                }
        except:
            pass
        return {"available": False}
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        context: str = None,
        chat_history: List[Dict] = None,
        use_cache: bool = True,
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        """
        Generate response with caching
        Returns dict with answer, cached flag, and timing
        """
        
        start_time = datetime.now()
        
        # Build context hash for cache key
        context_hash = hashlib.md5(
            f"{context or ''}{str(chat_history or [])}".encode()
        ).hexdigest()[:8]
        
        # Check cache first
        if use_cache:
            cache = await get_cache()
            cached = await cache.get_cached_response(prompt, context_hash)
            if cached:
                return {
                    "answer": cached,
                    "cached": True,
                    "time_ms": 0,
                    "model": self.model
                }
        
        # Build messages
        full_system = system_prompt or SYSTEM_PROMPT
        if context:
            full_system += f"\n\nKonteks:\n{context}"
        
        messages = [{"role": "system", "content": full_system}]
        
        # Add recent history (limit to 6 for speed)
        if chat_history:
            for msg in chat_history[-6:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")[:500]  # Truncate long messages
                })
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            client = await self.get_client()
            
            response = await client.post(
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        **self.model_options,
                        "num_predict": max_tokens
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.status_code}")
            
            data = response.json()
            answer = data.get("message", {}).get("content", "").strip()
            
            # Calculate timing
            end_time = datetime.now()
            time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Cache the response
            if use_cache and answer:
                cache = await get_cache()
                await cache.set_cached_response(prompt, answer, context_hash)
            
            return {
                "answer": answer or "Maaf, tidak dapat memproses.",
                "cached": False,
                "time_ms": time_ms,
                "model": self.model,
                "eval_count": data.get("eval_count", 0),
                "eval_duration_ms": data.get("eval_duration", 0) // 1_000_000
            }
            
        except httpx.TimeoutException:
            return {
                "answer": "⏱️ Request timeout. Silakan coba lagi.",
                "cached": False,
                "time_ms": settings.OLLAMA_TIMEOUT * 1000,
                "error": "timeout"
            }
        except Exception as e:
            return {
                "answer": f"❌ Error: {str(e)}",
                "cached": False,
                "time_ms": 0,
                "error": str(e)
            }
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        context: str = None,
        chat_history: List[Dict] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens for real-time display"""
        
        full_system = system_prompt or SYSTEM_PROMPT
        if context:
            full_system += f"\n\nKonteks:\n{context}"
        
        messages = [{"role": "system", "content": full_system}]
        
        if chat_history:
            for msg in chat_history[-6:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")[:500]
                })
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            client = await self.get_client()
            
            async with client.stream(
                "POST",
                "/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": self.model_options
                },
                timeout=settings.OLLAMA_TIMEOUT
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n❌ Error: {str(e)}"
    
    async def get_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """Get embedding with caching"""
        
        # Check cache
        if use_cache:
            cache = await get_cache()
            cached = await cache.get_cached_embedding(text)
            if cached:
                return cached
        
        try:
            client = await self.get_client()
            
            response = await client.post(
                "/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text[:2000]  # Limit text length
                },
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Embedding error: {response.status_code}")
            
            data = response.json()
            embedding = data.get("embedding", [])
            
            # Cache embedding
            if use_cache and embedding:
                cache = await get_cache()
                await cache.set_cached_embedding(text, embedding)
            
            return embedding
            
        except Exception as e:
            print(f"Embedding error: {e}")
            return []
    
    async def get_embeddings_batch(
        self, 
        texts: List[str],
        use_cache: bool = True,
        batch_size: int = None
    ) -> List[List[float]]:
        """Get embeddings for multiple texts with parallel processing"""
        
        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        
        # Check cache for all texts
        if use_cache:
            cache = await get_cache()
            cached_results, missing_indices = await cache.get_cached_embeddings_batch(texts)
        else:
            cached_results = [None] * len(texts)
            missing_indices = list(range(len(texts)))
        
        # If all cached, return immediately
        if not missing_indices:
            return cached_results
        
        # Get missing embeddings
        missing_texts = [texts[i] for i in missing_indices]
        
        # Process in batches with concurrency
        new_embeddings = []
        
        if settings.EMBEDDING_PARALLEL:
            # Parallel processing
            tasks = [
                self.get_embedding(text, use_cache=False) 
                for text in missing_texts
            ]
            new_embeddings = await asyncio.gather(*tasks)
        else:
            # Sequential processing
            for text in missing_texts:
                emb = await self.get_embedding(text, use_cache=False)
                new_embeddings.append(emb)
        
        # Cache new embeddings
        if use_cache and new_embeddings:
            cache = await get_cache()
            await cache.set_cached_embeddings_batch(missing_texts, new_embeddings)
        
        # Merge results
        for idx, emb in zip(missing_indices, new_embeddings):
            cached_results[idx] = emb
        
        return cached_results
    
    async def warmup(self):
        """Warmup the model by running a simple inference"""
        try:
            await self.generate(
                "Halo",
                max_tokens=10,
                use_cache=False
            )
            print("✅ LLM warmup complete")
        except Exception as e:
            print(f"⚠️ LLM warmup failed: {e}")
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
_llm_service: Optional[OptimizedOllamaService] = None


def get_llm_service() -> OptimizedOllamaService:
    """Get LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = OptimizedOllamaService()
    return _llm_service

# Alias for backward compatibility
get_ollama_service = get_llm_service
