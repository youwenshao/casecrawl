# CaseCrawl

Ethical web crawler for Westlaw Asia with human-in-the-loop disambiguation, fuzzy citation matching, and comprehensive anti-detection measures.

## Features

- **Smart Citation Parsing**: Supports HK and UK citation formats with fuzzy matching
- **4-Step Search Strategy**: Exact → Year Range → Party Only → Fail
- **Human-in-the-Loop**: Disambiguation interface for ambiguous results
- **Anti-Detection**: Playwright with stealth plugins, human-like behavior
- **Rate Limiting**: Configurable limits to avoid blocking
- **Real-time Updates**: WebSocket progress tracking
- **Civil Procedure Detection**: Automatic blocking with manual review requirement

## Quick Start

### Prerequisites

- Python 3.11+
- Docker Desktop
- Node.js 18+

### Automated Setup (Recommended)

**Mac/Linux:**
```bash
git clone <repository-url>
cd casecrawl
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
git clone <repository-url>
cd casecrawl
setup.bat
```

**Cross-platform (Python):**
```bash
git clone <repository-url>
cd casecrawl
python setup.py
```

### Manual Setup

If you prefer manual setup or the automated script doesn't work:

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 3. Install dependencies
cd backend
pip install -r requirements.txt
pip install "numpy<2"  # Compatibility fix
playwright install chromium

# 4. Setup frontend
cd ../frontend
npm install

# 5. Copy environment file
cd ..
cp .env.example .env

# 6. Start Docker services
docker compose up -d db redis

# 7. Create database tables
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
    print('Done!')

asyncio.run(setup())
"
```

### Running the Application

Start all services in separate terminals:

**Terminal 1 - Backend API:**
```bash
cd backend
../venv/bin/python -m uvicorn app.main:app --reload --port 18000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Celery Worker:**
```bash
cd backend
../venv/bin/python -m celery -A app.core.celery worker --loglevel=info
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:13000 |
| API Docs | http://localhost:18000/docs |
| Flower (Celery) | http://localhost:15555 |

## Usage

1. Open http://localhost:13000
2. Upload a CSV file with case information:
   ```csv
   party_name,citation,notes
   "Smith v Jones","[2020] HKCFI 123","Important case"
   ```
3. Monitor progress in real-time
4. Handle ambiguous cases through the disambiguation interface
5. Download completed cases

## API Documentation

See [API_REFERENCE.md](API_REFERENCE.md) for complete API documentation.

## Citation Formats Supported

### Hong Kong
- `[2020] HKCFI 123` - Court of First Instance
- `[2019] HKCA 456` - Court of Appeal
- `[2021] HKCFA 789` - Court of Final Appeal
- `[2020] 1 HKLRD 100` - Hong Kong Law Reports

### United Kingdom
- `[2020] UKSC 15` - Supreme Court
- `[2019] UKHL 25` - House of Lords
- `[2020] EWCA 100` - Court of Appeal
- `[2020] 1 WLR 456` - Weekly Law Reports
- `[2020] 2 AC 100` - Appeal Cases

## Project Structure

```
casecrawl/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Config, logging, constants
│   │   ├── db/            # Database models and session
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   │   ├── westlaw_client.py   # Playwright scraper
│   │   │   ├── search.py           # Search strategies
│   │   │   └── tasks.py            # Celery tasks
│   │   └── utils/         # Citation parser, party names
│   └── tests/
├── frontend/              # React dashboard
├── docker-compose.yml
├── setup.py              # Cross-platform setup script
├── setup.sh              # Mac/Linux setup script
├── setup.bat             # Windows setup script
└── README.md
```

## Development

### Running Tests

```bash
cd backend
pytest tests/ -v
```

### Useful Commands

```bash
# Stop Docker services
docker compose down

# View logs
docker compose logs -f

# Run Celery beat (scheduled tasks)
celery -A app.core.celery beat --loglevel=info

# Flower monitoring
celery -A app.core.celery flower --port=5555
```

## Troubleshooting

### Port Already in Use

If you see "port already allocated" errors, the services are configured to use non-standard ports:
- PostgreSQL: 15432 (instead of 5432)
- Redis: 16379 (instead of 6379)
- Backend: 18000 (instead of 8000)
- Frontend: 13000 (instead of 3000)

### Database Connection Issues

If you get authentication errors:
```bash
# Reset Docker volumes
docker compose down -v
docker compose up -d db redis
```

### NumPy Compatibility

If you see NumPy version errors:
```bash
pip install "numpy<2"
```

### Frontend Build Issues

If npm install fails:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## License

[License information]

## Disclaimer

This tool is for educational and ethical use only. Users must:
- Have valid Westlaw credentials
- Comply with Westlaw's Terms of Service
- Respect rate limits and anti-detection measures
- Use downloaded content in accordance with copyright law
