"""
AI Provider Endpoints
Manage multiple AI providers (OpenAI, Gemini, DeepSeek, Claude, etc.)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional

from app.models.enterprise import (
    AIProvider, AIProviderCreate, AIProviderUpdate, AIProviderType
)
from app.services.ai_provider_service import get_ai_provider_service, DEFAULT_MODELS
from app.api.auth import get_current_user

router = APIRouter()


# ==========================================
# CRUD Endpoints
# ==========================================

@router.get("/", response_model=List[Dict])
async def list_ai_providers(
    active_only: bool = False,
    current_user: Dict = Depends(get_current_user)
):
    """List all AI providers"""
    service = get_ai_provider_service()
    
    if active_only:
        providers = service.get_active_providers()
    else:
        providers = service.get_all_providers()
    
    # Mask API keys
    result = []
    for p in providers:
        data = p.dict()
        if data.get("api_key"):
            data["api_key"] = data["api_key"][:8] + "..." + data["api_key"][-4:]
        result.append(data)
    
    return result


@router.get("/types")
async def list_provider_types():
    """List available provider types and their default models"""
    return {
        "types": [
            {
                "type": ptype.value,
                "name": ptype.value.title(),
                "models": [m.dict() for m in models],
                "requires_api_key": ptype != AIProviderType.OLLAMA
            }
            for ptype, models in DEFAULT_MODELS.items()
        ]
    }


@router.get("/{provider_id}")
async def get_ai_provider(
    provider_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get single AI provider"""
    service = get_ai_provider_service()
    provider = service.get_provider(provider_id)
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    data = provider.dict()
    if data.get("api_key"):
        data["api_key"] = data["api_key"][:8] + "..." + data["api_key"][-4:]
    
    return data


