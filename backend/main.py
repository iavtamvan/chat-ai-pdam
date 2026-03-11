"""
PDAM Chatbot AI - Enterprise Edition
Full-featured with Multi-Provider AI, API Integration, and Embed Management
"""

import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import ORJSONResponse
from contextlib import asynccontextmanager
from datetime import datetime

from app.core.config import settings
from app.core.database import init_vector_db
from app.services.cache_service import get_cache
from app.services.llm_service import get_llm_service

# API Routers
from app.api import chat, documents, auth, health, training, monitoring

# Enterprise Routers
from app.api import api_integrations, ai_providers, embed_tokens


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle"""
    print("=" * 60)
    print("🚀 PDAM Chatbot AI Enterprise - Starting...")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Initialize components
    print("📦 Initializing components...")
    
    # Create data directory
    os.makedirs("./data", exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # 1. Initialize Redis cache
    try:
        cache = await get_cache()
        stats = await cache.get_stats()
        print(f"✅ Redis connected (Keys: {stats.get('total_keys', 0)})")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
    
    # 2. Initialize Vector database
    try:
        await init_vector_db()
        print("✅ Vector database initialized")
    except Exception as e:
        print(f"❌ Vector DB error: {e}")
    
    # 3. Check LLM availability
    try:
        llm = get_llm_service()
        health_check = await llm.health_check()
        if health_check.get("healthy"):
            print(f"✅ Ollama LLM connected: {settings.OLLAMA_MODEL}")
        else:
            print(f"⚠️ Ollama not ready: {health_check.get('error')}")
    except Exception as e:
        print(f"❌ LLM error: {e}")
    
    print("✅ Data directories ready")
    
    # 4. Warmup LLM (background)
    asyncio.create_task(_warmup_llm())
    
    startup_time = (datetime.now() - start_time).total_seconds()
    print("=" * 60)
    print(f"✅ Startup complete in {startup_time:.2f}s")
    print(f"🌐 API: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Docs: http://{settings.HOST}:{settings.PORT}/api/docs")
    print("=" * 60)
    
    yield
    
    print("👋 Shutting down...")


async def _warmup_llm():
    """Background LLM warmup"""
    try:
        await asyncio.sleep(5)
        llm = get_llm_service()
        await llm.warmup()
    except Exception as e:
        print(f"Warmup error: {e}")


# Create FastAPI app
app = FastAPI(
    title="PDAM Chatbot AI Enterprise",
    description="""
    🤖 Enterprise AI Chatbot untuk PDAM Tirta Moedal Kota Semarang
    
    ## Features:
    - ⚡ Multi-Provider AI (OpenAI, Gemini, DeepSeek, Claude, Groq, Ollama)
    - 🔗 API Integration Manager (Like Postman)
    - 🎫 Embed Token Management
    - 💬 RAG-powered intelligent answers
    - 📄 Multi-format document training
    - 🔐 PDAM authentication integration
    - 📊 Performance monitoring
    """,
    version="3.0.0-enterprise",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
    default_response_class=ORJSONResponse
)

# === Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds() * 1000
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    return response


# === Core Routers ===
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])

# === Enterprise Routers ===
app.include_router(api_integrations.router, prefix="/api/integrations", tags=["API Integrations"])
app.include_router(ai_providers.router, prefix="/api/ai-providers", tags=["AI Providers"])
app.include_router(embed_tokens.router, prefix="/api/embed-tokens", tags=["Embed Tokens"])

# Static files
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "PDAM Chatbot AI Enterprise",
        "version": "3.0.0",
        "status": "running",
        "features": ["Multi-Provider AI", "API Integration Manager", "Embed Token Management", "RAG Document Search"],
        "endpoints": {
            "docs": "/api/docs",
            "health": "/api/health",
            "ai_providers": "/api/ai-providers",
            "integrations": "/api/integrations",
            "embed_tokens": "/api/embed-tokens"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, workers=4, log_level="info")
