"""
Training API Router
Endpoints for document management, model training, and RAG operations
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import os
import shutil
import asyncio

from app.api.auth import get_current_user, get_current_user_optional

router = APIRouter()

# Paths
DOCUMENTS_DIR = Path("./data/documents")
TRAINING_STATUS_FILE = Path("./data/training_status.json")
CHUNKS_DIR = Path("./data/chunks")

# Ensure directories exist
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================
# MODELS
# ============================================

class TrainingStatus(BaseModel):
    status: str = "idle"  # idle, processing, completed, error
    total_documents: int = 0
    total_chunks: int = 0
    last_updated: Optional[str] = None
    error: Optional[str] = None


class DocumentInfo(BaseModel):
    id: str
    filename: str
    size: int
    uploaded_at: str
    status: str = "pending"


# ============================================
# HELPERS
# ============================================

def load_training_status() -> Dict:
    if TRAINING_STATUS_FILE.exists():
        try:
            with open(TRAINING_STATUS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "status": "idle",
        "total_documents": 0,
        "total_chunks": 0,
        "last_updated": None
    }


def save_training_status(status: Dict):
    TRAINING_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRAINING_STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def get_documents_list() -> List[Dict]:
    documents = []
    if DOCUMENTS_DIR.exists():
        for file in DOCUMENTS_DIR.iterdir():
            if file.is_file() and not file.name.startswith('.'):
                stat = file.stat()
                documents.append({
                    "id": file.stem,
                    "filename": file.name,
                    "size": stat.st_size,
                    "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "status": "indexed"
                })
    return documents


def count_chunks() -> int:
    count = 0
    if CHUNKS_DIR.exists():
        for file in CHUNKS_DIR.iterdir():
            if file.suffix == '.json':
                count += 1
    return count


# ============================================
# ENDPOINTS - DOCUMENTS
# ============================================

@router.get("/documents")
async def list_documents(
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> List[Dict]:
    """List all uploaded documents"""
    return get_documents_list()


@router.post("/documents/upload")
async def upload_document(
        file: UploadFile = File(...),
        current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Upload a document for training"""

    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.md', '.docx', '.doc'}
    ext = Path(file.filename).suffix.lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Allowed: {allowed_extensions}"
        )

    # Save file
    file_path = DOCUMENTS_DIR / file.filename

    try:
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)

        return {
            "success": True,
            "filename": file.filename,
            "size": len(content),
            "message": "Document uploaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
        document_id: str,
        current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Delete a document"""

    # Find file with this ID
    for file in DOCUMENTS_DIR.iterdir():
        if file.stem == document_id or file.name == document_id:
            file.unlink()
            return {"success": True, "message": f"Deleted {file.name}"}

    raise HTTPException(status_code=404, detail="Document not found")


# ============================================
# ENDPOINTS - TRAINING / RETRAIN
# ============================================

@router.get("/status")
async def get_training_status(
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """Get current training status"""
    status = load_training_status()
    status["total_documents"] = len(get_documents_list())
    status["total_chunks"] = count_chunks()
    return status


@router.post("/retrain")
async def retrain_documents(
        background_tasks: BackgroundTasks,
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """Retrain/reindex all documents into vector database"""

    # Update status to processing
    status = {
        "status": "processing",
        "total_documents": len(get_documents_list()),
        "total_chunks": 0,
        "last_updated": datetime.now().isoformat(),
        "error": None
    }
    save_training_status(status)

    # Run retraining in background
    background_tasks.add_task(do_retrain)

    return {
        "success": True,
        "message": "Retraining started",
        "status": "processing"
    }


async def do_retrain():
    """Background task to retrain documents"""
    try:
        print("🔄 Starting retrain process...")

        documents = get_documents_list()
        total_chunks = 0

        # Try to use RAG service if available
        try:
            from app.services.rag_service import get_rag_service
            rag = get_rag_service()

            for doc in documents:
                file_path = DOCUMENTS_DIR / doc['filename']
                if file_path.exists():
                    print(f"📄 Processing: {doc['filename']}")

                    # Read content
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except:
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('utf-8', errors='ignore')

                    # Simple chunking
                    chunks = chunk_text(content, chunk_size=500, overlap=50)

                    # Index chunks
                    for i, chunk in enumerate(chunks):
                        await rag.index_document({
                            "id": f"{doc['id']}_{i}",
                            "content": chunk,
                            "title": doc['filename'],
                            "source": doc['filename']
                        })
                        total_chunks += 1

            print(f"✅ Retrain completed: {total_chunks} chunks indexed")

        except ImportError:
            print("⚠️ RAG service not available, doing simple chunk save")

            # Fallback: Just save chunks to files
            for doc in documents:
                file_path = DOCUMENTS_DIR / doc['filename']
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except:
                        with open(file_path, 'rb') as f:
                            content = f.read().decode('utf-8', errors='ignore')

                    chunks = chunk_text(content, chunk_size=500, overlap=50)

                    for i, chunk in enumerate(chunks):
                        chunk_file = CHUNKS_DIR / f"{doc['id']}_{i}.json"
                        with open(chunk_file, 'w', encoding='utf-8') as f:
                            json.dump({
                                "id": f"{doc['id']}_{i}",
                                "content": chunk,
                                "source": doc['filename']
                            }, f, ensure_ascii=False)
                        total_chunks += 1

        # Update status
        status = {
            "status": "completed",
            "total_documents": len(documents),
            "total_chunks": total_chunks,
            "last_updated": datetime.now().isoformat(),
            "error": None
        }
        save_training_status(status)

    except Exception as e:
        print(f"❌ Retrain error: {e}")
        status = {
            "status": "error",
            "total_documents": len(get_documents_list()),
            "total_chunks": count_chunks(),
            "last_updated": datetime.now().isoformat(),
            "error": str(e)
        }
        save_training_status(status)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into chunks with overlap"""
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < text_len:
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)

            if break_point > chunk_size * 0.5:
                chunk = text[start:start + break_point + 1]
                end = start + break_point + 1

        chunks.append(chunk.strip())
        start = end - overlap

    return [c for c in chunks if c]