@router.post("/", response_model=Dict)
async def create_ai_provider(
    data: AIProviderCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create new AI provider"""
    service = get_ai_provider_service()
    provider = service.create_provider(data)
    
    result = provider.dict()
    if result.get("api_key"):
        result["api_key"] = result["api_key"][:8] + "..." + result["api_key"][-4:]
    
    return result


@router.put("/{provider_id}")
async def update_ai_provider(
    provider_id: str,
    data: AIProviderUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update AI provider"""
    service = get_ai_provider_service()
    provider = service.update_provider(provider_id, data)
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    result = provider.dict()
    if result.get("api_key"):
        result["api_key"] = result["api_key"][:8] + "..." + result["api_key"][-4:]
    
    return result


@router.delete("/{provider_id}")
async def delete_ai_provider(
    provider_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete AI provider"""
    service = get_ai_provider_service()
    success = service.delete_provider(provider_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"message": "Provider deleted"}


# ==========================================
# Status & Actions
# ==========================================

@router.post("/{provider_id}/toggle")
async def toggle_ai_provider(
    provider_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Toggle provider active status"""
    service = get_ai_provider_service()
    provider = service.toggle_provider(provider_id)
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {
        "message": f"Provider {'activated' if provider.is_active else 'deactivated'}",
        "is_active": provider.is_active
    }


@router.post("/{provider_id}/set-default")
async def set_default_provider(
    provider_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Set provider as default"""
    service = get_ai_provider_service()
    provider = service.set_default(provider_id)
    
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    return {"message": f"{provider.name} is now the default provider"}


@router.post("/{provider_id}/test")
async def test_ai_provider(
    provider_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Test AI provider connectivity"""
    service = get_ai_provider_service()
    result = await service.test_provider(provider_id)
    return result


# ==========================================
# Generation
# ==========================================

@router.post("/generate")
async def generate_with_provider(
    prompt: str,
    provider_id: Optional[str] = None,
    system_prompt: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Generate response using specified or default provider"""
    service = get_ai_provider_service()
    result = await service.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        provider_id=provider_id
    )
    return result


@router.post("/generate-with-fallback")
async def generate_with_fallback(
    prompt: str,
    system_prompt: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Generate with automatic fallback to other providers"""
    service = get_ai_provider_service()
    result = await service.generate_with_fallback(
        prompt=prompt,
        system_prompt=system_prompt
    )
    return result


# ==========================================
# Statistics
# ==========================================

@router.get("/stats/overview")
async def get_providers_stats(
    current_user: Dict = Depends(get_current_user)
):
    """Get AI providers statistics"""
    service = get_ai_provider_service()
    providers = service.get_all_providers()
    
    return {
        "total": len(providers),
        "active": sum(1 for p in providers if p.is_active),
        "total_requests": sum(p.total_requests for p in providers),
        "by_type": {
            ptype.value: sum(1 for p in providers if p.provider_type == ptype)
            for ptype in AIProviderType
        },
        "usage": [
            {
                "name": p.name,
                "type": p.provider_type.value,
                "requests": p.total_requests,
                "last_used": p.last_used_at
            }
            for p in sorted(providers, key=lambda x: x.total_requests, reverse=True)[:10]
        ]
    }


# ==========================================
# Quick Setup
# ==========================================

@router.post("/quick-setup")
async def quick_setup_provider(
    provider_type: AIProviderType,
    api_key: str,
    name: Optional[str] = None,
    set_as_default: bool = True,
    current_user: Dict = Depends(get_current_user)
):
    """Quick setup for a new provider"""
    service = get_ai_provider_service()
    
    # Get default model for this provider
    models = DEFAULT_MODELS.get(provider_type, [])
    default_model = models[0].id if models else None
    
    provider_data = AIProviderCreate(
        name=name or f"{provider_type.value.title()} Provider",
        provider_type=provider_type,
        api_key=api_key,
        default_model=default_model,
        is_active=True,
        is_default=set_as_default
    )
    
    provider = service.create_provider(provider_data)
    
    # Test the provider
    test_result = await service.test_provider(provider.id)
    
    result = provider.dict()
    result["api_key"] = result["api_key"][:8] + "..."
    result["test_result"] = test_result
    
    return result


# ==========================================
# Free API Keys Info
# ==========================================

@router.get("/free-options")
async def get_free_api_options():
    """Get information about free API options"""
    return {
        "free_options": [
            {
                "provider": "groq",
                "name": "Groq",
                "url": "https://console.groq.com/keys",
                "description": "Free tier dengan rate limit. Sangat cepat!",
                "free_tier": "14,400 requests/day",
                "models": ["llama-3.3-70b", "mixtral-8x7b", "gemma2-9b"],
                "recommended": True
            },
            {
                "provider": "gemini",
                "name": "Google Gemini",
                "url": "https://aistudio.google.com/app/apikey",
                "description": "15 RPM gratis untuk Gemini Pro",
                "free_tier": "15 requests/minute",
                "models": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash"],
                "recommended": True
            },
            {
                "provider": "openrouter",
                "name": "OpenRouter",
                "url": "https://openrouter.ai/keys",
                "description": "Akses ke banyak model, ada free tier",
                "free_tier": "Varies by model",
                "models": ["many free models available"],
                "recommended": True
            },
            {
                "provider": "deepseek",
                "name": "DeepSeek",
                "url": "https://platform.deepseek.com/api_keys",
                "description": "Murah banget, $1 = banyak request",
                "free_tier": "$5 credit for new users",
                "models": ["deepseek-chat", "deepseek-coder"],
                "recommended": True
            },
            {
                "provider": "ollama",
                "name": "Ollama (Local)",
                "url": "Already installed",
                "description": "100% gratis, jalan di lokal",
                "free_tier": "Unlimited",
                "models": ["llama3.2", "mistral", "qwen2.5"],
                "recommended": True
            },
            {
                "provider": "openai",
                "name": "OpenAI",
                "url": "https://platform.openai.com/api-keys",
                "description": "Bayar per penggunaan, tidak ada free tier",
                "free_tier": "No free tier (pay as you go)",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "recommended": False
            },
            {
                "provider": "claude",
                "name": "Anthropic Claude",
                "url": "https://console.anthropic.com/",
                "description": "Bayar per penggunaan",
                "free_tier": "$5 credit for new users",
                "models": ["claude-3.5-sonnet", "claude-3-haiku"],
                "recommended": False
            }
        ],
        "recommendation": "Untuk testing gratis, gunakan Groq atau Gemini. Keduanya cepat dan punya free tier yang cukup besar."
    }
