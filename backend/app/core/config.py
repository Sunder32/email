import os
import sys

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/email_service"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@postgres:5432/email_service"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    FERNET_KEY: str = ""

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    SMTP_CONNECT_TIMEOUT: int = 15
    SMTP_SEND_TIMEOUT: int = 30
    SMTP_MAX_ATTEMPTS: int = 3
    SMTP_RETRY_BACKOFF_BASE: int = 2

    MAX_UPLOAD_SIZE_MB: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

_is_pytest = "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST")

if not _is_pytest:
    if not settings.JWT_SECRET_KEY or settings.JWT_SECRET_KEY == "change-me-to-a-long-random-string":
        raise RuntimeError(
            "JWT_SECRET_KEY must be set to a secure random value in .env "
            "(generate with: python -c \"import secrets; print(secrets.token_hex(32))\")"
        )
    if not settings.FERNET_KEY:
        raise RuntimeError(
            "FERNET_KEY must be set in .env "
            "(generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")"
        )
