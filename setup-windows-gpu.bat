@echo off
echo ========================================
echo Configuracion para Windows con GPU
echo ========================================
echo.

echo Verificando requisitos del sistema...
echo.

REM Check if Docker Desktop is running
echo [1/5] Verificando Docker Desktop...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Desktop no esta instalado o no esta ejecutandose
    echo Por favor instala Docker Desktop desde: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)
echo ✓ Docker Desktop detectado

REM Check if NVIDIA Docker is available
echo [2/5] Verificando soporte NVIDIA Docker...
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo ADVERTENCIA: NVIDIA Docker no esta configurado
    echo Esto puede afectar el rendimiento de GPU
    echo Para configurar NVIDIA Docker:
    echo 1. Instala NVIDIA Container Toolkit
    echo 2. Reinicia Docker Desktop
    echo.
    set /p continue="¿Continuar sin GPU? (s/n): "
    if /i not "%continue%"=="s" (
        echo Configuracion cancelada
        pause
        exit /b 1
    )
) else (
    echo ✓ NVIDIA Docker configurado correctamente
)

REM Create necessary directories
echo [3/5] Creando directorios necesarios...
if not exist "backend\uploads" mkdir "backend\uploads"
if not exist "backend\models" mkdir "backend\models"
if not exist "backend\cache" mkdir "backend\cache"
if not exist "backend\logs" mkdir "backend\logs"
echo ✓ Directorios creados

REM Check if .env file exists
echo [4/5] Verificando archivo de configuracion...
if not exist ".env" (
    echo Creando archivo .env de ejemplo...
    (
        echo # Configuracion para Windows con GPU
        echo GEMINI_API_KEY=tu_api_key_aqui
        echo.
        echo # Firebase Configuration
        echo FIREBASE_PROJECT_ID=proyectoshergon
        echo FIREBASE_PRIVATE_KEY_ID=
        echo FIREBASE_PRIVATE_KEY=
        echo FIREBASE_CLIENT_EMAIL=
        echo FIREBASE_CLIENT_ID=
        echo FIREBASE_CLIENT_X509_CERT_URL=
        echo.
        echo # LangChain ^(opcional^)
        echo LANGSMITH_API_KEY=
        echo LANGCHAIN_PROJECT=
        echo LANGSMITH_ENDPOINT=
    ) > .env
    echo ✓ Archivo .env creado
    echo IMPORTANTE: Edita el archivo .env y agrega tu GEMINI_API_KEY
) else (
    echo ✓ Archivo .env encontrado
)

REM Build and start services
echo [5/5] Construyendo y ejecutando servicios...
echo.
echo Iniciando servicios con soporte GPU...
docker-compose up --build -d

echo.
echo ========================================
echo Configuracion completada
echo ========================================
echo.
echo Servicios disponibles:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - Health Check: http://localhost:8000/health
echo.
echo Para ver logs en tiempo real:
echo docker-compose logs -f
echo.
echo Para detener servicios:
echo docker-compose down
echo.
pause
