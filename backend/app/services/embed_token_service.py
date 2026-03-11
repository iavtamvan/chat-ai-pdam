"""
Embed Token Service
Manage tokens for Widget embedding and WhatsApp integration
"""

import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.models.enterprise import (
    EmbedToken, EmbedTokenCreate, EmbedTokenUpdate,
    TokenScope, TokenStatus,
    load_data, save_data, EMBED_TOKENS_FILE
)


class EmbedTokenService:
    """Service for managing embed tokens"""
    
    # ==========================================
    # CRUD Operations
    # ==========================================
    
    def get_all_tokens(self) -> List[EmbedToken]:
        """Get all embed tokens"""
        data = load_data(EMBED_TOKENS_FILE)
        return [EmbedToken(**item) for item in data]
    
    def get_token_by_id(self, token_id: str) -> Optional[EmbedToken]:
        """Get token by ID"""
        for token in self.get_all_tokens():
            if token.id == token_id:
                return token
        return None
    
    def get_token_by_value(self, token_value: str) -> Optional[EmbedToken]:
        """Get token by token value"""
        for token in self.get_all_tokens():
            if token.token == token_value:
                return token
        return None
    
    def get_active_tokens(self) -> List[EmbedToken]:
        """Get only active tokens"""
        return [t for t in self.get_all_tokens() if t.status == TokenStatus.ACTIVE]
    
    def create_token(self, data: EmbedTokenCreate, created_by: str = None) -> EmbedToken:
        """Create new embed token"""
        token = EmbedToken(
            **data.dict(),
            token=f"pdam_{secrets.token_hex(24)}",
            created_at=datetime.now(),
            created_by=created_by
        )
        
        tokens = self.get_all_tokens()
        tokens.append(token)
        save_data(EMBED_TOKENS_FILE, [t.dict() for t in tokens])
        
        return token
    
    def update_token(self, token_id: str, data: EmbedTokenUpdate) -> Optional[EmbedToken]:
        """Update existing token"""
        tokens = self.get_all_tokens()
        
        for i, t in enumerate(tokens):
            if t.id == token_id:
                update_data = data.dict(exclude_unset=True)
                
                for key, value in update_data.items():
                    setattr(t, key, value)
                
                tokens[i] = t
                save_data(EMBED_TOKENS_FILE, [tk.dict() for tk in tokens])
                return t
        
        return None
    
    def delete_token(self, token_id: str) -> bool:
        """Delete token"""
        tokens = self.get_all_tokens()
        original_count = len(tokens)
        
        tokens = [t for t in tokens if t.id != token_id]
        
        if len(tokens) < original_count:
            save_data(EMBED_TOKENS_FILE, [t.dict() for t in tokens])
            return True
        return False
    
    def revoke_token(self, token_id: str) -> Optional[EmbedToken]:
        """Revoke token"""
        return self.update_token(token_id, EmbedTokenUpdate(status=TokenStatus.REVOKED))
    
    def activate_token(self, token_id: str) -> Optional[EmbedToken]:
        """Activate token"""
        return self.update_token(token_id, EmbedTokenUpdate(status=TokenStatus.ACTIVE))
    
    def deactivate_token(self, token_id: str) -> Optional[EmbedToken]:
        """Deactivate token"""
        return self.update_token(token_id, EmbedTokenUpdate(status=TokenStatus.INACTIVE))
    
    def regenerate_token_value(self, token_id: str) -> Optional[EmbedToken]:
        """Regenerate token value"""
        tokens = self.get_all_tokens()
        
        for i, t in enumerate(tokens):
            if t.id == token_id:
                t.token = f"pdam_{secrets.token_hex(24)}"
                tokens[i] = t
                save_data(EMBED_TOKENS_FILE, [tk.dict() for tk in tokens])
                return t
        
        return None
    
    # ==========================================
    # Token Validation
    # ==========================================
    
    def validate_token(
        self, 
        token_value: str,
        domain: str = None,
        ip_address: str = None,
        require_internal: bool = False
    ) -> Dict[str, Any]:
        """Validate token for access"""
        
        token = self.get_token_by_value(token_value)
        
        if not token:
            return {
                "valid": False,
                "error": "Token not found"
            }
        
        # Check status
        if token.status != TokenStatus.ACTIVE:
            return {
                "valid": False,
                "error": f"Token is {token.status.value}"
            }
        
        # Check expiration
        if token.expires_at and datetime.now() > token.expires_at:
            # Auto-update status
            self.update_token(token.id, EmbedTokenUpdate(status=TokenStatus.EXPIRED))
            return {
                "valid": False,
                "error": "Token has expired"
            }
        
        # Check scope for internal access
        if require_internal and token.scope == TokenScope.EXTERNAL:
            return {
                "valid": False,
                "error": "Token does not have internal access"
            }
        
        # Check domain
        if domain and "*" not in token.allowed_domains:
            if not any(self._match_domain(domain, allowed) for allowed in token.allowed_domains):
                return {
                    "valid": False,
                    "error": "Domain not allowed"
                }
        
        # Check IP
        if ip_address and "*" not in token.allowed_ips:
            if ip_address not in token.allowed_ips:
                return {
                    "valid": False,
                    "error": "IP address not allowed"
                }
        
        # Update usage
        self._update_usage(token.id)
        
        return {
            "valid": True,
            "token": token,
            "scope": token.scope.value,
            "ai_provider_id": token.ai_provider_id
        }
    
    def _match_domain(self, domain: str, pattern: str) -> bool:
        """Check if domain matches pattern (supports wildcards)"""
        if pattern.startswith("*."):
            # Wildcard subdomain
            base = pattern[2:]
            return domain == base or domain.endswith(f".{base}")
        return domain == pattern
    
    def _update_usage(self, token_id: str):
        """Update token usage statistics"""
        tokens = self.get_all_tokens()
        for t in tokens:
            if t.id == token_id:
                t.total_requests += 1
                t.last_used_at = datetime.now()
                break
        save_data(EMBED_TOKENS_FILE, [tk.dict() for tk in tokens])
    
    # ==========================================
    # Rate Limiting
    # ==========================================
    
    async def check_rate_limit(self, token_id: str) -> Dict[str, Any]:
        """Check if token has exceeded rate limits"""
        # For production, use Redis for rate limiting
        # This is a simplified implementation
        token = self.get_token_by_id(token_id)
        
        if not token:
            return {"allowed": False, "error": "Token not found"}
        
        # TODO: Implement proper rate limiting with Redis
        # For now, always allow
        return {
            "allowed": True,
            "remaining": token.rate_limit,
            "reset_at": datetime.now() + timedelta(minutes=1)
        }
    
    # ==========================================
    # Statistics
    # ==========================================
    
    def get_token_stats(self, token_id: str) -> Dict[str, Any]:
        """Get statistics for a token"""
        token = self.get_token_by_id(token_id)
        
        if not token:
            return {"error": "Token not found"}
        
        return {
            "id": token.id,
            "name": token.name,
            "total_requests": token.total_requests,
            "last_used_at": token.last_used_at,
            "created_at": token.created_at,
            "status": token.status.value,
            "scope": token.scope.value,
            "expires_at": token.expires_at,
            "is_expired": token.expires_at and datetime.now() > token.expires_at,
            "days_until_expiry": (token.expires_at - datetime.now()).days if token.expires_at else None
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get overall statistics"""
        tokens = self.get_all_tokens()
        
        total = len(tokens)
        active = sum(1 for t in tokens if t.status == TokenStatus.ACTIVE)
        expired = sum(1 for t in tokens if t.status == TokenStatus.EXPIRED)
        total_requests = sum(t.total_requests for t in tokens)
        
        by_scope = {
            "internal": sum(1 for t in tokens if t.scope == TokenScope.INTERNAL),
            "external": sum(1 for t in tokens if t.scope == TokenScope.EXTERNAL),
            "both": sum(1 for t in tokens if t.scope == TokenScope.BOTH)
        }
        
        by_type = {}
        for t in tokens:
            by_type[t.integration_type] = by_type.get(t.integration_type, 0) + 1
        
        return {
            "total": total,
            "active": active,
            "expired": expired,
            "revoked": sum(1 for t in tokens if t.status == TokenStatus.REVOKED),
            "inactive": sum(1 for t in tokens if t.status == TokenStatus.INACTIVE),
            "total_requests": total_requests,
            "by_scope": by_scope,
            "by_type": by_type
        }
    
    # ==========================================
    # Generate Widget Code
    # ==========================================
    
    def generate_widget_code(self, token_id: str, api_base_url: str = None) -> str:
        """Generate embed widget code for a token"""
        token = self.get_token_by_id(token_id)
        
        if not token:
            return "<!-- Token not found -->"
        
        api_url = api_base_url or "http://localhost:8000"
        
        return f'''<!-- PDAM Chatbot Widget -->
<script>
  window.PDAChatbot = window.PDAChatbot || {{}};
  window.PDAChatbot.config = {{
    token: "{token.token}",
    apiUrl: "{api_url}",
    position: "bottom-right",
    title: "PDAM Chatbot",
    subtitle: "Tirta Moedal Semarang",
    primaryColor: "#3B82F6"
  }};
</script>
<script src="{api_url}/widget.js" defer></script>
<!-- End PDAM Chatbot Widget -->'''


# Singleton
_embed_token_service: Optional[EmbedTokenService] = None

def get_embed_token_service() -> EmbedTokenService:
    global _embed_token_service
    if _embed_token_service is None:
        _embed_token_service = EmbedTokenService()
    return _embed_token_service
