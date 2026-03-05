"""
Optimized RAG Service
- Parallel document retrieval
- Caching at every level
- Optimized context building
"""

import asyncio
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings, RAG_PROMPT_TEMPLATE
from app.services.llm_service import get_llm_service
from app.services.cache_service import get_cache
from app.core.database import query_documents


class OptimizedRAGService:
    """High-performance RAG with multi-level caching"""
    
    def __init__(self):
        self.llm = get_llm_service()
    
    async def search_documents(
        self, 
        query: str, 
        top_k: int = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Search documents with caching"""
        
        top_k = top_k or settings.TOP_K_RESULTS
        
        # Check cache
        if use_cache:
            cache = await get_cache()
            cached = await cache.get_cached_search(query, top_k)
            if cached:
                return cached
        
        # Get query embedding
        query_embedding = await self.llm.get_embedding(query)
        
        if not query_embedding:
            return []
        
        # Query vector database
        results = await query_documents(
            query_embedding=query_embedding,
            n_results=top_k
        )
        
        # Format results
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        similar_docs = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            similarity = 1 - dist
            if similarity >= settings.SIMILARITY_THRESHOLD:
                similar_docs.append({
                    "content": doc,
                    "metadata": meta,
                    "similarity": round(similarity, 4)
                })
        
        # Cache results
        if use_cache and similar_docs:
            cache = await get_cache()
            await cache.set_cached_search(query, top_k, similar_docs)
        
        return similar_docs
    
    def _build_context(self, documents: List[Dict], max_length: int = 2000) -> str:
        """Build optimized context string"""
        if not documents:
            return ""
        
        context_parts = []
        total_length = 0
        
        for doc in documents:
            content = doc.get("content", "")[:500]  # Limit per doc
            if total_length + len(content) > max_length:
                break
            context_parts.append(content)
            total_length += len(content)
        
        return "\n---\n".join(context_parts)
    
    async def generate_answer(
        self,
        question: str,
        chat_history: List[Dict] = None,
        use_rag: bool = True,
        use_cache: bool = True,
        top_k: int = None
    ) -> Dict[str, Any]:
        """Generate answer with full optimization"""
        
        start_time = datetime.now()
        sources = []
        context = ""
        
        # Parallel: search documents while preparing
        search_task = None
        if use_rag:
            search_task = asyncio.create_task(
                self.search_documents(question, top_k or settings.TOP_K_RESULTS)
            )
        
        # Build context hash for response caching
        history_hash = hashlib.md5(
            str(chat_history or []).encode()
        ).hexdigest()[:8]
        
        # Check response cache
        if use_cache:
            cache = await get_cache()
            cached_response = await cache.get_cached_response(question, history_hash)
            if cached_response:
                # Still get sources for display if available
                if search_task:
                    try:
                        sources_docs = await asyncio.wait_for(search_task, timeout=1.0)
                        sources = [
                            {"filename": d["metadata"].get("filename"), "similarity": d["similarity"]}
                            for d in sources_docs[:3]
                        ]
                    except asyncio.TimeoutError:
                        pass
                
                return {
                    "answer": cached_response,
                    "sources": sources,
                    "cached": True,
                    "time_ms": 0,
                    "rag_used": use_rag
                }
        
        # Wait for document search
        if search_task:
            similar_docs = await search_task
            if similar_docs:
                context = self._build_context(similar_docs)
                sources = [
                    {
                        "filename": d["metadata"].get("filename"),
                        "similarity": d["similarity"]
                    }
                    for d in similar_docs[:3]
                ]
        
        # Generate with LLM
        result = await self.llm.generate(
            prompt=question,
            context=context if use_rag else None,
            chat_history=chat_history,
            use_cache=use_cache
        )
        
        # Calculate total time
        end_time = datetime.now()
        total_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            "answer": result["answer"],
            "sources": sources,
            "cached": result.get("cached", False),
            "time_ms": total_time_ms,
            "llm_time_ms": result.get("time_ms", 0),
            "rag_used": use_rag and bool(sources),
            "model": result.get("model", settings.OLLAMA_MODEL)
        }
    
    async def generate_answer_stream(
        self,
        question: str,
        chat_history: List[Dict] = None,
        use_rag: bool = True
    ):
        """Stream answer generation"""
        
        # Search documents first
        sources = []
        context = ""
        
        if use_rag:
            similar_docs = await self.search_documents(question)
            if similar_docs:
                context = self._build_context(similar_docs)
                sources = [
                    {"filename": d["metadata"].get("filename"), "similarity": d["similarity"]}
                    for d in similar_docs[:3]
                ]
        
        # Return sources and stream
        return {
            "sources": sources,
            "stream": self.llm.generate_stream(
                prompt=question,
                context=context if use_rag else None,
                chat_history=chat_history
            ),
            "rag_used": use_rag and bool(sources)
        }


# Singleton
_rag_service: Optional[OptimizedRAGService] = None


def get_rag_service() -> OptimizedRAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = OptimizedRAGService()
    return _rag_service
