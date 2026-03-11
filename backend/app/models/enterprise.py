"""
Database Models for PDAM Chatbot AI Enterprise
- API Integration Management
- Multi-Model AI Providers
- Embed Token Management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import json
import os

# ============================================
# ENUMS
# ============================================

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class AuthType(str, Enum):
    NONE = "none"
    BEARER = "bearer"
    BASIC = "basic"
    API_KEY = "api_key"
    CUSTOM = "custom"

class AIProviderType(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    CUSTOM = "custom"

class TokenScope(str, Enum):
    INTERNAL = "internal"  # Requires PDAM login
    EXTERNAL = "external"  # Public access
    BOTH = "both"

class TokenStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ============================================
# API INTEGRATION MODELS
# ============================================

class APIHeader(BaseModel):
    """Header for API request"""
    key: str
    value: str
    enabled: bool = True

class APIParameter(BaseModel):
    """Parameter for API request"""
    key: str
    value: str
    param_type: str = "query"  # query, path, body
    enabled: bool = True

class APIEndpoint(BaseModel):
    """API Endpoint Configuration - Like Postman"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = ""
    
    # Request Config
    method: HttpMethod = HttpMethod.GET
    url: str
    headers: List[APIHeader] = []
    parameters: List[APIParameter] = []
    body_type: str = "json"  # json, form, raw
    body: Optional[str] = None
    
    # Auth Config
    auth_type: AuthType = AuthType.NONE
    auth_config: Dict[str, Any] = {}
    
    # Response Config
    response_mapping: Dict[str, str] = {}  # Map response fields to display names
    success_message: Optional[str] = None
    error_message: Optional[str] = None
    
    # Chat Integration
    trigger_keywords: List[str] = []  # Keywords that trigger this API
    auto_execute: bool = False  # Execute automatically when keywords detected
    display_format: str = "table"  # table, list, card, raw
    
    # Status
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Category
    category: str = "general"


class APIEndpointCreate(BaseModel):
    """Create API Endpoint"""
    name: str
    description: Optional[str] = ""
    method: HttpMethod = HttpMethod.GET
    url: str
    headers: List[APIHeader] = []
    parameters: List[APIParameter] = []
    body_type: str = "json"
    body: Optional[str] = None
    auth_type: AuthType = AuthType.NONE
    auth_config: Dict[str, Any] = {}
    response_mapping: Dict[str, str] = {}
    trigger_keywords: List[str] = []
    auto_execute: bool = False
    display_format: str = "table"
    category: str = "general"


class APIEndpointUpdate(BaseModel):
    """Update API Endpoint"""
    name: Optional[str] = None
    description: Optional[str] = None
    method: Optional[HttpMethod] = None
    url: Optional[str] = None
    headers: Optional[List[APIHeader]] = None
    parameters: Optional[List[APIParameter]] = None
    body_type: Optional[str] = None
    body: Optional[str] = None
    auth_type: Optional[AuthType] = None
    auth_config: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, str]] = None
    trigger_keywords: Optional[List[str]] = None
    auto_execute: Optional[bool] = None
    display_format: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None


# ============================================
# AI PROVIDER MODELS
# ============================================

class AIModel(BaseModel):
    """AI Model within a provider"""
    id: str
    name: str
    display_name: Optional[str] = None
    max_tokens: int = 4096
    supports_streaming: bool = True
    supports_vision: bool = False
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0

class AIProvider(BaseModel):
    """AI Provider Configuration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    provider_type: AIProviderType
    
    # API Config
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    organization_id: Optional[str] = None
    
    # Models
    models: List[AIModel] = []
    default_model: Optional[str] = None
    
    # Settings
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 0.9
    
    # Status
    is_active: bool = True
    is_default: bool = False
    priority: int = 0  # Lower = higher priority for fallback
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    total_requests: int = 0
    total_tokens: int = 0


class AIProviderCreate(BaseModel):
    """Create AI Provider"""
    name: str
    provider_type: AIProviderType
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    organization_id: Optional[str] = None
    default_model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    is_active: bool = True
    is_default: bool = False
    priority: int = 0


class AIProviderUpdate(BaseModel):
    """Update AI Provider"""
    name: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    organization_id: Optional[str] = None
    default_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    priority: Optional[int] = None


# ============================================
# EMBED TOKEN MODELS
# ============================================

class EmbedToken(BaseModel):
    """Embed Token for Widget/WhatsApp Integration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    token: str = Field(default_factory=lambda: f"pdam_{uuid.uuid4().hex}")
    name: str
    description: Optional[str] = ""
    
    # Scope & Access
    scope: TokenScope = TokenScope.EXTERNAL
    allowed_domains: List[str] = ["*"]  # Domains allowed to use this token
    allowed_ips: List[str] = ["*"]  # IPs allowed
    
    # Integration Type
    integration_type: str = "widget"  # widget, whatsapp, api
    webhook_url: Optional[str] = None  # For WhatsApp
    
    # AI Provider
    ai_provider_id: Optional[str] = None  # Which AI provider to use
    
    # Rate Limiting
    rate_limit: int = 100  # Requests per minute
    daily_limit: int = 10000  # Requests per day
    
    # Expiration
    expires_at: Optional[datetime] = None  # None = unlimited
    
    # Status
    status: TokenStatus = TokenStatus.ACTIVE
    
    # Usage Stats
    total_requests: int = 0
    last_used_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None


class EmbedTokenCreate(BaseModel):
    """Create Embed Token"""
    name: str
    description: Optional[str] = ""
    scope: TokenScope = TokenScope.EXTERNAL
    allowed_domains: List[str] = ["*"]
    allowed_ips: List[str] = ["*"]
    integration_type: str = "widget"
    webhook_url: Optional[str] = None
    ai_provider_id: Optional[str] = None
    rate_limit: int = 100
    daily_limit: int = 10000
    expires_at: Optional[datetime] = None


class EmbedTokenUpdate(BaseModel):
    """Update Embed Token"""
    name: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[TokenScope] = None
    allowed_domains: Optional[List[str]] = None
    allowed_ips: Optional[List[str]] = None
    ai_provider_id: Optional[str] = None
    rate_limit: Optional[int] = None
    daily_limit: Optional[int] = None
    expires_at: Optional[datetime] = None
    status: Optional[TokenStatus] = None


# ============================================
# JSON FILE STORAGE (Simple persistence)
# ============================================

DATA_DIR = "./data"

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_data(filename: str) -> List[Dict]:
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(filename: str, data: List[Dict]):
    ensure_data_dir()
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

# File names
API_ENDPOINTS_FILE = "api_endpoints.json"
AI_PROVIDERS_FILE = "ai_providers.json"
EMBED_TOKENS_FILE = "embed_tokens.json"
