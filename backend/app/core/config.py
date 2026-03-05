"""
PDAM Chatbot AI - Optimized Configuration
Enterprise-grade settings for < 10 second response time
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """High-performance application settings"""
    
    # === Application ===
    APP_NAME: str = "PDAM Chatbot AI"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 8  # Increased for high concurrency
    
    # === Security ===
    SECRET_KEY: str = "pdam-chatbot-secret-key-change-in-production-2024"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # === PDAM Auth ===
    PDAM_AUTH_API_URL: str = "https://gateway.pdamkotasmg.co.id/api-gw/portal-pegawai/api/auth"
    PDAM_AUTH_TIMEOUT: int = 10
    
    # === CORS ===
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://pdamkotasmg.co.id",
        "https://*.pdamkotasmg.co.id",
    ]
    
    # === Redis Cache (CRITICAL for speed!) ===
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_TTL_EMBEDDINGS: int = 86400  # 24 hours
    REDIS_TTL_RESPONSES: int = 3600    # 1 hour
    REDIS_TTL_DOCUMENTS: int = 86400   # 24 hours
    CACHE_ENABLED: bool = True
    
    # === Ollama LLM - GPU Optimized ===
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"  # atau mistral:7b untuk kualitas
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TIMEOUT: int = 60  # Reduced with GPU
    OLLAMA_NUM_CTX: int = 4096  # Context window
    OLLAMA_NUM_GPU: int = 99  # Use all GPU layers
    OLLAMA_NUM_THREAD: int = 16  # CPU threads
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_TOP_P: float = 0.9
    OLLAMA_TOP_K: int = 40
    OLLAMA_REPEAT_PENALTY: float = 1.1
    
    # === Vector Database - Optimized ===
    CHROMA_PERSIST_DIR: str = "./vectordb"
    CHROMA_COLLECTION_NAME: str = "pdam_documents"
    
    # === Milvus (Alternative - Faster for large scale) ===
    MILVUS_ENABLED: bool = False
    MILVUS_HOST: str = "milvus"
    MILVUS_PORT: int = 19530
    
    # === Document Processing ===
    UPLOAD_DIR: str = "./documents/uploads"
    PROCESSED_DIR: str = "./documents/processed"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: List[str] = [
        ".pdf", ".doc", ".docx", 
        ".xls", ".xlsx", 
        ".txt", ".md",
        ".jpg", ".jpeg", ".png", ".gif", ".webp"
    ]
    
    # === RAG Settings - Optimized ===
    CHUNK_SIZE: int = 512  # Smaller chunks = faster search
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 3  # Reduced for speed
    SIMILARITY_THRESHOLD: float = 0.75
    
    # === Embedding Batch ===
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_PARALLEL: bool = True
    
    # === Connection Pooling ===
    HTTP_POOL_SIZE: int = 100
    HTTP_POOL_MAXSIZE: int = 100
    HTTP_POOL_TIMEOUT: int = 30
    
    # === Rate Limiting ===
    RATE_LIMIT_REQUESTS: int = 200
    RATE_LIMIT_WINDOW: int = 60
    
    # === Logging ===
    LOG_LEVEL: str = "WARNING"  # Reduce logging overhead
    LOG_FILE: str = "./logs/app.log"
    
    # === Performance Monitoring ===
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# === Optimized System Prompt (Shorter = Faster) ===
SYSTEM_PROMPT = """Kamu adalah asisten AI PDAM Tirta Moedal Kota Semarang.

TUGAS: Jawab pertanyaan pelanggan tentang layanan PDAM dengan akurat dan singkat.

ATURAN:
1. Gunakan Bahasa Indonesia yang sopan
2. Jawab berdasarkan konteks yang diberikan
3. Jika tidak yakin, sarankan hubungi (024) 8311113
4. Gunakan emoji yang sesuai (💧✅❌📞)

Jawab dengan SINGKAT dan JELAS."""


RAG_PROMPT_TEMPLATE = """Konteks:
{context}

Pertanyaan: {question}

Jawab singkat dan akurat:"""
