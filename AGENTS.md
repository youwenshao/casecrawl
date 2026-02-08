# CaseCrawl - AI Agent Documentation

This document provides essential information for AI coding agents working on the CaseCrawl project. CaseCrawl is an ethical web crawler for Westlaw Asia with human-in-the-loop disambiguation, fuzzy citation matching, and comprehensive anti-detection measures.

## Project Overview

CaseCrawl is a full-stack application designed to crawl legal case documents from Westlaw Asia. It features:

- **Smart Citation Parsing**: Supports Hong Kong and UK citation formats with fuzzy matching
- **4-Step Search Strategy**: Exact → Year Range → Party Only → Fail
- **Human-in-the-Loop**: Disambiguation interface for ambiguous results
- **Anti-Detection**: Playwright with stealth plugins and human-like behavior
- **Rate Limiting**: Configurable limits to avoid blocking
- **Real-time Updates**: WebSocket progress tracking

## Technology Stack

### Backend (Python)
- **Framework**: FastAPI 0.110+ with Uvicorn
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Task Queue**: Celery 5.3+ with Redis
- **Web Scraping**: Playwright 1.41+ with playwright-stealth
- **Data Processing**: Pandas, openpyxl
- **Logging**: structlog
- **Testing**: pytest, pytest-asyncio

### Frontend (TypeScript/React)
- **Framework**: React 18 with TypeScript 5.2+
- **Build Tool**: Vite 5.0+
- **Styling**: Tailwind CSS 3.4+
- **Routing**: React Router DOM 6.21+
- **State Management**: TanStack Query (React Query) 5.17+
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Icons**: Lucide React

### Infrastructure
- **Database**: PostgreSQL 15 (port 15432)
- **Cache/Task Queue**: Redis 7 (port 16379)
- **Containerization**: Docker Compose
- **Process Monitoring**: Flower (Celery monitoring on port 15555)

## Directory Structure

```
casecrawl/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints (batches, cases, sessions, websocket)
│   │   ├── core/              # Config, logging, constants, Celery config
│   │   ├── db/                # Database base model and session
│   │   ├── models/            # SQLAlchemy models (BatchJob, CaseJob, SearchResultCache, CrawlerSession)
│   │   ├── schemas/           # Pydantic schemas for request/response
│   │   ├── services/          # Business logic (WestlawClient, SearchService, tasks)
│   │   ├── utils/             # Utilities (citation_parser, party_names)
│   │   └── main.py            # FastAPI application entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container image
│   └── pytest.ini            # Test configuration
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── hooks/             # Custom React hooks (useWebSocket)
│   │   ├── pages/             # Page components (BatchUpload, Dashboard, Disambiguation)
│   │   ├── types/             # TypeScript type definitions
│   │   ├── utils/             # API client and utilities
│   │   ├── App.tsx            # Main application component
│   │   ├── main.tsx           # Application entry point
│   │   └── index.css          # Global styles with Tailwind
│   ├── package.json           # Node dependencies
│   ├── tsconfig.json          # TypeScript configuration
│   ├── vite.config.ts         # Vite configuration
│   └── tailwind.config.js     # Tailwind CSS configuration
├── data/downloads/            # Downloaded case files
├── logs/                      # Application logs
├── docker-compose.yml         # Docker services configuration
├── Makefile                   # Development commands
├── setup.py                   # Cross-platform setup script
├── setup.sh                   # Unix setup script
├── setup.bat                  # Windows setup script
├── healthcheck.py             # Service health verification
├── .env.example               # Environment template
└── .env                       # Local environment (not in git)
```

## Build and Development Commands

### Initial Setup
```bash
# Automated setup (recommended)
python setup.py
# OR
./setup.sh          # Mac/Linux
setup.bat           # Windows

# Manual setup
cd backend && pip install -r requirements.txt && pip install "numpy<2" && playwright install chromium
cd ../frontend && npm install
cd .. && cp .env.example .env
docker compose up -d db redis
```

