"""
The Lineup - Application Configuration
Centralized configuration management using Pydantic settings.
"""

from pydantic import BaseSettings, validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application Settings
    APP_NAME: str = "The Lineup API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str
    
    # Database Configuration
    DATABASE_URL: str
    DATABASE_URL_SYNC: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Authentication Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    
    # NBA API Configuration
    NBA_STATS_API_BASE_URL: str = "https://stats.nba.com"
    NBA_API_RATE_LIMIT_DELAY: float = 1.0
    
    # CORS Settings
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def cors_origins(self) -> List[str]:
        """Get parsed CORS origins."""
        return self.ALLOWED_ORIGINS if isinstance(self.ALLOWED_ORIGINS, list) else []
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()

# Database configuration helpers
def get_database_url() -> str:
    """Get the async database URL."""
    return settings.DATABASE_URL

def get_sync_database_url() -> str:
    """Get the sync database URL (for Alembic migrations)."""
    if settings.DATABASE_URL_SYNC:
        return settings.DATABASE_URL_SYNC
    # Convert async URL to sync URL
    return settings.DATABASE_URL.replace("+asyncpg", "").replace("+asyncio", "") 