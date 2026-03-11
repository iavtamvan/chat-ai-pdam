"""
Embed Token Endpoints
Manage tokens for widget embedding and WhatsApp integration
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.models.enterprise import (
    EmbedToken, EmbedTokenCreate, EmbedTokenUpdate,
    TokenScope, TokenStatus
)
from app.services.embed_token_service import get_embed_token_service
from app.api.auth import get_current_user

router = APIRouter()


# ==========================================
# CRUD Endpoints
# ==========================================

@router.get("/", response_model=List[Dict])
async def list_embed_tokens(
    status: Optional[TokenStatus] = None,
    scope: Optional[TokenScope] = None,
    integration_type: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """List all embed tokens"""
    service = get_embed_token_service()
    tokens = service.get_all_tokens()
    
    if status:
        tokens = [t for t in tokens if t.status == status]
    
    if scope:
        tokens = [t for t in tokens if t.scope == scope]
    
    if integration_type:
        tokens = [t for t in tokens if t.integration_type == integration_type]
    
    # Mask token values for security
    result = []
    for t in tokens:
        data = t.dict()
        data["token_masked"] = data["token"][:12] + "..." + data["token"][-6:]
        result.append(data)
    
    return result


@router.get("/{token_id}")
async def get_embed_token(
    token_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get single embed token"""
    service = get_embed_token_service()
    token = service.get_token_by_id(token_id)
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return token.dict()


@router.post("/", response_model=Dict)
async def create_embed_token(
    data: EmbedTokenCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create new embed token"""
    service = get_embed_token_service()
    token = service.create_token(data, created_by=current_user.get("npp"))
    return token.dict()


@router.put("/{token_id}")
async def update_embed_token(
    token_id: str,
    data: EmbedTokenUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update embed token"""
    service = get_embed_token_service()
    token = service.update_token(token_id, data)
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return token.dict()


@router.delete("/{token_id}")
async def delete_embed_token(
    token_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete embed token"""
    service = get_embed_token_service()
    success = service.delete_token(token_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return {"message": "Token deleted"}


# ==========================================
# Token Actions
# ==========================================

@router.post("/{token_id}/activate")
async def activate_token(
    token_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Activate token"""
    service = get_embed_token_service()
    token = service.activate_token(token_id)
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return {"message": "Token activated", "status": token.status.value}


@router.post("/{token_id}/deactivate")
async def deactivate_token(
    token_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Deactivate token"""
    service = get_embed_token_service()
    token = service.deactivate_token(token_id)
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return {"message": "Token deactivated", "status": token.status.value}


@router.post("/{token_id}/revoke")
async def revoke_token(
    token_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Revoke token permanently"""
    service = get_embed_token_service()
    token = service.revoke_token(token_id)
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return {"message": "Token revoked", "status": token.status.value}


@router.post("/{token_id}/regenerate")
async def regenerate_token(
    token_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Regenerate token value"""
    service = get_embed_token_service()
    token = service.regenerate_token_value(token_id)
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return {
        "message": "Token regenerated",
        "new_token": token.token
    }


# ==========================================
# Embed Code Generation
# ==========================================

@router.get("/{token_id}/widget-code")
async def get_widget_code(
    token_id: str,
    api_base_url: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get widget embed code for token"""
    service = get_embed_token_service()
    code = service.generate_widget_code(token_id, api_base_url)
    
    return {
        "html_code": code,
        "usage": "Copy and paste this code before </body> tag in your website"
    }


@router.get("/{token_id}/whatsapp-config")
async def get_whatsapp_config(
    token_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get WhatsApp bot configuration"""
    service = get_embed_token_service()
    token = service.get_token_by_id(token_id)
    
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    return {
        "token": token.token,
        "webhook_url": token.webhook_url,
        "scope": token.scope.value,
        "env_config": f"""
# WhatsApp Bot Configuration
PDAM_CHATBOT_TOKEN={token.token}
PDAM_CHATBOT_API_URL=http://localhost:8000
PDAM_CHATBOT_SCOPE={token.scope.value}
WEBHOOK_URL={token.webhook_url or 'http://localhost:3001/webhook'}
"""
    }


# ==========================================
# Token Validation (Public)
# ==========================================

@router.post("/validate")
async def validate_token(
    request: Request,
    token: str
):
    """Validate embed token (public endpoint)"""
    service = get_embed_token_service()
    
    # Get domain and IP from request
    domain = request.headers.get("origin", "").replace("http://", "").replace("https://", "").split("/")[0]
    ip_address = request.client.host if request.client else None
    
    result = service.validate_token(
        token_value=token,
        domain=domain,
        ip_address=ip_address
    )
    
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=result.get("error", "Invalid token"))
    
    return {
        "valid": True,
        "scope": result["scope"],
        "requires_login": result["scope"] == TokenScope.INTERNAL.value
    }


# ==========================================
# Statistics
# ==========================================

@router.get("/stats/overview")
async def get_token_stats(
    current_user: Dict = Depends(get_current_user)
):
    """Get embed tokens statistics"""
    service = get_embed_token_service()
    return service.get_all_stats()


@router.get("/{token_id}/stats")
async def get_single_token_stats(
    token_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get statistics for single token"""
    service = get_embed_token_service()
    stats = service.get_token_stats(token_id)
    
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    
    return stats


# ==========================================
# Quick Create
# ==========================================

@router.post("/quick-create/widget")
async def quick_create_widget_token(
    name: str,
    domains: List[str] = ["*"],
    expires_days: Optional[int] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Quick create token for website widget"""
    service = get_embed_token_service()
    
    token_data = EmbedTokenCreate(
        name=name,
        description=f"Widget token for {name}",
        scope=TokenScope.EXTERNAL,
        allowed_domains=domains,
        integration_type="widget",
        expires_at=datetime.now() + timedelta(days=expires_days) if expires_days else None
    )
    
    token = service.create_token(token_data, created_by=current_user.get("npp"))
    
    return {
        "token": token.dict(),
        "widget_code": service.generate_widget_code(token.id)
    }


@router.post("/quick-create/whatsapp")
async def quick_create_whatsapp_token(
    name: str,
    webhook_url: Optional[str] = None,
    scope: TokenScope = TokenScope.BOTH,
    current_user: Dict = Depends(get_current_user)
):
    """Quick create token for WhatsApp bot"""
    service = get_embed_token_service()
    
    token_data = EmbedTokenCreate(
        name=name,
        description=f"WhatsApp bot token for {name}",
        scope=scope,
        integration_type="whatsapp",
        webhook_url=webhook_url,
        rate_limit=60,  # Lower rate limit for WhatsApp
        daily_limit=5000
    )
    
    token = service.create_token(token_data, created_by=current_user.get("npp"))
    
    return {
        "token": token.dict(),
        "bot_config": {
            "token": token.token,
            "webhook_url": token.webhook_url,
            "scope": token.scope.value
        }
    }


@router.post("/quick-create/internal")
async def quick_create_internal_token(
    name: str,
    expires_days: int = 365,
    current_user: Dict = Depends(get_current_user)
):
    """Quick create token for internal use (requires PDAM login)"""
    service = get_embed_token_service()
    
    token_data = EmbedTokenCreate(
        name=name,
        description=f"Internal token for {name}",
        scope=TokenScope.INTERNAL,
        integration_type="api",
        expires_at=datetime.now() + timedelta(days=expires_days),
        daily_limit=50000  # Higher limit for internal
    )
    
    token = service.create_token(token_data, created_by=current_user.get("npp"))
    
    return {
        "token": token.dict(),
        "usage_note": "This token requires PDAM authentication to use"
    }