### Development (requires 3 terminals)
```bash
# Terminal 1: Backend API
cd backend
../venv/bin/python -m uvicorn app.main:app --reload --port 18000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Celery Worker
cd backend
../venv/bin/python -m celery -A app.core.celery worker --loglevel=info
```

### Make Commands
```bash
make setup              # Run automated setup
make install            # Install backend dependencies
make install-frontend   # Install frontend dependencies
make dev                # Start backend dev server
make dev-frontend       # Start frontend dev server
make worker             # Start Celery worker
make flower             # Start Flower monitoring
make docker-up          # Start Docker services
make docker-down        # Stop Docker services
make migrate            # Run database migrations
make test               # Run backend tests
make lint               # Run linters
make format             # Format code
make clean              # Clean generated files
```

### NPM Commands (frontend)
```bash
cd frontend
npm run dev             # Development server (port 13000)
npm run build           # Production build
npm run preview         # Preview production build
npm run lint            # Run ESLint
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Critical settings
DEBUG=true                                    # Enable debug mode
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:15432/casecrawl
REDIS_URL=redis://localhost:16379/0
SECRET_KEY=your-secret-key-change-in-production
DOWNLOAD_DIR=./data/downloads

# Westlaw scraping behavior
SEARCHES_PER_MINUTE=4
DOWNLOADS_PER_MINUTE=3
BROWSER_HEADLESS=false                        # Set true for headless mode
DELAY_BETWEEN_ACTIONS_MIN=3.0
DELAY_BETWEEN_ACTIONS_MAX=8.0
```

## Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:13000 | React dashboard |
| API | http://localhost:18000/api/v1 | FastAPI endpoints |
| API Docs | http://localhost:18000/docs | Swagger UI (debug only) |
| Flower | http://localhost:15555 | Celery monitoring |
| PostgreSQL | localhost:15432 | Database |
| Redis | localhost:16379 | Cache/Queue |

## API Structure

### Main Routes (`/api/v1`)

**Batches** (`/batches`)
- `POST /` - Upload CSV/Excel file with case information
- `GET /{batch_id}` - Get batch details
- `GET /{batch_id}/statistics` - Get batch statistics
- `GET /{batch_id}/cases` - List cases in batch

**Cases** (`/cases`)
- `GET /{case_id}` - Get case details
- `GET /{case_id}/search-results` - Get search results for disambiguation
- `POST /{case_id}/select` - Select a search result
- `POST /{case_id}/force-manual` - Force manual review
- `GET /{case_id}/download` - Download case document

**Sessions** (`/sessions`)
- `POST /` - Create Westlaw session (login)
- `GET /{session_id}/health` - Check session health

**WebSocket** (`/ws/batch-progress`)
- Real-time updates for case processing

## Database Models

### CaseJob
Individual case crawling job with fields:
- `party_names_raw` / `party_names_normalized` - Party name information
- `citation_raw` / `citation_normalized` - Citation data
- `year_extracted` / `jurisdiction` - Extracted metadata
- `status` - CaseStatus enum (pending, searching, ambiguous, etc.)
- `search_results` - JSONB array of potential matches
- `civil_procedure_flag` - Blocks automatic download
- `file_path` / `file_name` - Downloaded document location

### BatchJob
Collection of cases to process:
- `total_cases`, `completed_cases_count`, `error_cases_count`
- `auto_download_exact_matches` - Auto-download setting
- `status` - BatchStatus enum

### SearchResultCache
Cached search results from Westlaw:
- `westlaw_citation`, `parties_display`, `principal_subject`
- `available_documents` - PDF, transcript, analysis flags
- `citation_match_type` - exact, similar_volume, year_match_only

### CrawlerSession
Westlaw authentication session:
- `cookies` - Session cookies
- `status` - active, expired, captcha_blocked

## Key Constants

Located in `backend/app/core/constants.py`:

