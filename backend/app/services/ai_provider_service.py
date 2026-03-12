"""
Multi-Model AI Provider Service
Supports multiple AI providers: OpenAI, Gemini, DeepSeek, Claude, Groq, OpenRouter, Ollama
"""

import httpx
import json
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
from abc import ABC, abstractmethod

from app.models.enterprise import (
    AIProvider, AIProviderCreate, AIProviderUpdate, AIProviderType, AIModel,
    load_data, save_data, AI_PROVIDERS_FILE
)
from app.core.config import settings


# ============================================
# DEFAULT MODELS PER PROVIDER
# ============================================

DEFAULT_MODELS = {
    AIProviderType.OPENAI: [
        AIModel(id="gpt-4o", name="gpt-4o", display_name="GPT-4o (Latest)", max_tokens=128000, supports_vision=True),
        AIModel(id="gpt-4o-mini", name="gpt-4o-mini", display_name="GPT-4o Mini", max_tokens=128000, supports_vision=True),
        AIModel(id="gpt-4-turbo", name="gpt-4-turbo", display_name="GPT-4 Turbo", max_tokens=128000, supports_vision=True),
        AIModel(id="gpt-3.5-turbo", name="gpt-3.5-turbo", display_name="GPT-3.5 Turbo", max_tokens=16385),
    ],
    AIProviderType.GEMINI: [
        AIModel(id="gemini-1.5-pro", name="gemini-1.5-pro", display_name="Gemini 1.5 Pro", max_tokens=1000000, supports_vision=True),
        AIModel(id="gemini-1.5-flash", name="gemini-1.5-flash", display_name="Gemini 1.5 Flash", max_tokens=1000000, supports_vision=True),
        AIModel(id="gemini-2.0-flash-exp", name="gemini-2.0-flash-exp", display_name="Gemini 2.0 Flash", max_tokens=1000000, supports_vision=True),
    ],
    AIProviderType.DEEPSEEK: [
        AIModel(id="deepseek-chat", name="deepseek-chat", display_name="DeepSeek Chat", max_tokens=64000),
        AIModel(id="deepseek-coder", name="deepseek-coder", display_name="DeepSeek Coder", max_tokens=64000),
        AIModel(id="deepseek-reasoner", name="deepseek-reasoner", display_name="DeepSeek R1", max_tokens=64000),
    ],
    AIProviderType.CLAUDE: [
        AIModel(id="claude-3-5-sonnet-20241022", name="claude-3-5-sonnet-20241022", display_name="Claude 3.5 Sonnet", max_tokens=200000, supports_vision=True),
        AIModel(id="claude-3-opus-20240229", name="claude-3-opus-20240229", display_name="Claude 3 Opus", max_tokens=200000, supports_vision=True),
        AIModel(id="claude-3-haiku-20240307", name="claude-3-haiku-20240307", display_name="Claude 3 Haiku", max_tokens=200000, supports_vision=True),
    ],
    AIProviderType.GROQ: [
        AIModel(id="llama-3.3-70b-versatile", name="llama-3.3-70b-versatile", display_name="Llama 3.3 70B", max_tokens=32768),
        AIModel(id="llama-3.1-8b-instant", name="llama-3.1-8b-instant", display_name="Llama 3.1 8B Instant", max_tokens=8192),
        AIModel(id="mixtral-8x7b-32768", name="mixtral-8x7b-32768", display_name="Mixtral 8x7B", max_tokens=32768),
        AIModel(id="gemma2-9b-it", name="gemma2-9b-it", display_name="Gemma 2 9B", max_tokens=8192),
    ],
    AIProviderType.OPENROUTER: [
        AIModel(id="openai/gpt-4o", name="openai/gpt-4o", display_name="GPT-4o via OpenRouter", max_tokens=128000),
        AIModel(id="anthropic/claude-3.5-sonnet", name="anthropic/claude-3.5-sonnet", display_name="Claude 3.5 via OpenRouter", max_tokens=200000),
        AIModel(id="google/gemini-pro-1.5", name="google/gemini-pro-1.5", display_name="Gemini Pro via OpenRouter", max_tokens=1000000),
        AIModel(id="deepseek/deepseek-r1", name="deepseek/deepseek-r1", display_name="DeepSeek R1 via OpenRouter", max_tokens=64000),
        AIModel(id="meta-llama/llama-3.3-70b-instruct", name="meta-llama/llama-3.3-70b-instruct", display_name="Llama 3.3 70B", max_tokens=32768),
    ],
    AIProviderType.OLLAMA: [
        AIModel(id="llama3.2:3b", name="llama3.2:3b", display_name="Llama 3.2 3B", max_tokens=4096),
        AIModel(id="llama3.2:1b", name="llama3.2:1b", display_name="Llama 3.2 1B", max_tokens=4096),
        AIModel(id="mistral:7b", name="mistral:7b", display_name="Mistral 7B", max_tokens=8192),
        AIModel(id="qwen2.5:3b", name="qwen2.5:3b", display_name="Qwen 2.5 3B", max_tokens=8192),
    ],
}