# ============================================
# ENDPOINTS - OLLAMA MODEL MANAGEMENT
# ============================================

@router.get("/models")
async def list_models(
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """List available Ollama models"""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("http://ollama:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "models": data.get("models", [])
                }
            return {"success": False, "models": [], "error": f"Status {resp.status_code}"}
    except Exception as e:
        return {"success": False, "models": [], "error": str(e)}


@router.post("/pull-model")
async def pull_model(
        model_name: str = Form(...),
        background_tasks: BackgroundTasks = None,
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """Pull/download an Ollama model"""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                "http://ollama:11434/api/pull",
                json={"name": model_name, "stream": False}
            )

            if resp.status_code == 200:
                return {
                    "success": True,
                    "message": f"Model {model_name} pulled successfully"
                }
            else:
                return {
                    "success": False,
                    "error": resp.text
                }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/models/{model_name}")
async def delete_model(
        model_name: str,
        current_user: Dict = Depends(get_current_user)
) -> Dict:
    """Delete an Ollama model"""
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(
                "http://ollama:11434/api/delete",
                json={"name": model_name}
            )

            if resp.status_code == 200:
                return {"success": True, "message": f"Model {model_name} deleted"}
            else:
                return {"success": False, "error": resp.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# ENDPOINTS - STATS
# ============================================

@router.get("/stats/overview")
async def get_stats_overview(
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """Get training stats overview"""
    documents = get_documents_list()
    status = load_training_status()

    total_size = sum(d.get('size', 0) for d in documents)

    return {
        "total_documents": len(documents),
        "total_chunks": count_chunks(),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "training_status": status.get("status", "idle"),
        "last_trained": status.get("last_updated")
    }