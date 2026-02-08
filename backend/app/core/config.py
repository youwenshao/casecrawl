"""
Application configuration using Pydantic Settings.
All sensitive config is loaded from environment variables.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find .env file in project root (parent of backend directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application
    app_name: str = "CaseCrawl"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/casecrawl",
        alias="DATABASE_URL"
    )
    
    # Redis (for Celery)
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    
    # Security
    secret_key: str = Field(default="change-me-in-production", alias="SECRET_KEY")
    
    # File Storage
    download_dir: str = Field(default="./data/downloads", alias="DOWNLOAD_DIR")
    file_retention_days: int = Field(default=30, alias="FILE_RETENTION_DAYS")
    
    # Westlaw Settings
    westlaw_base_url: str = Field(
        default="https://www.westlawasia.com",
        alias="WESTLAW_BASE_URL"
    )
    
    # Rate Limiting
    searches_per_minute: int = Field(default=4, alias="SEARCHES_PER_MINUTE")
    downloads_per_minute: int = Field(default=3, alias="DOWNLOADS_PER_MINUTE")
    max_concurrent_batches: int = Field(default=1, alias="MAX_CONCURRENT_BATCHES")
    
    # Browser Configuration
    browser_headless: bool = Field(default=False, alias="BROWSER_HEADLESS")
    browser_viewport_width: int = Field(default=1920, alias="BROWSER_VIEWPORT_WIDTH")
    browser_viewport_height: int = Field(default=1080, alias="BROWSER_VIEWPORT_HEIGHT")
    browser_locale: str = Field(default="en-GB", alias="BROWSER_LOCALE")
    browser_timezone: str = Field(default="Asia/Hong_Kong", alias="BROWSER_TIMEZONE")
    
    # Behavioral Delays (seconds)
    delay_between_actions_min: float = Field(default=3.0, alias="DELAY_BETWEEN_ACTIONS_MIN")
    delay_between_actions_max: float = Field(default=8.0, alias="DELAY_BETWEEN_ACTIONS_MAX")
    page_load_wait_min: float = Field(default=3.0, alias="PAGE_LOAD_WAIT_MIN")
    page_load_wait_max: float = Field(default=6.0, alias="PAGE_LOAD_WAIT_MAX")
    post_search_wait_min: float = Field(default=4.0, alias="POST_SEARCH_WAIT_MIN")
    post_search_wait_max: float = Field(default=7.0, alias="POST_SEARCH_WAIT_MAX")
    
    # Typing delays (ms)
    typing_delay_min: int = Field(default=50, alias="TYPING_DELAY_MIN")
    typing_delay_max: int = Field(default=150, alias="TYPING_DELAY_MAX")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    structured_logging: bool = Field(default=True, alias="STRUCTURED_LOGGING")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
