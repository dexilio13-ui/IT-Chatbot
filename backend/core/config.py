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

    # ── Aplikacija ─────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]
    UPLOAD_DIR: str = str(BACKEND_DIR / "uploads")

    # ── Podesavanja ponasanja asistenta ─────────────────────
    ENABLE_CHITCHAT: bool = True
    # Kada je ukljuceno, asistent odgovara na pozdrave i caskanje
    # pored tehnickih pitanja iz baze znanja.

    CHITCHAT_TEMPERATURE: float = 0.4
    # Temperatura za LLM kada je caskanje ukljuceno.
    # 0.1 = precizno/faktografski, 0.3-0.5 = prirodnije za caskanje.
    # Kad je caskanje iskljuceno, koristi se 0.1 (fiksno).

    # ── Cene se ucitavaju automatski sa HF Space-a ────────────
    # GitHub Action svakodnevno push-uje komponente.json direktno
    # na HF Space. Configurator prvo cita taj fajl, pa pada na
    # backend/data/components.json ako ne postoji.
    # Nisu potrebne dodatne env varijable.


import logging

settings = Settings()

# Validacija da je DATABASE_URL postavljen.
# Ovo JE obavezno za regularni rad (backend/server), ali nije obavezno
# za HF Spaces gde se koristi in-memory umesto PostgreSQL.
# HF Spaces treba da postavi HF_SPACE=true u env varijablama.
if not settings.DATABASE_URL:
    logger = logging.getLogger("config")
    logger.warning(
        "DATABASE_URL nije postavljen. "
        "Istorija razgovora nece biti sacuvana u bazi. "
        "Koristi se in-memory cuvanje (samo za ovu sesiju)."
    )