```python
# Search strategies (4-step approach)
SearchStrategy.EXACT        # Full citation match
SearchStrategy.YEAR_RANGE   # Year ±1 with parties
SearchStrategy.PARTY_ONLY   # Party names only
SearchStrategy.FAILED       # No results found

# Case statuses
CaseStatus.PENDING, CaseStatus.SEARCHING, CaseStatus.AMBIGUOUS
CaseStatus.AWAITING_SELECTION, CaseStatus.CIVIL_PROCEDURE_BLOCKED
CaseStatus.COMPLETED, CaseStatus.ERROR

# Citation patterns (regex)
HK: r"\[(\d{4})\]\s*(HKCFI|HKCA|HKCFA|...)\s*(\d+)"
UK: r"\[(\d{4})\]\s*(UKSC|UKHL|EWCA|...)\s*(\d+)"
```

## Testing

### Backend Tests
```bash
cd backend
../venv/bin/python -m pytest tests/ -v
```

Test files:
- `tests/test_citation_parser.py` - Citation parsing tests
- `tests/test_party_names.py` - Party name normalization tests
- `tests/conftest.py` - Pytest fixtures (async DB sessions)

### Frontend Tests
No frontend tests are currently configured, but ESLint is available:
```bash
cd frontend
npm run lint
```

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8
- Use type hints throughout
- Use `async/await` for async code
- Use SQLAlchemy 2.0 style (Mapped, mapped_column)
- Use Pydantic v2 for schemas
- Use structlog for structured logging

Example:
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

class MyModel(Base):
    __tablename__ = "my_table"
    
    id: Mapped[str] = mapped_column(UUID, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
```

### TypeScript (Frontend)
- Strict TypeScript configuration enabled
- Use functional components with hooks
- Prefer `const` and `let` over `var`
- Use TypeScript interfaces for props and state

Example:
```typescript
interface MyComponentProps {
  batchId: string
  onComplete?: () => void
}

const MyComponent: React.FC<MyComponentProps> = ({ batchId, onComplete }) => {
  // Component logic
}
```

## Development Workflow

1. **Start infrastructure**: `make docker-up`
2. **Run backend**: `make dev` (Terminal 1)
3. **Run frontend**: `make dev-frontend` (Terminal 2)
4. **Run worker**: `make worker` (Terminal 3)
5. **Verify**: Run `python healthcheck.py`

### Making Changes

**Backend changes**:
- Models in `backend/app/models/`
- API endpoints in `backend/app/api/`
- Business logic in `backend/app/services/`
- Database migrations via Alembic (if needed)

**Frontend changes**:
- Pages in `frontend/src/pages/`
- Components in `frontend/src/components/`
- API calls in `frontend/src/utils/api.ts`
- Types in `frontend/src/types/index.ts`

**Configuration changes**:
- Add to `.env` and `backend/app/core/config.py`
- Document in `.env.example`

## Security Considerations

1. **Never commit `.env` files** - Contains secrets
2. **Westlaw credentials** - Users must provide their own valid credentials
3. **Rate limiting** - Configured to respect Westlaw's limits
4. **File downloads** - Stored in `data/downloads/` (not version controlled)
5. **Session management** - Crawler sessions expire after 8 hours
6. **Civil Procedure detection** - Prevents automatic download of flagged cases

## Troubleshooting

### Port Conflicts
CaseCrawl uses non-standard ports to avoid conflicts:
- PostgreSQL: 15432 (not 5432)
- Redis: 16379 (not 6379)
- Backend: 18000 (not 8000)
- Frontend: 13000 (not 3000)

### Common Issues

**Database connection failed**:
```bash
docker compose down -v
docker compose up -d db redis
```

**NumPy compatibility error**:
```bash
pip install "numpy<2"
```

**Frontend build issues**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Worker not processing tasks**:
- Check Redis connection: `redis-cli -p 16379 ping`
- Verify Celery is running: `celery -A app.core.celery inspect active`
- Check Flower at http://localhost:15555

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

## Additional Resources

- `README.md` - User-facing documentation
- `SETUP.md` - Detailed setup instructions
- `API_REFERENCE.md` - Complete API documentation
- `healthcheck.py` - Service verification script
