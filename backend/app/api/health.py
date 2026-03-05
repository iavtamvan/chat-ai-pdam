"""
Health Check API Endpoints
System health monitoring and diagnostics
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import platform
import os
import psutil

from app.core.config import settings
from app.services.llm_service import get_ollama_service
from app.core.database import get_document_count, get_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint
    
    Returns overall system health status
    """
    
    # Check Ollama
    ollama = get_ollama_service()
    ollama_health = await ollama.health_check()
    
    # Check ChromaDB
    try:
        client = get_client()
        chroma_healthy = True
        doc_count = await get_document_count()
    except Exception as e:
        chroma_healthy = False
        doc_count = 0
    
    overall_healthy = ollama_health.get("healthy", False) and chroma_healthy
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "api": True,
            "llm": ollama_health.get("healthy", False),
            "vector_db": chroma_healthy,
            "documents": doc_count
        }
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with system information
    
    Includes CPU, memory, disk usage
    """
    
    # System info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Ollama status
    ollama = get_ollama_service()
    ollama_health = await ollama.health_check()
    
    # ChromaDB status
    try:
        client = get_client()
        doc_count = await get_document_count()
        chroma_status = {
            "healthy": True,
            "document_count": doc_count,
            "persist_dir": settings.CHROMA_PERSIST_DIR
        }
    except Exception as e:
        chroma_status = {
            "healthy": False,
            "error": str(e)
        }
    
    return {
        "status": "healthy" if ollama_health.get("healthy") and chroma_status.get("healthy") else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "system": {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "cpu_usage_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": round((disk.used / disk.total) * 100, 1)
            }
        },
        "components": {
            "api": {
                "healthy": True,
                "host": settings.HOST,
                "port": settings.PORT
            },
            "llm": ollama_health,
            "vector_db": chroma_status
        },
        "settings": {
            "model": settings.OLLAMA_MODEL,
            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
            "chunk_size": settings.CHUNK_SIZE,
            "top_k_results": settings.TOP_K_RESULTS
        }
    }


@router.get("/health/llm")
async def llm_health_check():
    """Check LLM (Ollama) health specifically"""
    
    ollama = get_ollama_service()
    health = await ollama.health_check()
    
    # Test generation if healthy
    if health.get("healthy") and health.get("model_loaded"):
        try:
            start = datetime.now()
            test_response = await ollama.generate(
                prompt="Halo, sebutkan satu kata saja.",
                max_tokens=10,
                temperature=0.1
            )
            latency = (datetime.now() - start).total_seconds()
            health["test_generation"] = {
                "success": True,
                "latency_seconds": round(latency, 2),
                "response_preview": test_response[:50]
            }
        except Exception as e:
            health["test_generation"] = {
                "success": False,
                "error": str(e)
            }
    
    return health


@router.get("/health/vectordb")
async def vectordb_health_check():
    """Check Vector Database (ChromaDB) health"""
    
    try:
        client = get_client()
        doc_count = await get_document_count()
        
        # Get collection info
        from app.core.database import get_collection
        collection = get_collection()
        
        return {
            "healthy": True,
            "persist_dir": settings.CHROMA_PERSIST_DIR,
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "document_count": doc_count,
            "settings": {
                "chunk_size": settings.CHUNK_SIZE,
                "chunk_overlap": settings.CHUNK_OVERLAP,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD
            }
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e)
        }


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe
    
    Returns 200 if ready to accept traffic
    """
    
    ollama = get_ollama_service()
    ollama_health = await ollama.health_check()
    
    if not ollama_health.get("healthy"):
        return {"ready": False, "reason": "LLM not healthy"}
    
    if not ollama_health.get("model_loaded"):
        return {"ready": False, "reason": "Model not loaded"}
    
    return {"ready": True}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe
    
    Returns 200 if the service is alive
    """
    return {"alive": True, "timestamp": datetime.now().isoformat()}
