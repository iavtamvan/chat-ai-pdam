"""
Chat API with Multi-Provider AI Support + API Integration
FINAL VERSION
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import asyncio

from app.api.auth import get_current_user_optional, get_current_user
from app.services.rag_service import get_rag_service
from app.services.llm_service import get_llm_service

# Try to import AI Provider Service (Enterprise feature)
try:
    from app.services.ai_provider_service import get_ai_provider_service
    HAS_ENTERPRISE = True
    print("✅ Enterprise AI Provider Service loaded")
except ImportError as e:
    HAS_ENTERPRISE = False
    print(f"⚠️ Enterprise AI Provider not available: {e}")

# Try to import API Integration Service
try:
    from app.services.api_integration_service import get_api_integration_service
    HAS_API_INTEGRATION = True
    print("✅ API Integration Service loaded")
except ImportError as e:
    HAS_API_INTEGRATION = False
    print(f"⚠️ API Integration not available: {e}")

router = APIRouter()


# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    chat_history: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None
    use_rag: bool = True
    stream: bool = False
    provider_id: Optional[str] = None
    use_fallback: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []
    cached: bool = False
    time_ms: int = 0
    rag_used: bool = False
    model: Optional[str] = None
    provider: Optional[str] = None
    api_used: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ============================================
# SYSTEM PROMPT
# ============================================

SYSTEM_PROMPT = """Kamu adalah asisten resmi AI untuk PDAM Tirta Moedal Kota Semarang yang tau segalanya. 
Tugas kamu adalah membantu menjawab pertanyaan seputar layanan PDAM dengan ramah dan informatif.

Panduan menjawab:
- Gunakan bahasa Indonesia yang baik dan sopan
- Jika ada informasi dari dokumen atau sistem, gunakan itu sebagai referensi utama
- Jika tidak tahu jawabannya, akui dengan jujur dan sarankan menghubungi customer service
- Cari informasi yang relevan dan terbaru kemudian berikan dengan jelas
- Berikan jawaban yang ringkas namun lengkap
- Untuk pertanyaan teknis, berikan langkah-langkah yang jelas
- Jika ada data tagihan atau informasi pelanggan, tampilkan dengan format yang rapi

Informasi kontak PDAM:
- Call Center: 024-8311911
- WhatsApp: 0811-2900-911
- Website: www.pdamkotasmg.co.id
- Alamat: Jl. Kelud Raya No.60, Semarang"""


# ============================================
# HELPER FUNCTIONS
# ============================================

async def generate_with_enterprise(
        prompt: str,
        system_prompt: str,
        chat_history: List[Dict] = None,
        provider_id: str = None,
        use_fallback: bool = True
) -> Dict[str, Any]:
    """Generate response using Enterprise AI Provider Service"""
    service = get_ai_provider_service()

    if use_fallback and not provider_id:
        result = await service.generate_with_fallback(
            prompt=prompt,
            system_prompt=system_prompt,
            chat_history=chat_history
        )
    else:
        result = await service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            chat_history=chat_history,
            provider_id=provider_id
        )

    return result


async def generate_with_ollama(
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None
) -> Dict[str, Any]:
    """Generate using basic Ollama LLM service"""
    llm = get_llm_service()

    try:
        start_time = datetime.now()
        response = await llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            chat_history=chat_history
        )
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "success": True,
            "answer": response,
            "provider": "ollama-local",
            "model": "llama3.2:3b",
            "time_ms": elapsed_ms
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": "ollama-local"
        }


# ============================================
# CHAT ENDPOINT
# ============================================

@router.post("/send", response_model=ChatResponse)
async def send_message(
        request: ChatRequest,
        background_tasks: BackgroundTasks,
        current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Send chat message and get AI response"""
    start_time = datetime.now()

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    print(f"\n{'='*50}")
    print(f"📨 New message: {message}")
    print(f"HAS_API_INTEGRATION: {HAS_API_INTEGRATION}")
    print(f"{'='*50}")

    # =====================================
    # 0. Check API Integration FIRST
    # =====================================
    api_response = None
    api_used = None

    if HAS_API_INTEGRATION:
        try:
            print("🔍 Checking API Integration...")
            api_service = get_api_integration_service()
            api_result = await api_service.process_message(message)

            print(f"📋 API Result: {api_result}")

            if api_result:
                if api_result.get("success"):
                    # API call succeeded!
                    api_response = api_result.get("formatted", "")
                    api_used = api_result.get("api_name")
                    print(f"✅ API Integration SUCCESS: {api_used}")
                    print(f"📄 Response: {api_response[:200]}...")

                elif api_result.get("needs_param"):
                    # Need more info from user - return immediately
                    print(f"⚠️ API needs more params")
                    return ChatResponse(
                        answer=api_result.get("message", "Mohon sertakan nomor pelanggan Anda."),
                        sources=[],
                        cached=False,
                        time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                        rag_used=False,
                        model=None,
                        provider="api-integration",
                        api_used=api_result.get("api_name")
                    )
                else:
                    print(f"❌ API call failed: {api_result.get('error')}")
        except Exception as e:
            print(f"❌ API Integration error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ API Integration not available")

    # =====================================
    # 1. RAG Search (if enabled and no API response)
    # =====================================
    context = ""
    sources = []
    rag_used = False

    if request.use_rag and not api_response:
        try:
            rag = get_rag_service()
            rag_results = await rag.search(message, top_k=3)

            if rag_results:
                rag_used = True
                context_parts = []

                for i, result in enumerate(rag_results):
                    context_parts.append(f"[Dokumen {i+1}]: {result.get('content', '')}")
                    sources.append({
                        "title": result.get("title", f"Dokumen {i+1}"),
                        "score": result.get("score", 0),
                        "snippet": result.get("content", "")[:200] + "..."
                    })

                context = "\n\n".join(context_parts)
        except Exception as e:
            print(f"⚠️ RAG search error: {e}")

    # =====================================
    # 2. Build prompt
    # =====================================

    # If API response exists, use it as primary context
    if api_response:
        full_prompt = f"""Data dari sistem PDAM:

{api_response}

Pertanyaan pengguna: {message}

Berikan jawaban berdasarkan data di atas. Format dengan rapi dan mudah dibaca. Jangan bilang kamu tidak bisa mengakses data karena data sudah tersedia di atas."""
    elif context:
        full_prompt = f"""Berdasarkan informasi berikut:

{context}

Pertanyaan pengguna: {message}

Berikan jawaban yang informatif berdasarkan dokumen di atas."""
    else:
        full_prompt = message

    # =====================================
    # 3. Generate AI Response
    # =====================================
    answer = ""
    model_used = None
    provider_used = None

    if HAS_ENTERPRISE:
        result = await generate_with_enterprise(
            prompt=full_prompt,
            system_prompt=SYSTEM_PROMPT,
            chat_history=request.chat_history,
            provider_id=request.provider_id,
            use_fallback=request.use_fallback
        )

        if result.get("success"):
            answer = result.get("answer", "")
            model_used = result.get("model")
            provider_used = result.get("provider")
        else:
            print(f"⚠️ Enterprise AI failed: {result.get('error')}, falling back to Ollama")
            ollama_result = await generate_with_ollama(
                prompt=full_prompt,
                system_prompt=SYSTEM_PROMPT,
                chat_history=request.chat_history
            )
            if ollama_result.get("success"):
                answer = ollama_result.get("answer", "")
                model_used = ollama_result.get("model")
                provider_used = ollama_result.get("provider")
            else:
                raise HTTPException(
                    status_code=503,
                    detail=f"All AI providers failed. Last error: {result.get('error')}"
                )
    else:
        result = await generate_with_ollama(
            prompt=full_prompt,
            system_prompt=SYSTEM_PROMPT,
            chat_history=request.chat_history
        )

        if result.get("success"):
            answer = result.get("answer", "")
            model_used = result.get("model")
            provider_used = result.get("provider")
        else:
            raise HTTPException(
                status_code=503,
                detail=f"AI service unavailable: {result.get('error')}"
            )

    # =====================================
    # 4. Build response
    # =====================================
    elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

    print(f"\n✅ Response ready:")
    print(f"   - API Used: {api_used}")
    print(f"   - Provider: {provider_used}")
    print(f"   - Time: {elapsed_ms}ms")

    return ChatResponse(
        answer=answer,
        sources=sources,
        cached=False,
        time_ms=elapsed_ms,
        rag_used=rag_used,
        model=model_used,
        provider=provider_used,
        api_used=api_used,
        timestamp=datetime.now().isoformat()
    )


