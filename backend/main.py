"""
PDAM Chatbot AI - Optimized Main Application
High Performance FastAPI with Redis Caching and GPU Support
"""

import os
import asyncio
import uvicorn
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
from app.api import chat, documents, auth, health, training, monitoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle with optimized startup"""
    print("=" * 60)
    print("🚀 PDAM Chatbot AI - Starting...")
    print("=" * 60)
    
    start_time = datetime.now()
    
    # Initialize components in parallel
    print("📦 Initializing components...")
    
    # 1. Initialize Redis cache
    try:
        cache = await get_cache()
        stats = await cache.get_stats()
        print(f"✅ Redis connected (Keys: {stats.get('total_keys', 0)})")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        print("   Running without cache - performance will be degraded")
    
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
            print(f"✅ LLM connected: {settings.OLLAMA_MODEL}")
            if health_check.get("gpu", {}).get("available"):
                print(f"🎮 GPU acceleration: ENABLED")
            else:
                print(f"⚠️ GPU: Not detected (CPU mode)")
        else:
            print(f"⚠️ LLM not ready: {health_check.get('error')}")
    except Exception as e:
        print(f"❌ LLM error: {e}")
    
    # 4. Warmup LLM (background)
    asyncio.create_task(_warmup_llm())
    
    startup_time = (datetime.now() - start_time).total_seconds()
    print("=" * 60)
    print(f"✅ Startup complete in {startup_time:.2f}s")
    print(f"🌐 API: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 Docs: http://{settings.HOST}:{settings.PORT}/api/docs")
    print("=" * 60)
    
    yield
    
    # Cleanup
    print("👋 Shutting down...")
    llm = get_llm_service()
    await llm.close()


async def _warmup_llm():
    """Background LLM warmup"""
    try:
        await asyncio.sleep(5)  # Wait for other components
        llm = get_llm_service()
        await llm.warmup()
    except Exception as e:
        print(f"Warmup error: {e}")


# Create FastAPI app with optimizations
app = FastAPI(
    title="PDAM Chatbot AI",
    description="""
    🤖 High-Performance AI Chatbot untuk PDAM Tirta Moedal Kota Semarang
    
    Features:
    - ⚡ Response time < 10 detik dengan GPU + Redis
    - 💬 RAG-powered intelligent answers
    - 📄 Multi-format document training
    - 🔐 PDAM authentication integration
    - 📊 Performance monitoring & benchmarking
    """,
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
    default_response_class=ORJSONResponse  # Faster JSON serialization
)

# === Middleware ===

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request timing middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds() * 1000
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    return response


# === Routers ===
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])

# Static files
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with system info"""
    return {
        "name": "PDAM Chatbot AI",
        "version": "2.0.0 (Optimized)",
        "status": "running",
        "endpoints": {
            "docs": "/api/docs",
            "health": "/api/health",
            "chat": "/api/chat/send",
            "metrics": "/api/monitoring/metrics",
            "benchmark": "/api/monitoring/benchmark"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        log_level="warning",  # Reduce logging overhead
        access_log=False,  # Disable access log for performance
        loop="uvloop",  # Faster event loop
        http="httptools"  # Faster HTTP parser
    )
