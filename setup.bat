@echo off
REM CaseCrawl Quickstart Setup Script for Windows
REM Run: setup.bat

echo ===================================
echo CaseCrawl Setup (Windows)
echo ===================================

REM Check prerequisites
echo.
echo Checking prerequisites...

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is required but not installed.
    exit /b 1
)

docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is required but not installed.
    exit /b 1
)

npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm is required but not installed.
    exit /b 1
)

echo [OK] All prerequisites found

REM Get script directory
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

REM Create virtual environment
echo.
echo Setting up Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [WARNING] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip -q

REM Install numpy first (compatibility fix)
echo.
echo Installing NumPy (compatibility version)...
pip install "numpy<2" --quiet

REM Install backend dependencies
echo.
echo Installing backend dependencies...
pip install -r backend\requirements.txt --quiet

REM Install Playwright browsers
echo.
echo Installing Playwright browsers...
python -m playwright install chromium

echo [OK] Backend setup complete

REM Setup frontend
echo.
echo Setting up frontend...
cd frontend
if exist "node_modules" rmdir /s /q node_modules
if exist "package-lock.json" del package-lock.json
npm install
cd ..

echo [OK] Frontend setup complete

REM Create .env if not exists
echo.
echo Setting up environment...
if not exist ".env" (
    copy .env.example .env
    echo [OK] Created .env file
) else (
    echo [WARNING] .env file already exists
)

REM Start Docker services
echo.
echo Starting Docker services...
docker compose up -d db redis 2>nul
if errorlevel 1 (
    docker-compose up -d db redis
)

echo [OK] Docker services started

REM Wait for PostgreSQL
echo.
echo Waiting for PostgreSQL...
timeout /t 5 /nobreak >nul

REM Create database tables
echo.
echo Creating database tables...
cd backend
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings
from app.models import Base

async def setup():
    try:
        settings = get_settings()
        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()
        print('Database tables created!')
    except Exception as e:
        print(f'Note: {e}')
        print('Tables will be created on first app start')

asyncio.run(setup())
"
cd ..

echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo To start the application:
echo.
echo 1. Start the backend API:
echo    cd backend
echo    ..\venv\Scripts\python -m uvicorn app.main:app --reload --port 18000
echo.
echo 2. Start the frontend (new terminal):
echo    cd frontend
echo    npm run dev
echo.
echo 3. Start Celery worker (new terminal):
echo    cd backend
echo    ..\venv\Scripts\python -m celery -A app.core.celery worker --loglevel=info
echo.
echo Access Points:
echo   - Frontend: http://localhost:13000
echo   - API Docs: http://localhost:18000/docs
echo.

pause