# ============================================
# STREAMING ENDPOINT
# ============================================

@router.post("/stream")
async def stream_message(
        request: ChatRequest,
        current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Stream chat response"""
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check API Integration first
    api_context = ""
    if HAS_API_INTEGRATION:
        try:
            api_service = get_api_integration_service()
            api_result = await api_service.process_message(message)
            if api_result and api_result.get("success"):
                api_context = f"Data dari sistem PDAM:\n{api_result.get('formatted', '')}\n\n"
        except Exception as e:
            print(f"⚠️ API Integration error: {e}")

    # RAG search
    rag_context = ""
    if request.use_rag and not api_context:
        try:
            rag = get_rag_service()
            rag_results = await rag.search(message, top_k=3)
            if rag_results:
                context_parts = [f"[Doc {i+1}]: {r.get('content', '')}" for i, r in enumerate(rag_results)]
                rag_context = "\n\n".join(context_parts)
        except Exception as e:
            print(f"⚠️ RAG error: {e}")

    # Build prompt
    full_context = api_context + rag_context
    if full_context:
        full_prompt = f"Berdasarkan informasi:\n{full_context}\n\nPertanyaan: {message}"
    else:
        full_prompt = message

    async def generate():
        try:
            if HAS_ENTERPRISE:
                service = get_ai_provider_service()
                async for chunk in service.generate_stream(
                        prompt=full_prompt,
                        system_prompt=SYSTEM_PROMPT,
                        chat_history=request.chat_history,
                        provider_id=request.provider_id
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            else:
                llm = get_llm_service()
                async for chunk in llm.generate_stream(
                        prompt=full_prompt,
                        system_prompt=SYSTEM_PROMPT,
                        chat_history=request.chat_history
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================
# UTILITY ENDPOINTS
# ============================================

@router.get("/providers")
async def get_available_providers():
    """Get list of available AI providers"""
    if not HAS_ENTERPRISE:
        return {
            "enterprise": False,
            "providers": [{
                "id": "ollama-local",
                "name": "Ollama (Local)",
                "type": "ollama",
                "is_default": True,
                "is_active": True
            }]
        }

    service = get_ai_provider_service()
    providers = service.get_active_providers()

    return {
        "enterprise": True,
        "providers": [{
            "id": p.id,
            "name": p.name,
            "type": p.provider_type.value,
            "model": p.default_model,
            "is_default": p.is_default,
            "is_active": p.is_active
        } for p in providers]
    }


@router.get("/status")
async def get_chat_status():
    """Get chat service status"""
    return {
        "enterprise_ai": HAS_ENTERPRISE,
        "api_integration": HAS_API_INTEGRATION,
        "message": "Chat service ready"
    }