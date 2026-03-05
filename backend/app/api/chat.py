"""
Optimized Chat API Endpoints
With performance monitoring and caching
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import asyncio

from app.services.rag_service import get_rag_service
from app.services.llm_service import get_llm_service
from app.services.cache_service import get_cache
from app.api.auth import get_current_user_optional
from app.api.monitoring import record_response_time
from app.core.config import settings

router = APIRouter()


# === Models ===

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    chat_history: Optional[List[ChatMessage]] = []
    use_rag: bool = True
    use_cache: bool = True
    stream: bool = False
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    cached: bool = False
    time_ms: int
    rag_used: bool
    model: str
    timestamp: str


# === Endpoints ===

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Send message to AI chatbot
    
    Performance optimized with:
    - Redis response caching
    - Parallel document retrieval
    - Connection pooling
    """
    
    rag_service = get_rag_service()
    
    # Convert history
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in (request.chat_history or [])
    ]
    
    # Generate answer
    result = await rag_service.generate_answer(
        question=request.message,
        chat_history=history,
        use_rag=request.use_rag,
        use_cache=request.use_cache
    )
    
    # Record metrics
    record_response_time(
        result.get("time_ms", 0),
        result.get("cached", False),
        "chat"
    )
    
    return ChatResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        cached=result.get("cached", False),
        time_ms=result.get("time_ms", 0),
        rag_used=result.get("rag_used", False),
        model=result.get("model", settings.OLLAMA_MODEL),
        timestamp=datetime.now().isoformat()
    )


@router.post("/stream")
async def stream_message(
    request: ChatRequest,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Stream response for real-time display
    
    Returns Server-Sent Events (SSE)
    """
    
    start_time = datetime.now()
    rag_service = get_rag_service()
    
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in (request.chat_history or [])
    ]
    
    # Get streaming result
    result = await rag_service.generate_answer_stream(
        question=request.message,
        chat_history=history,
        use_rag=request.use_rag
    )
    
    async def event_generator():
        """Generate SSE events"""
        full_answer = ""
        
        # Send sources first
        yield f"data: {json.dumps({'type': 'sources', 'data': result['sources']})}\n\n"
        
        # Stream content
        try:
            async for chunk in result["stream"]:
                full_answer += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'data': chunk})}\n\n"
                await asyncio.sleep(0.005)  # Smooth streaming
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        
        # Calculate time
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Record metrics
        record_response_time(elapsed_ms, False, "stream")
        
        # Send completion
        yield f"data: {json.dumps({'type': 'done', 'data': {'time_ms': elapsed_ms, 'rag_used': result['rag_used']}})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/quick")
async def quick_answer(
    q: str = Query(..., min_length=1, max_length=500, description="Question"),
    rag: bool = Query(True, description="Use document retrieval")
):
    """
    Quick answer endpoint for simple queries
    
    Optimized for speed - no authentication required
    """
    
    rag_service = get_rag_service()
    
    result = await rag_service.generate_answer(
        question=q,
        use_rag=rag,
        use_cache=True
    )
    
    record_response_time(
        result.get("time_ms", 0),
        result.get("cached", False),
        "quick"
    )
    
    return {
        "question": q,
        "answer": result["answer"],
        "cached": result.get("cached", False),
        "time_ms": result.get("time_ms", 0)
    }


@router.get("/suggestions")
async def get_suggestions(
    context: Optional[str] = Query(None, description="Context for suggestions")
):
    """Get suggested questions"""
    
    # Check cache first
    cache = await get_cache()
    cache_key = f"suggestions:{context or 'default'}"
    
    try:
        cached = await cache._pool  # Quick check if cache available
    except:
        pass
    
    # Default suggestions (fast)
    default_suggestions = [
        "Bagaimana cara cek tagihan air?",
        "Apa syarat pemasangan baru?",
        "Cara lapor kebocoran pipa",
        "Dimana loket pembayaran terdekat?",
        "Berapa tarif air per kubik?"
    ]
    
    return {
        "suggestions": default_suggestions,
        "count": len(default_suggestions)
    }


@router.get("/models")
async def get_available_models():
    """Get available LLM models"""
    
    llm = get_llm_service()
    health = await llm.health_check()
    
    return {
        "current": settings.OLLAMA_MODEL,
        "embedding": settings.OLLAMA_EMBEDDING_MODEL,
        "available": health.get("models", []),
        "gpu_enabled": health.get("gpu", {}).get("available", False)
    }


@router.post("/preload")
async def preload_common_queries(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Preload common queries into cache for instant responses
    """
    
    common_queries = [
        "Bagaimana cara cek tagihan air PDAM?",
        "Apa syarat untuk pemasangan baru?",
        "Dimana lokasi loket pembayaran?",
        "Bagaimana cara melaporkan kebocoran?",
        "Berapa tarif air PDAM?",
        "Bagaimana cara balik nama pelanggan?",
        "Apa saja metode pembayaran tagihan?",
        "Bagaimana prosedur pengaduan?",
        "Kapan jadwal pembacaan meter?",
        "Berapa denda keterlambatan?"
    ]
    
    rag_service = get_rag_service()
    results = []
    
    for query in common_queries:
        try:
            result = await rag_service.generate_answer(
                question=query,
                use_rag=True,
                use_cache=True
            )
            results.append({
                "query": query,
                "cached": result.get("cached", False),
                "time_ms": result.get("time_ms", 0)
            })
        except Exception as e:
            results.append({
                "query": query,
                "error": str(e)
            })
    
    return {
        "preloaded": len(results),
        "results": results
    }
