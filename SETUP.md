# CaseCrawl Setup Guide

This document provides detailed setup instructions for CaseCrawl on Mac, Windows, and Linux.

## Quick Setup (Recommended)

Choose the setup method that works best for your platform:

### Option 1: Python Script (Cross-platform)

Works on Mac, Windows, and Linux:

```bash
python setup.py
```

### Option 2: Shell Script (Mac/Linux)

```bash
chmod +x setup.sh
./setup.sh
```

### Option 3: Batch Script (Windows)

```cmd
setup.bat
```

### Option 4: Make (Mac/Linux with make installed)

```bash
make setup
```

## What the Setup Does

The automated setup scripts will:

1. **Check Prerequisites**: Verify Python 3.11+, Docker, and Node.js are installed
2. **Create Virtual Environment**: Set up Python venv in `./venv`
3. **Install Dependencies**:
   - Backend: FastAPI, SQLAlchemy, Celery, Playwright, etc.
   - Frontend: React, Vite, Tailwind CSS, etc.
4. **Install Playwright Browsers**: Download Chromium for web scraping
5. **Setup Environment**: Create `.env` file from template
6. **Start Docker Services**: PostgreSQL on port 15432, Redis on port 16379
7. **Create Database Tables**: Initialize the database schema

## Post-Setup: Starting Services

After setup completes, start the services in separate terminals:

### Terminal 1: Backend API
```bash
cd backend
../venv/bin/python -m uvicorn app.main:app --reload --port 18000
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

### Terminal 3: Celery Worker
```bash
cd backend
../venv/bin/python -m celery -A app.core.celery worker --loglevel=info
```

Or use Make to start all at once (Mac/Linux):
```bash
make docker-up  # Start Docker services
make dev        # Start backend
make dev-frontend  # Start frontend (new terminal)
make worker     # Start Celery (new terminal)
```

## Verification

Run the health check script to verify everything is working:

```bash
python healthcheck.py
```

This will check:
- Docker services (PostgreSQL, Redis)
- Database connectivity
- Redis connectivity
- Backend API health
- Frontend availability
- Celery worker status

## Access Points

Once all services are running:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:13000 | React dashboard |
| API Docs | http://localhost:18000/docs | Swagger UI |
| API | http://localhost:18000 | FastAPI endpoints |
| Flower | http://localhost:15555 | Celery monitoring |

## Manual Setup

If automated setup fails, follow these manual steps:

### 1. Prerequisites

- Python 3.11 or higher
- Docker Desktop
- Node.js 18 or higher
- Git

### 2. Clone Repository

```bash
git clone <repository-url>
cd casecrawl
```

### 3. Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
pip install "numpy<2"  # Compatibility fix

# Install Playwright browsers
python -m playwright install chromium
```

### 4. Frontend Setup

```bash
cd ../frontend
npm install
```

### 5. Environment Configuration

```bash
cd ..
cp .env.example .env
# Edit .env with your settings if needed
```

### 6. Docker Services

```bash
docker compose up -d db redis
```

### 7. Database Setup

```bash
cd backend
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings
from app.models import Base

async def setup():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('Database tables created!')

asyncio.run(setup())
"
```

## Troubleshooting

### Port Conflicts

CaseCrawl uses non-standard ports to avoid conflicts:
- PostgreSQL: **15432** (instead of 5432)
- Redis: **16379** (instead of 6379)
- Backend: **18000** (instead of 8000)
- Frontend: **13000** (instead of 3000)
- Flower: **15555** (instead of 5555)

### Docker Issues

**PostgreSQL authentication failed:**
```bash
# Reset Docker volumes
docker compose down -v
docker compose up -d db redis
```

**Port already allocated:**
```bash
# Find and stop conflicting services
lsof -ti:15432 | xargs kill -9
lsof -ti:16379 | xargs kill -9
```

### Python Issues

**NumPy compatibility error:**
```bash
pip install "numpy<2"
```

**Module not found errors:**
```bash
# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Frontend Issues

**npm install stuck or fails:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Rollup native module error (Mac):**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --target_arch=arm64 --target_platform=darwin
```

### Database Issues

**Tables not created:**
- Tables are auto-created when the backend starts
- Or run: `make migrate`

**Connection refused:**
- Ensure Docker is running: `docker compose up -d db redis`
- Wait 10 seconds for services to initialize
- Check `.env` has correct DATABASE_URL

## Development Commands

### Backend
```bash
# Run tests
make test

# Format code
make format

# Lint
make lint

# Database migration
make migrate
```

### Frontend
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker
```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Reset (WARNING: data loss)
docker compose down -v
```

### Celery
```bash
# Start worker
celery -A app.core.celery worker --loglevel=info

# Start beat (scheduler)
celery -A app.core.celery beat --loglevel=info

# Flower monitoring
celery -A app.core.celery flower --port=15555
```

## Platform-Specific Notes

### macOS

- Requires Xcode Command Line Tools: `xcode-select --install`
- Docker Desktop must be running
- May need to allow Playwright browser downloads in Security settings

### Windows

- Run PowerShell/Command Prompt as Administrator for Docker commands
- May need Windows Subsystem for Linux (WSL2) for Docker
- Use `setup.bat` or `python setup.py`

### Linux

- Install Docker using your distribution's package manager
- May need to add user to docker group: `sudo usermod -aG docker $USER`
- Log out and back in for group changes to take effect

## Getting Help

If you encounter issues:

1. Check the logs: `docker compose logs -f`
2. Run health check: `python healthcheck.py`
3. Review troubleshooting section above
4. Check GitHub Issues (if applicable)

## Next Steps

After successful setup:

1. Open http://localhost:13000
2. Upload a CSV file with case information
3. Monitor progress in the dashboard
4. Handle any ambiguous cases that require selection

See [README.md](README.md) for usage instructions and [API_REFERENCE.md](API_REFERENCE.md) for API documentation.
