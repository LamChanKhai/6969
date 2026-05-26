"""Core configuration."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "CSCV2025 Secure Platform"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # JWT
    SECRET_KEY: str = "demo-secret-key-replace-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./demo.db"

    # Storage
    STORAGE_PATH: Path = Path(__file__).parent.parent / "storage"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: tuple = (".txt", ".docx", ".png", ".jpg", ".jpeg", ".pdf", ".xlsx", ".zip")

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
