"""
Performance Monitoring & Benchmarking API
Track response times and system health
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import statistics
import psutil

from app.core.config import settings
from app.services.llm_service import get_llm_service
from app.services.rag_service import get_rag_service
from app.services.cache_service import get_cache
from app.api.auth import get_current_user

router = APIRouter()


class BenchmarkResult(BaseModel):
    """Benchmark result model"""
    question: str
    response_time_ms: int
    cached: bool
    tokens_generated: Optional[int] = None
    model: str


class SystemMetrics(BaseModel):
    """System metrics model"""
    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float


# In-memory metrics storage (use TimescaleDB/InfluxDB for production)
_response_times: List[Dict] = []
_max_metrics = 1000


def record_response_time(time_ms: int, cached: bool, endpoint: str):
    """Record response time for monitoring"""
    global _response_times
    _response_times.append({
        "time_ms": time_ms,
        "cached": cached,
        "endpoint": endpoint,
        "timestamp": datetime.now().isoformat()
    })
    # Keep only last N records
    if len(_response_times) > _max_metrics:
        _response_times = _response_times[-_max_metrics:]


@router.get("/metrics")
async def get_performance_metrics():
    """Get performance metrics summary"""
    
    if not _response_times:
        return {
            "message": "No metrics recorded yet",
            "total_requests": 0
        }
    
    times = [r["time_ms"] for r in _response_times]
    cached_count = sum(1 for r in _response_times if r["cached"])
    
    return {
        "total_requests": len(_response_times),
        "cached_requests": cached_count,
        "cache_hit_rate": round(cached_count / len(_response_times) * 100, 2),
        "response_times": {
            "avg_ms": round(statistics.mean(times), 2),
            "median_ms": round(statistics.median(times), 2),
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": round(statistics.quantiles(times, n=20)[18], 2) if len(times) > 20 else max(times),
            "p99_ms": round(statistics.quantiles(times, n=100)[98], 2) if len(times) > 100 else max(times)
        },
        "last_hour": await _get_hourly_stats(),
        "system": await get_system_metrics()
    }


async def _get_hourly_stats() -> Dict:
    """Get stats for the last hour"""
    one_hour_ago = datetime.now() - timedelta(hours=1)
    recent = [
        r for r in _response_times 
        if datetime.fromisoformat(r["timestamp"]) > one_hour_ago
    ]
    
    if not recent:
        return {"requests": 0}
    
    times = [r["time_ms"] for r in recent]
    return {
        "requests": len(recent),
        "avg_ms": round(statistics.mean(times), 2),
        "under_10s": sum(1 for t in times if t < 10000),
        "under_10s_percent": round(sum(1 for t in times if t < 10000) / len(times) * 100, 2)
    }


@router.get("/system")
async def get_system_metrics() -> Dict[str, Any]:
    """Get current system resource usage"""
    
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Try to get GPU info
    gpu_info = None
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(', ')
            gpu_info = {
                "utilization_percent": int(parts[0]),
                "memory_used_mb": int(parts[1]),
                "memory_total_mb": int(parts[2]),
                "memory_percent": round(int(parts[1]) / int(parts[2]) * 100, 2)
            }
    except:
        pass
    
    return {
        "cpu_percent": cpu,
        "memory": {
            "percent": memory.percent,
            "used_gb": round(memory.used / (1024**3), 2),
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2)
        },
        "disk": {
            "percent": round(disk.used / disk.total * 100, 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2)
        },
        "gpu": gpu_info
    }


@router.post("/benchmark")
async def run_benchmark(
    questions: int = 5,
    use_cache: bool = False,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Run benchmark test
    
    - **questions**: Number of test questions (1-20)
    - **use_cache**: Whether to use cache (False for raw performance)
    """
    
    test_questions = [
        "Bagaimana cara cek tagihan air PDAM?",
        "Apa syarat untuk pemasangan baru sambungan air?",
        "Dimana lokasi loket pembayaran PDAM terdekat?",
        "Bagaimana cara melaporkan kebocoran pipa?",
        "Berapa tarif air PDAM per meter kubik?",
        "Apa saja dokumen yang diperlukan untuk balik nama?",
        "Bagaimana prosedur pengaduan gangguan air?",
        "Kapan jadwal pembacaan meter air?",
        "Berapa denda keterlambatan pembayaran?",
        "Bagaimana cara mengajukan keringanan tagihan?"
    ][:min(questions, 10)]
    
    rag_service = get_rag_service()
    results = []
    
    # Clear cache if not using it
    if not use_cache:
        cache = await get_cache()
        await cache.clear_responses()
    
    total_time = 0
    
    for question in test_questions:
        start = datetime.now()
        
        response = await rag_service.generate_answer(
            question=question,
            use_rag=True,
            use_cache=use_cache
        )
        
        elapsed_ms = response.get("time_ms", 0)
        total_time += elapsed_ms
        
        results.append(BenchmarkResult(
            question=question,
            response_time_ms=elapsed_ms,
            cached=response.get("cached", False),
            model=response.get("model", settings.OLLAMA_MODEL)
        ))
        
        # Record for metrics
        record_response_time(elapsed_ms, response.get("cached", False), "benchmark")
    
    # Calculate statistics
    times = [r.response_time_ms for r in results]
    cached_count = sum(1 for r in results if r.cached)
    under_10s = sum(1 for t in times if t < 10000)
    
    return {
        "benchmark_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "config": {
            "questions": len(test_questions),
            "use_cache": use_cache,
            "model": settings.OLLAMA_MODEL
        },
        "summary": {
            "total_time_ms": total_time,
            "avg_time_ms": round(total_time / len(results), 2),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "median_time_ms": round(statistics.median(times), 2),
            "cache_hits": cached_count,
            "cache_hit_rate": round(cached_count / len(results) * 100, 2),
            "under_10s_count": under_10s,
            "under_10s_percent": round(under_10s / len(results) * 100, 2)
        },
        "results": [r.dict() for r in results],
        "verdict": "✅ PASS" if under_10s / len(results) >= 0.9 else "❌ FAIL",
        "target": "90% responses under 10 seconds"
    }


