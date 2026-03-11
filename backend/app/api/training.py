"""
Training API Router
Endpoints for document management, model training, and RAG operations
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import os
import hashlib

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
    status: str = "idle"
    total_documents: int = 0
    total_chunks: int = 0
    last_updated: Optional[str] = None
    error: Optional[str] = None


class PullModelRequest(BaseModel):
    model_name: str


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
    """Count chunks from ChromaDB first, fallback to files"""
    # Try ChromaDB first
    try:
        from app.core.database import get_collection
        col = get_collection()
        return col.count()
    except Exception as e:
        print(f"⚠️ ChromaDB count failed: {e}")

    # Fallback: count JSON files
    count = 0
    if CHUNKS_DIR.exists():
        for file in CHUNKS_DIR.iterdir():
            if file.suffix == '.json':
                count += 1
    return count


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF using multiple methods"""
    text = ""

    # Method 1: Try PyPDF2
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            print(f"  ✅ Extracted with PyPDF2: {len(text)} chars")
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️ PyPDF2 failed: {e}")

    # Method 2: Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            print(f"  ✅ Extracted with pdfplumber: {len(text)} chars")
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️ pdfplumber failed: {e}")

    # Method 3: Try pymupdf (fitz)
    try:
        import fitz
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        if text.strip():
            print(f"  ✅ Extracted with pymupdf: {len(text)} chars")
            return text
    except ImportError:
        pass
    except Exception as e:
        print(f"  ⚠️ pymupdf failed: {e}")

    print(f"  ❌ Could not extract text from PDF")
    return ""


def read_document_content(file_path: Path) -> str:
    """Read content from various document types"""
    ext = file_path.suffix.lower()

    if ext == '.pdf':
        return extract_text_from_pdf(file_path)

    elif ext in ['.txt', '.md']:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            with open(file_path, 'rb') as f:
                return f.read().decode('utf-8', errors='ignore')

    elif ext in ['.docx']:
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        except ImportError:
            print(f"  ⚠️ python-docx not installed")
            return ""
        except Exception as e:
            print(f"  ⚠️ docx read error: {e}")
            return ""

    else:
        # Try reading as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into chunks with overlap"""
    if not text or len(text.strip()) < 10:
        return []

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

    return [c for c in chunks if c and len(c) > 10]


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
        current_user: Optional[Dict] = Depends(get_current_user_optional)
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
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """Delete a document"""

    # Find file with this ID
    for file in DOCUMENTS_DIR.iterdir():
        if file.stem == document_id or file.name == document_id:
            file.unlink()

            # Also delete related chunks
            for chunk_file in CHUNKS_DIR.iterdir():
                if chunk_file.name.startswith(document_id):
                    chunk_file.unlink()

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
        rag_available = False
        rag = None

        # Try to get RAG service
        try:
            from app.services.rag_service import get_rag_service
            rag = get_rag_service()
            rag_available = True
            print("✅ RAG service available")
        except Exception as e:
            print(f"⚠️ RAG service not available: {e}")

        # Clear old chunks
        for chunk_file in CHUNKS_DIR.iterdir():
            if chunk_file.suffix == '.json':
                chunk_file.unlink()

        for doc in documents:
            file_path = DOCUMENTS_DIR / doc['filename']
            if not file_path.exists():
                continue

            print(f"📄 Processing: {doc['filename']}")

            # Read content based on file type
            content = read_document_content(file_path)

            if not content or len(content.strip()) < 10:
                print(f"  ⚠️ No content extracted from {doc['filename']}")
                continue

            print(f"  📝 Content length: {len(content)} chars")

            # Chunk the content
            chunks = chunk_text(content, chunk_size=500, overlap=50)
            print(f"  📦 Created {len(chunks)} chunks")

            # Process each chunk
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc['id']}_{i}"

                if rag_available and rag:
                    # Index to vector database
                    try:
                        success = await rag.index_document({
                            "id": chunk_id,
                            "content": chunk,
                            "title": doc['filename'],
                            "source": doc['filename'],
                            "chunk_index": i
                        })
                        if success:
                            total_chunks += 1
                    except Exception as e:
                        print(f"  ⚠️ Error indexing chunk {i}: {e}")
                        # Fallback to file
                        chunk_file = CHUNKS_DIR / f"{chunk_id}.json"
                        with open(chunk_file, 'w', encoding='utf-8') as f:
                            json.dump({
                                "id": chunk_id,
                                "content": chunk,
                                "source": doc['filename'],
                                "chunk_index": i
                            }, f, ensure_ascii=False, indent=2)
                        total_chunks += 1
                else:
                    # Save chunk to file (fallback)
                    chunk_file = CHUNKS_DIR / f"{chunk_id}.json"
                    with open(chunk_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            "id": chunk_id,
                            "content": chunk,
                            "source": doc['filename'],
                            "chunk_index": i
                        }, f, ensure_ascii=False, indent=2)
                    total_chunks += 1

        print(f"✅ Retrain completed: {total_chunks} chunks indexed")

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
        import traceback
        traceback.print_exc()

        status = {
            "status": "error",
            "total_documents": len(get_documents_list()),
            "total_chunks": count_chunks(),
            "last_updated": datetime.now().isoformat(),
            "error": str(e)
        }
        save_training_status(status)


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
        request: PullModelRequest,
        background_tasks: BackgroundTasks = None,
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """Pull/download an Ollama model"""
    import httpx

    model_name = request.model_name

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


@router.delete("/models/{model_name:path}")
async def delete_model(
        model_name: str,
        current_user: Optional[Dict] = Depends(get_current_user_optional)
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


@router.get("/chunks")
async def list_chunks(
        limit: int = 100,
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """List all chunks from vector database"""
    try:
        from app.core.database import get_collection
        col = get_collection()

        result = col.get(
            limit=limit,
            include=["documents", "metadatas"]
        )

        chunks = []
        for i, (doc_id, doc, meta) in enumerate(zip(
                result.get("ids", []),
                result.get("documents", []),
                result.get("metadatas", [])
        )):
            chunks.append({
                "id": doc_id,
                "content_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                "filename": meta.get("filename", "unknown"),
                "source": meta.get("source", "unknown"),
                "chunk_index": meta.get("chunk_index", 0)
            })

        return {
            "success": True,
            "total": col.count(),
            "chunks": chunks
        }
    except Exception as e:
        return {"success": False, "error": str(e), "chunks": []}


@router.get("/chunks/by-document/{document_id}")
async def get_chunks_by_document(
        document_id: str,
        current_user: Optional[Dict] = Depends(get_current_user_optional)
) -> Dict:
    """Get chunks for a specific document"""
    try:
        from app.core.database import get_collection
        col = get_collection()

        # Get all chunks and filter by document
        result = col.get(
            include=["documents", "metadatas"]
        )

        chunks = []
        for doc_id, doc, meta in zip(
                result.get("ids", []),
                result.get("documents", []),
                result.get("metadatas", [])
        ):
            # Match by document ID prefix or filename
            if doc_id.startswith(document_id) or meta.get("filename", "").startswith(document_id):
                chunks.append({
                    "id": doc_id,
                    "content_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                    "chunk_index": meta.get("chunk_index", 0)
                })

        return {
            "success": True,
            "document_id": document_id,
            "total_chunks": len(chunks),
            "chunks": sorted(chunks, key=lambda x: x.get("chunk_index", 0))
        }
    except Exception as e:
        return {"success": False, "error": str(e), "chunks": []}