API_BASE_URLS = {
    AIProviderType.OPENAI: "https://api.openai.com/v1",
    AIProviderType.GEMINI: "https://generativelanguage.googleapis.com/v1beta",
    AIProviderType.DEEPSEEK: "https://api.deepseek.com/v1",
    AIProviderType.CLAUDE: "https://api.anthropic.com/v1",
    AIProviderType.GROQ: "https://api.groq.com/openai/v1",
    AIProviderType.OPENROUTER: "https://openrouter.ai/api/v1",
    AIProviderType.OLLAMA: "http://ollama:11434",
}


# ============================================
# PROVIDER ADAPTERS
# ============================================

class BaseProviderAdapter(ABC):
    """Base adapter for AI providers"""
    
    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.client: Optional[httpx.AsyncClient] = None
    
    async def get_client(self) -> httpx.AsyncClient:
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0),
                http2=True
            )
        return self.client
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        pass
    
    async def close(self):
        if self.client:
            await self.client.aclose()


class OpenAIAdapter(BaseProviderAdapter):
    """Adapter for OpenAI API (also works for DeepSeek, Groq, OpenRouter)"""
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        client = await self.get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if chat_history:
            messages.extend(chat_history[-10:])
        
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.provider.api_key}",
            "Content-Type": "application/json"
        }
        
        # Special headers for OpenRouter
        if self.provider.provider_type == AIProviderType.OPENROUTER:
            headers["HTTP-Referer"] = "https://pdamkotasmg.co.id"
            headers["X-Title"] = "PDAM Chatbot"
        
        base_url = self.provider.api_base_url or API_BASE_URLS.get(self.provider.provider_type)
        
        try:
            start_time = datetime.now()
            
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.provider.default_model or self.provider.models[0].id if self.provider.models else "gpt-3.5-turbo",
                    "messages": messages,
                    "temperature": self.provider.temperature,
                    "max_tokens": kwargs.get("max_tokens", self.provider.max_tokens),
                    "stream": False
                }
            )
            
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code} - {response.text}",
                    "provider": self.provider.name
                }
            
            data = response.json()
            answer = data["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "answer": answer,
                "provider": self.provider.name,
                "model": data.get("model"),
                "time_ms": elapsed_ms,
                "usage": data.get("usage", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider.name
            }
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        client = await self.get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if chat_history:
            messages.extend(chat_history[-10:])
        
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.provider.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.provider.provider_type == AIProviderType.OPENROUTER:
            headers["HTTP-Referer"] = "https://pdamkotasmg.co.id"
            headers["X-Title"] = "PDAM Chatbot"
        
        base_url = self.provider.api_base_url or API_BASE_URLS.get(self.provider.provider_type)
        
        try:
            async with client.stream(
                "POST",
                f"{base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self.provider.default_model or "gpt-3.5-turbo",
                    "messages": messages,
                    "temperature": self.provider.temperature,
                    "max_tokens": kwargs.get("max_tokens", self.provider.max_tokens),
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except:
                            continue
        except Exception as e:
            yield f"\n❌ Error: {str(e)}"


class GeminiAdapter(BaseProviderAdapter):
    """Adapter for Google Gemini API"""
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        client = await self.get_client()
        
        # Build contents
        contents = []
        
        if chat_history:
            for msg in chat_history[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        contents.append({
            "role": "user",
            "parts": [{"text": prompt}]
        })
        
        model = self.provider.default_model or "gemini-1.5-flash"
        base_url = self.provider.api_base_url or API_BASE_URLS[AIProviderType.GEMINI]
        
        try:
            start_time = datetime.now()
            
            response = await client.post(
                f"{base_url}/models/{model}:generateContent",
                params={"key": self.provider.api_key},
                json={
                    "contents": contents,
                    "systemInstruction": {"parts": [{"text": system_prompt}]} if system_prompt else None,
                    "tools": [{"googleSearch": {}}],
                    "generationConfig": {
                        "temperature": self.provider.temperature,
                        "maxOutputTokens": kwargs.get("max_tokens", self.provider.max_tokens),
                        "topP": 0.9
                    }
                }
            )
            
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code} - {response.text}",
                    "provider": self.provider.name
                }
            
            data = response.json()
            answer = data["candidates"][0]["content"]["parts"][0]["text"]
            
            return {
                "success": True,
                "answer": answer,
                "provider": self.provider.name,
                "model": model,
                "time_ms": elapsed_ms
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider.name
            }
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        # Gemini streaming implementation
        result = await self.generate(prompt, system_prompt, chat_history, **kwargs)
        if result["success"]:
            yield result["answer"]
        else:
            yield f"❌ Error: {result.get('error')}"


class ClaudeAdapter(BaseProviderAdapter):
    """Adapter for Anthropic Claude API"""
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        client = await self.get_client()
        
        messages = []
        if chat_history:
            for msg in chat_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "x-api-key": self.provider.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        base_url = self.provider.api_base_url or API_BASE_URLS[AIProviderType.CLAUDE]
        
        try:
            start_time = datetime.now()
            
            response = await client.post(
                f"{base_url}/messages",
                headers=headers,
                json={
                    "model": self.provider.default_model or "claude-3-haiku-20240307",
                    "max_tokens": kwargs.get("max_tokens", self.provider.max_tokens),
                    "system": system_prompt or "",
                    "messages": messages
                }
            )
            
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code} - {response.text}",
                    "provider": self.provider.name
                }
            
            data = response.json()
            answer = data["content"][0]["text"]
            
            return {
                "success": True,
                "answer": answer,
                "provider": self.provider.name,
                "model": data.get("model"),
                "time_ms": elapsed_ms,
                "usage": data.get("usage", {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider.name
            }
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        result = await self.generate(prompt, system_prompt, chat_history, **kwargs)
        if result["success"]:
            yield result["answer"]
        else:
            yield f"❌ Error: {result.get('error')}"


class OllamaAdapter(BaseProviderAdapter):
    """Adapter for local Ollama"""
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        client = await self.get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if chat_history:
            messages.extend(chat_history[-10:])
        
        messages.append({"role": "user", "content": prompt})
        
        base_url = self.provider.api_base_url or API_BASE_URLS[AIProviderType.OLLAMA]
        
        try:
            start_time = datetime.now()
            
            response = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": self.provider.default_model or "llama3.2:3b",
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": self.provider.temperature,
                        "num_predict": kwargs.get("max_tokens", self.provider.max_tokens)
                    }
                }
            )
            
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Ollama Error: {response.status_code}",
                    "provider": self.provider.name
                }
            
            data = response.json()
            answer = data["message"]["content"]
            
            return {
                "success": True,
                "answer": answer,
                "provider": self.provider.name,
                "model": self.provider.default_model,
                "time_ms": elapsed_ms
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": self.provider.name
            }
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        client = await self.get_client()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if chat_history:
            messages.extend(chat_history[-10:])
        
        messages.append({"role": "user", "content": prompt})
        
        base_url = self.provider.api_base_url or API_BASE_URLS[AIProviderType.OLLAMA]
        
        try:
            async with client.stream(
                "POST",
                f"{base_url}/api/chat",
                json={
                    "model": self.provider.default_model or "llama3.2:3b",
                    "messages": messages,
                    "stream": True
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except:
                            continue
        except Exception as e:
            yield f"\n❌ Error: {str(e)}"


# ============================================
# AI PROVIDER SERVICE
# ============================================

class AIProviderService:
    """Service for managing multiple AI providers"""
    
    def __init__(self):
        self._adapters: Dict[str, BaseProviderAdapter] = {}
    
    # ==========================================
    # CRUD Operations
    # ==========================================
    
    def get_all_providers(self) -> List[AIProvider]:
        """Get all AI providers"""
        data = load_data(AI_PROVIDERS_FILE)
        return [AIProvider(**item) for item in data]
    
    def get_provider(self, provider_id: str) -> Optional[AIProvider]:
        """Get single provider by ID"""
        for provider in self.get_all_providers():
            if provider.id == provider_id:
                return provider
        return None
    
    def get_active_providers(self) -> List[AIProvider]:
        """Get only active providers"""
        return [p for p in self.get_all_providers() if p.is_active]
    
    def get_default_provider(self) -> Optional[AIProvider]:
        """Get default provider"""
        for p in self.get_active_providers():
            if p.is_default:
                return p
        # Fallback to first active
        active = self.get_active_providers()
        return active[0] if active else None
    
    def create_provider(self, data: AIProviderCreate) -> AIProvider:
        """Create new AI provider"""
        provider = AIProvider(
            **data.dict(),
            models=DEFAULT_MODELS.get(data.provider_type, []),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # If this is default, unset others
        if provider.is_default:
            self._unset_all_defaults()
        
        providers = self.get_all_providers()
        providers.append(provider)
        save_data(AI_PROVIDERS_FILE, [p.dict() for p in providers])
        
        return provider
    
    def update_provider(self, provider_id: str, data: AIProviderUpdate) -> Optional[AIProvider]:
        """Update existing provider"""
        providers = self.get_all_providers()
        
        for i, p in enumerate(providers):
            if p.id == provider_id:
                update_data = data.dict(exclude_unset=True)
                update_data['updated_at'] = datetime.now()
                
                # If setting as default, unset others
                if update_data.get('is_default'):
                    self._unset_all_defaults()
                
                for key, value in update_data.items():
                    setattr(p, key, value)
                
                providers[i] = p
                save_data(AI_PROVIDERS_FILE, [pr.dict() for pr in providers])
                
                # Clear adapter cache
                if provider_id in self._adapters:
                    del self._adapters[provider_id]
                
                return p
        
        return None
    
    def delete_provider(self, provider_id: str) -> bool:
        """Delete AI provider"""
        providers = self.get_all_providers()
        original_count = len(providers)
        
        providers = [p for p in providers if p.id != provider_id]
        
        if len(providers) < original_count:
            save_data(AI_PROVIDERS_FILE, [p.dict() for p in providers])
            
            # Clear adapter cache
            if provider_id in self._adapters:
                del self._adapters[provider_id]
            
            return True
        return False
    
    def toggle_provider(self, provider_id: str) -> Optional[AIProvider]:
        """Toggle provider active status"""
        provider = self.get_provider(provider_id)
        if provider:
            return self.update_provider(
                provider_id,
                AIProviderUpdate(is_active=not provider.is_active)
            )
        return None
    
    def set_default(self, provider_id: str) -> Optional[AIProvider]:
        """Set provider as default"""
        self._unset_all_defaults()
        return self.update_provider(provider_id, AIProviderUpdate(is_default=True))
    
    def _unset_all_defaults(self):
        """Unset all providers as default"""
        providers = self.get_all_providers()
        for p in providers:
            if p.is_default:
                p.is_default = False
        save_data(AI_PROVIDERS_FILE, [pr.dict() for pr in providers])
    
    # ==========================================
    # Adapter Management
    # ==========================================
    
    def get_adapter(self, provider: AIProvider) -> BaseProviderAdapter:
        """Get or create adapter for provider"""
        if provider.id not in self._adapters:
            if provider.provider_type == AIProviderType.OLLAMA:
                self._adapters[provider.id] = OllamaAdapter(provider)
            elif provider.provider_type == AIProviderType.GEMINI:
                self._adapters[provider.id] = GeminiAdapter(provider)
            elif provider.provider_type == AIProviderType.CLAUDE:
                self._adapters[provider.id] = ClaudeAdapter(provider)
            else:
                # OpenAI-compatible (OpenAI, DeepSeek, Groq, OpenRouter)
                self._adapters[provider.id] = OpenAIAdapter(provider)
        
        return self._adapters[provider.id]
    
    # ==========================================
    # Generation
    # ==========================================
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        provider_id: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate response using specified or default provider"""
        
        if provider_id:
            provider = self.get_provider(provider_id)
        else:
            provider = self.get_default_provider()
        
        if not provider:
            return {
                "success": False,
                "error": "No active AI provider found"
            }
        
        adapter = self.get_adapter(provider)
        result = await adapter.generate(prompt, system_prompt, chat_history, **kwargs)
        
        # Update usage stats
        if result.get("success"):
            self._update_usage_stats(provider.id)
        
        return result
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        provider_id: str = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream response using specified or default provider"""
        
        if provider_id:
            provider = self.get_provider(provider_id)
        else:
            provider = self.get_default_provider()
        
        if not provider:
            yield "❌ No active AI provider found"
            return
        
        adapter = self.get_adapter(provider)
        
        async for chunk in adapter.generate_stream(prompt, system_prompt, chat_history, **kwargs):
            yield chunk
        
        # Update usage stats
        self._update_usage_stats(provider.id)
    
    async def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: str = None,
        chat_history: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate with automatic fallback to other providers"""
        
        providers = sorted(self.get_active_providers(), key=lambda p: p.priority)
        
        for provider in providers:
            adapter = self.get_adapter(provider)
            result = await adapter.generate(prompt, system_prompt, chat_history, **kwargs)
            
            if result.get("success"):
                self._update_usage_stats(provider.id)
                return result
        
        return {
            "success": False,
            "error": "All providers failed"
        }
    
    def _update_usage_stats(self, provider_id: str):
        """Update provider usage statistics"""
        providers = self.get_all_providers()
        for p in providers:
            if p.id == provider_id:
                p.total_requests += 1
                p.last_used_at = datetime.now()
                break
        save_data(AI_PROVIDERS_FILE, [pr.dict() for pr in providers])
    
    # ==========================================
    # Test Provider
    # ==========================================
    
    async def test_provider(self, provider_id: str) -> Dict[str, Any]:
        """Test provider connectivity"""
        provider = self.get_provider(provider_id)
        if not provider:
            return {"success": False, "error": "Provider not found"}
        
        adapter = self.get_adapter(provider)
        return await adapter.generate("Hello, respond with 'OK' only.")
    
    async def close(self):
        """Close all adapters"""
        for adapter in self._adapters.values():
            await adapter.close()


# Singleton
_ai_provider_service: Optional[AIProviderService] = None

def get_ai_provider_service() -> AIProviderService:
    global _ai_provider_service
    if _ai_provider_service is None:
        _ai_provider_service = AIProviderService()
    return _ai_provider_service
