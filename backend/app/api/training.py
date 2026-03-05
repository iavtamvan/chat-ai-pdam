"""
Training API Endpoints
Manage LLM model training and fine-tuning
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from app.core.config import settings
from app.services.llm_service import get_ollama_service
from app.services.document_service import get_document_processor
from app.core.database import get_document_count
from app.api.auth import get_current_user, require_admin

router = APIRouter()


# === Pydantic Models ===

class ModelPullRequest(BaseModel):
    """Request to pull/download a model"""
    model_name: str = Field(..., description="Model name (e.g., llama3.2:3b, mistral:7b)")


class TrainingDataRequest(BaseModel):
    """Training data for custom model"""
    examples: List[Dict[str, str]] = Field(
        ..., 
        description="List of {'question': '...', 'answer': '...'} pairs"
    )
    name: str = Field(..., description="Training dataset name")


class ReindexRequest(BaseModel):
    """Request to reindex documents"""
    force: bool = Field(default=False, description="Force reindex all documents")


# === Background Tasks ===

async def pull_model_task(model_name: str, status_store: Dict):
    """Background task to pull model"""
    status_store["status"] = "downloading"
    status_store["model"] = model_name
    status_store["started_at"] = datetime.now().isoformat()
    
    ollama = get_ollama_service()
    success = await ollama.pull_model(model_name)
    
    status_store["status"] = "completed" if success else "failed"
    status_store["completed_at"] = datetime.now().isoformat()
    status_store["success"] = success


# In-memory status tracking (use Redis in production)
_training_status: Dict[str, Any] = {}


# === API Endpoints ===

@router.get("/status")
async def get_training_status(
    current_user: Dict = Depends(get_current_user)
):
    """Get current training/model status"""
    
    ollama = get_ollama_service()
    health = await ollama.health_check()
    doc_count = await get_document_count()
    
    return {
        "llm_status": health,
        "document_count": doc_count,
        "current_operations": _training_status,
        "settings": {
            "model": settings.OLLAMA_MODEL,
            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "top_k_results": settings.TOP_K_RESULTS
        }
    }


@router.post("/pull-model")
async def pull_model(
    request: ModelPullRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_admin)
):
    """
    Pull/download a new model from Ollama
    
    Popular models:
    - llama3.2:3b - Fast, good for most tasks
    - llama3.2:1b - Very fast, lightweight
    - mistral:7b - High quality
    - gemma2:2b - Google's model, efficient
    - qwen2.5:3b - Good for Indonesian
    """
    
    # Check if already downloading
    if _training_status.get("status") == "downloading":
        raise HTTPException(
            status_code=409,
            detail=f"Sedang download model: {_training_status.get('model')}"
        )
    
    # Start background download
    _training_status.clear()
    background_tasks.add_task(pull_model_task, request.model_name, _training_status)
    
    return {
        "message": f"Mulai download model: {request.model_name}",
        "status": "started",
        "model": request.model_name,
        "check_status": "/api/training/status"
    }


@router.get("/models/available")
async def get_available_models():
    """Get list of available Ollama models to download"""
    
    # Popular models for Indonesian chatbot
    recommended_models = [
        {
            "name": "llama3.2:3b",
            "size": "2GB",
            "description": "Recommended - Fast and good quality",
            "language": "Multilingual (termasuk Indonesia)"
        },
        {
            "name": "llama3.2:1b", 
            "size": "1.3GB",
            "description": "Very fast, good for limited resources",
            "language": "Multilingual"
        },
        {
            "name": "mistral:7b",
            "size": "4.1GB",
            "description": "High quality, needs more RAM",
            "language": "Multilingual"
        },
        {
            "name": "gemma2:2b",
            "size": "1.6GB",
            "description": "Google's efficient model",
            "language": "Multilingual"
        },
        {
            "name": "qwen2.5:3b",
            "size": "1.9GB",
            "description": "Good for Asian languages",
            "language": "Multilingual (bagus untuk Indonesia)"
        },
        {
            "name": "phi3:mini",
            "size": "2.3GB",
            "description": "Microsoft's efficient model",
            "language": "Multilingual"
        },
        {
            "name": "nomic-embed-text",
            "size": "274MB",
            "description": "Embedding model for RAG",
            "language": "Multilingual"
        }
    ]
    
    ollama = get_ollama_service()
    health = await ollama.health_check()
    installed = health.get("available_models", [])
    
    # Mark which are installed
    for model in recommended_models:
        model["installed"] = (
            model["name"] in installed or 
            f"{model['name']}:latest" in installed
        )
    
    return {
        "recommended": recommended_models,
        "installed": installed,
        "current_chat_model": settings.OLLAMA_MODEL,
        "current_embedding_model": settings.OLLAMA_EMBEDDING_MODEL
    }


@router.post("/reindex")
async def reindex_documents(
    request: ReindexRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(require_admin)
):
    """
    Reindex all documents with current embedding model
    
    Useful after changing embedding model or settings
    """
    
    # TODO: Implement reindexing logic
    # This would:
    # 1. Get all documents from storage
    # 2. Re-chunk them
    # 3. Generate new embeddings
    # 4. Update vector database
    
    return {
        "message": "Reindex dimulai di background",
        "force": request.force,
        "note": "Fitur ini akan diimplementasi dengan queue system"
    }


@router.post("/add-examples")
async def add_training_examples(
    request: TrainingDataRequest,
    current_user: Dict = Depends(require_admin)
):
    """
    Add Q&A examples for training
    
    These will be stored and used to improve responses
    """
    
    doc_processor = get_document_processor()
    ollama = get_ollama_service()
    
    # Format examples as documents
    documents = []
    for i, example in enumerate(request.examples):
        doc_text = f"""Pertanyaan: {example.get('question', '')}
