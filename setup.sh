#!/bin/bash
# CaseCrawl Quickstart Setup Script for Mac/Linux
# Run: chmod +x setup.sh && ./setup.sh

set -e

echo "==================================="
echo "CaseCrawl Setup (Mac/Linux)"
echo "==================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${BLUE}Checking prerequisites...${NC}"
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python 3 is required but not installed.${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}npm is required but not installed.${NC}"; exit 1; }

echo -e "${GREEN}✓ All prerequisites found${NC}"

# Get script directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Create virtual environment
echo -e "\n${BLUE}Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip -q

# Install numpy first (compatibility fix)
echo -e "\n${BLUE}Installing NumPy (compatibility version)...${NC}"
pip install "numpy<2" --quiet

# Install backend dependencies
echo -e "\n${BLUE}Installing backend dependencies...${NC}"
pip install -r backend/requirements.txt --quiet

# Install Playwright browsers
echo -e "\n${BLUE}Installing Playwright browsers...${NC}"
python -m playwright install chromium

echo -e "${GREEN}✓ Backend setup complete${NC}"

# Setup frontend
echo -e "\n${BLUE}Setting up frontend...${NC}"
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..

echo -e "${GREEN}✓ Frontend setup complete${NC}"

# Create .env if not exists
echo -e "\n${BLUE}Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi

# Start Docker services
echo -e "\n${BLUE}Starting Docker services...${NC}"
if docker compose version >/dev/null 2>&1; then
    docker compose up -d db redis
else
    docker-compose up -d db redis
fi

echo -e "${GREEN}✓ Docker services started${NC}"

# Wait for PostgreSQL
echo -e "\n${BLUE}Waiting for PostgreSQL...${NC}"
sleep 5

# Create database tables
echo -e "\n${BLUE}Creating database tables...${NC}"
cd backend
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
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
" 2>/dev/null || echo -e "${YELLOW}Tables will be created on first app start${NC}"

cd ..

echo -e "\n${GREEN}===================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}===================================${NC}"

echo -e "\n${BLUE}To start the application:${NC}"
echo ""
echo "1. Start the backend API:"
echo "   cd backend"
echo "   ../venv/bin/python -m uvicorn app.main:app --reload --port 18000"
echo ""
echo "2. Start the frontend (new terminal):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Start Celery worker (new terminal):"
echo "   cd backend"
echo "   ../venv/bin/python -m celery -A app.core.celery worker --loglevel=info"
echo ""
echo -e "${BLUE}Access Points:${NC}"
echo "  - Frontend: http://localhost:13000"
echo "  - API Docs: http://localhost:18000/docs"
echo ""
