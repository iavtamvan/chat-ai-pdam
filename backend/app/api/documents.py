"""
Documents API Endpoints
Upload, manage, and query documents for RAG
"""

import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.config import settings
from app.services.document_service import get_document_processor
from app.api.auth import get_current_user, require_admin

router = APIRouter()


# === Pydantic Models ===

class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    success: bool
    message: str
    filename: Optional[str] = None
    chunks: Optional[int] = None
    processing_time: Optional[float] = None


class DocumentSearchRequest(BaseModel):
    """Document search request"""
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    filter_type: Optional[str] = None


class DocumentInfo(BaseModel):
    """Document information"""
    filename: str
    file_type: str
    upload_date: str
    chunks: int
    size_bytes: Optional[int] = None


# === API Endpoints ===

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="Document to upload"),
    category: str = Form(default="general", description="Document category"),
    description: str = Form(default="", description="Document description"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Upload a document for RAG training
    
    Supported formats: PDF, Word (doc/docx), Excel (xls/xlsx), 
    Images (jpg/png), Text (txt/md)
    """
    
    start_time = datetime.now()
    
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format file tidak didukung. Format yang didukung: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File terlalu besar. Maksimal: {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = Path(settings.UPLOAD_DIR) / unique_filename
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process document
        doc_processor = get_document_processor()
        success, message, chunks = await doc_processor.process_document(
            file_path=str(file_path),
            filename=file.filename,
            metadata={
                "category": category,
                "description": description,
                "uploaded_by": current_user.get("npp", "unknown"),
                "original_filename": file.filename,
                "stored_filename": unique_filename,
                "file_size": file_size
            }
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        if success:
            return DocumentUploadResponse(
                success=True,
                message=message,
                filename=file.filename,
                chunks=chunks,
                processing_time=round(processing_time, 2)
            )
        else:
            # Remove file if processing failed
            if file_path.exists():
                os.remove(file_path)
            
            return DocumentUploadResponse(
                success=False,
                message=message
            )
            
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.post("/upload-multiple")
async def upload_multiple_documents(
    files: List[UploadFile] = File(..., description="Multiple documents to upload"),
    category: str = Form(default="general", description="Document category"),
    current_user: Dict = Depends(get_current_user)
):
    """Upload multiple documents at once"""
    
    results = []
    
    for file in files:
        try:
            # Reuse single upload logic
            ext = Path(file.filename).suffix.lower()
            if ext not in settings.ALLOWED_EXTENSIONS:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": f"Format tidak didukung: {ext}"
                })
                continue
            
            unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
            file_path = Path(settings.UPLOAD_DIR) / unique_filename
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            doc_processor = get_document_processor()
            success, message, chunks = await doc_processor.process_document(
                file_path=str(file_path),
                filename=file.filename,
                metadata={
                    "category": category,
                    "uploaded_by": current_user.get("npp", "unknown")
                }
            )
            
            results.append({
                "filename": file.filename,
                "success": success,
                "message": message,
                "chunks": chunks if success else None
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "message": str(e)
            })
    
    success_count = sum(1 for r in results if r["success"])
    
    return {
        "total": len(files),
        "success": success_count,
        "failed": len(files) - success_count,
        "results": results
    }


@router.post("/search")
async def search_documents(
    request: DocumentSearchRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Search documents using semantic similarity
    
    Returns relevant document chunks for the query
    """
    
    doc_processor = get_document_processor()
    
    filter_metadata = None
    if request.filter_type:
        filter_metadata = {"file_type": request.filter_type}
    
    results = await doc_processor.search_similar(
        query=request.query,
        top_k=request.top_k,
        filter_metadata=filter_metadata
    )
    
    return {
        "query": request.query,
        "count": len(results),
        "results": results
    }


@router.get("/list")
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Dict = Depends(get_current_user)
):
    """List all uploaded documents"""
    
    doc_processor = get_document_processor()
    stats = await doc_processor.get_document_stats()
    
    documents = stats.get("documents", [])
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    paginated = documents[start:end]
    
    return {
        "total": len(documents),
        "page": page,
        "limit": limit,
        "total_pages": (len(documents) + limit - 1) // limit,
        "documents": paginated,
        "file_types": stats.get("file_types", {}),
        "total_chunks": stats.get("total_chunks", 0)
    }


@router.get("/stats")
async def get_document_stats(
    current_user: Dict = Depends(get_current_user)
):
    """Get document statistics"""
    
    doc_processor = get_document_processor()
    stats = await doc_processor.get_document_stats()
    
    # Get upload directory size
    upload_dir = Path(settings.UPLOAD_DIR)
    total_size = sum(f.stat().st_size for f in upload_dir.glob("*") if f.is_file())
    
    return {
        **stats,
        "storage_used_mb": round(total_size / (1024 * 1024), 2),
        "storage_limit_mb": settings.MAX_UPLOAD_SIZE // (1024 * 1024) * 100  # Rough estimate
    }


@router.delete("/{filename}")
async def delete_document(
    filename: str,
    current_user: Dict = Depends(require_admin)
):
    """Delete a document and its chunks (Admin only)"""
    
    doc_processor = get_document_processor()
    success, message = await doc_processor.delete_document_by_filename(filename)
    
    # Also try to delete the physical file
    upload_dir = Path(settings.UPLOAD_DIR)
    for file in upload_dir.glob(f"*{filename}"):
        try:
            os.remove(file)
        except:
            pass
    
    return {
        "success": success,
        "message": message,
        "filename": filename
    }


@router.delete("/reset/all")
async def reset_all_documents(
    confirm: bool = Query(False, description="Confirm reset"),
    current_user: Dict = Depends(require_admin)
):
    """Reset all documents (Admin only - DANGEROUS!)"""
    
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Konfirmasi reset dengan ?confirm=true"
        )
    
    from app.core.database import reset_database
    
    success = await reset_database()
    
    # Clean upload directory
    upload_dir = Path(settings.UPLOAD_DIR)
    for file in upload_dir.glob("*"):
        try:
            os.remove(file)
        except:
            pass
    
    return {
        "success": success,
        "message": "Database direset" if success else "Gagal reset database"
    }


@router.get("/download/{filename}")
async def download_document(
    filename: str,
    current_user: Dict = Depends(get_current_user)
):
    """Download an uploaded document"""
    
    upload_dir = Path(settings.UPLOAD_DIR)
    
    # Find file (might have UUID prefix)
    matching_files = list(upload_dir.glob(f"*{filename}"))
    
    if not matching_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = matching_files[0]
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream"
    )