Jawaban: {example.get('answer', '')}"""
        documents.append(doc_text)
    
    # Generate embeddings
    embeddings = await ollama.get_embeddings_batch(documents)
    
    # Add to database
    from app.core.database import add_documents
    import hashlib
    from datetime import datetime
    
    ids = []
    metadatas = []
    for i, doc in enumerate(documents):
        doc_id = hashlib.md5(f"{request.name}_{i}_{doc[:50]}".encode()).hexdigest()[:16]
        ids.append(doc_id)
        metadatas.append({
            "type": "training_example",
            "dataset_name": request.name,
            "created_at": datetime.now().isoformat(),
            "created_by": current_user.get("npp", "unknown")
        })
    
    success = await add_documents(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    
    return {
        "success": success,
        "message": f"Added {len(documents)} training examples",
        "dataset_name": request.name
    }


@router.get("/benchmark")
async def run_benchmark(
    questions: int = Query(5, ge=1, le=20, description="Number of test questions"),
    current_user: Dict = Depends(get_current_user)
):
    """Run a simple benchmark to test system performance"""
    
    test_questions = [
        "Bagaimana cara cek tagihan air PDAM?",
        "Apa syarat untuk pemasangan baru?",
        "Dimana loket pembayaran terdekat?",
        "Bagaimana cara lapor kebocoran?",
        "Berapa tarif air per meter kubik?"
    ][:questions]
    
    from app.services.rag_service import get_rag_service
    rag = get_rag_service()
    
    results = []
    total_time = 0
    
    for q in test_questions:
        start = datetime.now()
        response = await rag.generate_answer(q, use_rag=True)
        elapsed = (datetime.now() - start).total_seconds()
        total_time += elapsed
        
        results.append({
            "question": q,
            "response_time": round(elapsed, 2),
            "has_sources": len(response.get("sources", [])) > 0,
            "answer_length": len(response.get("answer", ""))
        })
    
    return {
        "benchmark_results": results,
        "total_questions": len(test_questions),
        "total_time": round(total_time, 2),
        "average_time": round(total_time / len(test_questions), 2),
        "model": settings.OLLAMA_MODEL
    }


@router.post("/change-model")
async def change_active_model(
    model_name: str = Query(..., description="Model name to switch to"),
    current_user: Dict = Depends(require_admin)
):
    """
    Change the active LLM model
    
    Note: Model must be installed first via /pull-model
    """
    
    ollama = get_ollama_service()
    health = await ollama.health_check()
    
    available = health.get("available_models", [])
    
    if model_name not in available and f"{model_name}:latest" not in available:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model_name}' belum terinstall. Download dulu via /pull-model"
        )
    
    # Update settings (in production, save to database/env)
    settings.OLLAMA_MODEL = model_name
    ollama.model = model_name
    
    return {
        "success": True,
        "message": f"Model berhasil diganti ke {model_name}",
        "current_model": model_name
    }
