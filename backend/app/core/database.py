"""
Vector Database Initialization using ChromaDB
Free, local, and persistent vector storage
"""

import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Optional, List, Dict, Any
import asyncio

from app.core.config import settings

# Global ChromaDB client and collection
_chroma_client: Optional[chromadb.Client] = None
_collection: Optional[chromadb.Collection] = None


def get_chroma_settings() -> ChromaSettings:
    """Get ChromaDB settings"""
    return ChromaSettings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=settings.CHROMA_PERSIST_DIR,
        anonymized_telemetry=False
    )


async def init_vector_db():
    """Initialize ChromaDB vector database"""
    global _chroma_client, _collection
    
    # Create persist directory
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    
    # Initialize ChromaDB client with persistence
    _chroma_client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=chromadb.Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    # Get or create collection
    _collection = _chroma_client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={
            "description": "PDAM Kota Semarang document embeddings",
            "hnsw:space": "cosine"  # Use cosine similarity
        }
    )
    
    print(f"📊 ChromaDB initialized with {_collection.count()} documents")
    return _collection


def get_collection() -> chromadb.Collection:
    """Get the ChromaDB collection"""
    global _collection
    if _collection is None:
        raise RuntimeError("Vector database not initialized. Call init_vector_db() first.")
    return _collection


def get_client() -> chromadb.Client:
    """Get the ChromaDB client"""
    global _chroma_client
    if _chroma_client is None:
        raise RuntimeError("ChromaDB client not initialized.")
    return _chroma_client


async def add_documents(
    documents: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
    ids: List[str]
) -> bool:
    """Add documents to vector database"""
    try:
        collection = get_collection()
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        return True
    except Exception as e:
        print(f"Error adding documents: {e}")
        return False


async def query_documents(
    query_embedding: List[float],
    n_results: int = None,
    where: Dict = None,
    where_document: Dict = None
) -> Dict[str, Any]:
    """Query similar documents from vector database"""
    try:
        collection = get_collection()
        n_results = n_results or settings.TOP_K_RESULTS
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )
        
        return results
    except Exception as e:
        print(f"Error querying documents: {e}")
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


async def delete_documents(ids: List[str]) -> bool:
    """Delete documents by IDs"""
    try:
        collection = get_collection()
        collection.delete(ids=ids)
        return True
    except Exception as e:
        print(f"Error deleting documents: {e}")
        return False


async def get_document_count() -> int:
    """Get total document count"""
    try:
        collection = get_collection()
        return collection.count()
    except Exception:
        return 0


async def reset_database() -> bool:
    """Reset the entire vector database"""
    try:
        client = get_client()
        client.delete_collection(settings.CHROMA_COLLECTION_NAME)
        await init_vector_db()
        return True
    except Exception as e:
        print(f"Error resetting database: {e}")
        return False


async def get_all_documents(limit: int = 100) -> Dict[str, Any]:
    """Get all documents from the collection"""
    try:
        collection = get_collection()
        return collection.get(
            limit=limit,
            include=["documents", "metadatas"]
        )
    except Exception as e:
        print(f"Error getting documents: {e}")
        return {"ids": [], "documents": [], "metadatas": []}
