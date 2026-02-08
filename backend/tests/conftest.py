"""
Pytest configuration and fixtures.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import BatchJob, CaseJob, CrawlerSession, SearchResultCache

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create a test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_citations():
    """Sample citations for testing."""
    return {
        "hk_cfci": "[2020] HKCFI 123",
        "hk_ca": "[2019] HKCA 456",
        "hk_cfa": "[2021] HKCFA 789",
        "uk_sc": "[2020] UKSC 15",
        "uk_hl": "[2005] UKHL 25",
        "wlr": "[2020] 1 WLR 456",
        "wlr_periods": "[2020] 1 W.L.R. 456",
    }


@pytest.fixture
def sample_party_names():
    """Sample party names for testing."""
    return {
        "simple": "Smith v Jones",
        "regina": "Regina v Smith",
        "hsbc": "HSBC Bank Plc v Jones",
        "multi": "John Paul Smith v Mary Jane Jones",
    }
