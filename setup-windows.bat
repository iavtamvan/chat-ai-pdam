@echo off
REM ============================================
REM PDAM Chatbot AI - Optimized Setup for Windows
REM High Performance with GPU + Redis
REM ============================================

title PDAM Chatbot AI - Optimized Setup
color 0A

echo.
echo ========================================================
echo    PDAM Chatbot AI - Optimized Performance Setup
echo    Target: Response Time ^< 10 detik
echo ========================================================
echo.

REM Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] Tidak running sebagai Administrator
    echo Beberapa fitur mungkin tidak berfungsi optimal
    echo.
)

REM Check Docker
echo [1/8] Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker tidak running!
    echo.
    echo Silakan:
    echo 1. Buka Docker Desktop
    echo 2. Tunggu sampai status "Running"
    echo 3. Jalankan script ini lagi
    echo.
    pause
    exit /b 1
)
echo       [OK] Docker running

REM Check NVIDIA GPU
echo [2/8] Checking GPU...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo       [WARNING] NVIDIA GPU tidak terdeteksi
    echo       Response time akan lebih lambat tanpa GPU
    set HAS_GPU=0
) else (
    echo       [OK] NVIDIA GPU detected
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    set HAS_GPU=1
)
echo.

REM Create .env if not exists
echo [3/8] Creating configuration...
if not exist ".env" (
    echo SECRET_KEY=pdam-chatbot-secret-%RANDOM%-%RANDOM%> .env
    echo ENVIRONMENT=production>> .env
    echo OLLAMA_MODEL=llama3.2:3b>> .env
    echo OLLAMA_EMBEDDING_MODEL=nomic-embed-text>> .env
    echo OLLAMA_NUM_GPU=99>> .env
    echo CACHE_ENABLED=true>> .env
    echo       [OK] .env created
) else (
    echo       [OK] .env already exists
)

REM Create directories
echo [4/8] Creating directories...
if not exist "backend\documents\uploads" mkdir backend\documents\uploads
if not exist "backend\documents\processed" mkdir backend\documents\processed
if not exist "backend\vectordb" mkdir backend\vectordb
if not exist "backend\logs" mkdir backend\logs
echo       [OK] Directories ready

REM Pull Docker images
echo [5/8] Pulling Docker images (this may take a while)...
docker compose pull redis
docker compose pull ollama/ollama:latest
echo       [OK] Images pulled

REM Start Redis first
echo [6/8] Starting Redis cache...
docker compose up -d redis
timeout /t 5 /nobreak >nul
echo       [OK] Redis started

REM Start Ollama with GPU
echo [7/8] Starting Ollama with GPU...
if %HAS_GPU%==1 (
    docker compose up -d ollama
) else (
    echo       [INFO] Starting without GPU support
    docker compose up -d ollama
)
echo       Waiting for Ollama to be ready...
timeout /t 30 /nobreak >nul

REM Check Ollama health
:check_ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo       Still waiting...
    timeout /t 10 /nobreak >nul
    goto check_ollama
)
echo       [OK] Ollama ready

REM Download models
echo [8/8] Downloading AI models...
echo       This may take 10-30 minutes depending on internet speed
echo.
echo       Downloading llama3.2:3b (2GB)...
docker exec pdam-ollama ollama pull llama3.2:3b
echo       [OK] Chat model ready
echo.
echo       Downloading nomic-embed-text (300MB)...
docker exec pdam-ollama ollama pull nomic-embed-text
echo       [OK] Embedding model ready

REM Start all services
echo.
echo Starting all services...
docker compose up -d backend frontend

REM Wait for backend
echo Waiting for backend to be ready...
timeout /t 20 /nobreak >nul

:check_backend
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo Still starting...
    timeout /t 5 /nobreak >nul
    goto check_backend
)

REM Warmup
echo.
echo Running model warmup for faster first response...
curl -s -X POST http://localhost:8000/api/monitoring/warmup >nul 2>&1

echo.
echo ========================================================
echo    SETUP COMPLETE!
echo ========================================================
echo.
echo    Frontend:     http://localhost:3000
echo    API Docs:     http://localhost:8000/api/docs
echo    Monitoring:   http://localhost:8000/api/monitoring/metrics
echo    Benchmark:    http://localhost:8000/api/monitoring/benchmark
echo.
echo    Commands:
echo    - Start:   docker compose up -d
echo    - Stop:    docker compose down
echo    - Logs:    docker compose logs -f
echo    - Status:  docker compose ps
echo.
echo ========================================================
echo.
echo Press any key to open the chatbot in browser...
pause >nul
start http://localhost:3000
