"""Centralizovana konfiguracija aplikacije koristeći Pydantic Settings.

Sve env varijable se učitavaju na jednom mestu.
Koristiti `from core.config import settings` u svim modulima.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Putanja do backend/ direktorijuma (za uploads i sl.)
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── JWT ────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "tvoja-super-tajna-sifra-za-jwt-32bita"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── PostgreSQL (Lokalni) ──────────────────────────────
    DATABASE_URL: str = ""

    # ── Qdrant ─────────────────────────────────────────────
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "it_support_kb"
    QDRANT_EMBEDDING_DIM: int = 1536  # text-embedding-3-small dimenzija

    # ── OpenAI ─────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── LlamaCloud (LlamaParse) ───────────────────────────
    LLAMA_CLOUD_API_KEY: str = ""

    # ── Groq LLM (opciono, legacy) ────────────────────────
    GROQ_API_KEY: str = ""

    # ── Redis (Celery broker/backend) ──────────────────────
    REDIS_BROKER_URL: str = "redis://localhost:6379/0"
    REDIS_BACKEND_URL: str = "redis://localhost:6379/1"

    # ── Aplikacija ─────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]
    UPLOAD_DIR: str = str(BACKEND_DIR / "uploads")


settings = Settings()

# Validacija da je DATABASE_URL postavljen (jedino mesto gde proveravamo)
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL nije postavljen. Proveri .env fajl ili okruženje.")