@router.get("/cache")
async def get_cache_stats():
    """Get cache statistics"""
    cache = await get_cache()
    return await cache.get_stats()


@router.post("/cache/clear")
async def clear_cache(
    cache_type: str = "all",
    current_user: Dict = Depends(get_current_user)
):
    """
    Clear cache
    
    - **cache_type**: 'all', 'responses', 'embeddings', 'search'
    """
    cache = await get_cache()
    
    if cache_type == "all":
        await cache.clear_all()
        return {"message": "All cache cleared"}
    elif cache_type == "responses":
        await cache.clear_responses()
        return {"message": "Response cache cleared"}
    else:
        return {"message": f"Unknown cache type: {cache_type}"}


@router.get("/llm")
async def get_llm_status():
    """Get detailed LLM status"""
    llm = get_llm_service()
    health = await llm.health_check()
    
    return {
        "status": "healthy" if health.get("healthy") else "unhealthy",
        "details": health,
        "config": {
            "model": settings.OLLAMA_MODEL,
            "embedding_model": settings.OLLAMA_EMBEDDING_MODEL,
            "num_gpu": settings.OLLAMA_NUM_GPU,
            "num_thread": settings.OLLAMA_NUM_THREAD,
            "num_ctx": settings.OLLAMA_NUM_CTX,
            "temperature": settings.OLLAMA_TEMPERATURE
        }
    }


@router.post("/warmup")
async def warmup_llm(
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """Warmup LLM model for faster first response"""
    llm = get_llm_service()
    background_tasks.add_task(llm.warmup)
    return {"message": "Warmup started in background"}


@router.get("/report")
async def get_performance_report():
    """Get comprehensive performance report"""
    
    metrics = await get_performance_metrics()
    system = await get_system_metrics()
    cache_stats = await (await get_cache()).get_stats()
    llm_status = await get_llm_status()
    
    # Determine overall health
    issues = []
    
    if metrics.get("response_times", {}).get("avg_ms", 0) > 10000:
        issues.append("Average response time > 10 seconds")
    
    if cache_stats.get("memory_used_mb", 0) > 1800:  # 90% of 2GB
        issues.append("Redis memory usage high")
    
    if system.get("memory", {}).get("percent", 0) > 85:
        issues.append("System memory usage high")
    
    if system.get("gpu", {}).get("memory_percent", 0) > 90:
        issues.append("GPU memory usage high")
    
    return {
        "generated_at": datetime.now().isoformat(),
        "overall_status": "healthy" if not issues else "warning",
        "issues": issues,
        "performance": metrics,
        "system": system,
        "cache": cache_stats,
        "llm": llm_status,
        "recommendations": _get_recommendations(metrics, system, cache_stats)
    }


def _get_recommendations(metrics: Dict, system: Dict, cache: Dict) -> List[str]:
    """Generate performance recommendations"""
    recs = []
    
    avg_time = metrics.get("response_times", {}).get("avg_ms", 0)
    cache_hit = metrics.get("cache_hit_rate", 0)
    
    if avg_time > 15000:
        recs.append("🔴 Response time very slow. Consider upgrading GPU or using smaller model.")
    elif avg_time > 10000:
        recs.append("🟡 Response time above target. Enable caching or optimize prompts.")
    
    if cache_hit < 50:
        recs.append("📈 Low cache hit rate. Consider longer cache TTL or preloading common queries.")
    
    gpu = system.get("gpu")
    if not gpu:
        recs.append("⚠️ No GPU detected. Install NVIDIA GPU for 10-20x faster inference.")
    elif gpu.get("utilization_percent", 0) < 30:
        recs.append("💡 GPU underutilized. Consider enabling more parallel requests.")
    
    if system.get("memory", {}).get("percent", 0) > 80:
        recs.append("🔴 High memory usage. Consider adding more RAM.")
    
    if not recs:
        recs.append("✅ System performing optimally!")
    
    return recs
