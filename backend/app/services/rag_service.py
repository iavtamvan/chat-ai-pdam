"""
Optimized RAG Service
- Parallel document retrieval
- Caching at every level
- Optimized context building
- Document indexing for training
"""

import asyncio
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings, RAG_PROMPT_TEMPLATE
from app.services.llm_service import get_llm_service
from app.services.cache_service import get_cache
from app.core.database import query_documents, add_documents, get_document_count


class OptimizedRAGService:
    """High-performance RAG with multi-level caching"""

    def __init__(self):
        self.llm = get_llm_service()

    # =============================================
    # NEW: Methods for training/retraining
    # =============================================

    async def index_document(self, doc: Dict[str, Any]) -> bool:
        """Index a single document chunk into vector database"""
        try:
            doc_id = doc.get("id", hashlib.md5(doc.get("content", "").encode()).hexdigest()[:16])
            content = doc.get("content", "")

            if not content:
                return False

            # Generate embedding
            embedding = await self.llm.get_embedding(content)
            if not embedding:
                print(f"⚠️ Failed to generate embedding for {doc_id}")
                return False

            # Prepare metadata
            metadata = {
                "filename": doc.get("title") or doc.get("source") or "unknown",
                "source": doc.get("source", "uploaded"),
                "indexed_at": datetime.now().isoformat(),
                "chunk_index": doc.get("chunk_index", 0)
            }

            # Add to vector database
            success = await add_documents(
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )

            if success:
                print(f"✅ Indexed: {doc_id}")

            return success

        except Exception as e:
            print(f"❌ Error indexing document: {e}")
            return False

    async def index_documents_batch(self, docs: List[Dict[str, Any]]) -> int:
        """Index multiple document chunks (more efficient)"""
        if not docs:
            return 0

        try:
            contents = []
            ids = []
            metadatas = []

            for doc in docs:
                content = doc.get("content", "")
                if not content:
                    continue

                doc_id = doc.get("id", hashlib.md5(content.encode()).hexdigest()[:16])

                contents.append(content)
                ids.append(doc_id)
                metadatas.append({
                    "filename": doc.get("title") or doc.get("source") or "unknown",
                    "source": doc.get("source", "uploaded"),
                    "indexed_at": datetime.now().isoformat(),
                    "chunk_index": doc.get("chunk_index", 0)
                })

            if not contents:
                return 0

            # Generate embeddings in batch (or one by one if batch not available)
            print(f"📊 Generating embeddings for {len(contents)} chunks...")

            embeddings = []
            if hasattr(self.llm, 'get_embeddings_batch'):
                embeddings = await self.llm.get_embeddings_batch(contents)
            else:
                # Fallback: generate one by one
                for i, content in enumerate(contents):
                    emb = await self.llm.get_embedding(content)
                    if emb:
                        embeddings.append(emb)
                    else:
                        print(f"⚠️ Failed embedding for chunk {i}")
                        embeddings.append(None)

            # Filter out failed embeddings
            valid_data = [(c, e, m, i) for c, e, m, i in zip(contents, embeddings, metadatas, ids) if e is not None]
            if not valid_data:
                print("⚠️ No valid embeddings generated")
                return 0

            contents, embeddings, metadatas, ids = zip(*valid_data)
            contents, embeddings, metadatas, ids = list(contents), list(embeddings), list(metadatas), list(ids)

            # Add to vector database
            success = await add_documents(
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            if success:
                print(f"✅ Indexed {len(contents)} chunks")
                return len(contents)

            return 0

        except Exception as e:
            print(f"❌ Error batch indexing: {e}")
            return 0

    # =============================================
    # EXISTING: Search and generate methods
    # =============================================

    async def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search documents - alias for search_documents"""
        return await self.search_documents(query, top_k)

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
            try:
                cache = await get_cache()
                cached = await cache.get_cached_search(query, top_k)
                if cached:
                    return cached
            except:
                pass

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
                    "similarity": round(similarity, 4),
                    "title": meta.get("filename", "Unknown"),
                    "score": round(similarity, 4)
                })

        # Cache results
        if use_cache and similar_docs:
            try:
                cache = await get_cache()
                await cache.set_cached_search(query, top_k, similar_docs)
            except:
                pass

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
            try:
                cache = await get_cache()
                cached_response = await cache.get_cached_response(question, history_hash)
                if cached_response:
                    if search_task:
                        try:
                            sources_docs = await asyncio.wait_for(search_task, timeout=1.0)
                            sources = [
                                {
                                    "filename": d["metadata"].get("filename"),
                                    "similarity": d["similarity"],
                                    "snippet": d.get("content", "")[:100] + "..."
                                }
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
            except:
                pass

        # Wait for document search
        if search_task:
            similar_docs = await search_task
            if similar_docs:
                context = self._build_context(similar_docs)
                sources = [
                    {
                        "filename": d["metadata"].get("filename"),
                        "similarity": d["similarity"],
                        "snippet": d.get("content", "")[:100] + "..."
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
                    {
                        "filename": d["metadata"].get("filename"),
                        "similarity": d["similarity"],
                        "snippet": d.get("content", "")[:100] + "..."
                    }
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