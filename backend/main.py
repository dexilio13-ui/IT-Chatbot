import logging
from contextlib import asynccontextmanager

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, select

from core.logger import setup_logging
from core.db import engine
from core.config import settings
from models.user import User
from api.chat import router as chat_router
from api.auth import router as auth_router
from api.admin import router as admin_router


def _hash_password(password: str) -> str:
    """Vraća bcrypt hash lozinke."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Startup (pre yield): inicijalizacija logera, baze i drugih resursa.
    Shutdown (posle yield): graceful cleanup.
    """
    # ── STARTUP ──────────────────────────────────────────────
    setup_logging()
    logger = logging.getLogger("main")
    logger.info("=" * 50)
    logger.info("Aplikacija se pokrece...")
    logger.info("Modularni RAG Chatbot - FastAPI + LlamaIndex + Qdrant Cloud")

    # ── PostgreSQL baza ──────────────────────────────────────
    logger.info("Inicijalizacija PostgreSQL baze podataka...")
    SQLModel.metadata.create_all(engine)

    # Automatski seeding: Dodajemo testne korisnike ako je baza prazna
    with Session(engine) as session:
        existing_user = session.exec(select(User)).first()
        if not existing_user:
            logger.info("Tabela korisnika je prazna. Dodajem pocetne korisnike...")
            pocetni_korisnici = [
                User(
                    username="admin",
                    hashed_password=_hash_password("admin123"),
                    role_id=3,
                    role_name="Admin",
                    is_admin=True,
                ),
                User(
                    username="serviser",
                    hashed_password=_hash_password("123"),
                    role_id=3,
                    role_name="Technician",
                ),
                User(
                    username="prodavac",
                    hashed_password=_hash_password("123"),
                    role_id=2,
                    role_name="Sales",
                ),
                User(
                    username="kupac",
                    hashed_password=_hash_password("123"),
                    role_id=1,
                    role_name="Customer",
                ),
            ]
            session.add_all(pocetni_korisnici)
            session.commit()
            logger.info("Pocetni korisnici uspesno kreirani!")

    # ── Qdrant: auto-migracija kolekcije na ispravnu dimenziju ────
    logger.info("Proveravam Qdrant kolekciju '%s'...", settings.QDRANT_COLLECTION)
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import VectorParams, Distance, PayloadSchemaType

        qdrant_client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )

        collections = qdrant_client.get_collections()
        existing_names = {c.name for c in collections.collections}

        if settings.QDRANT_COLLECTION not in existing_names:
            logger.info(
                "Kolekcija '%s' ne postoji. Kreiram je (vektor_size=%d, distance=Cosine)...",
                settings.QDRANT_COLLECTION,
                settings.QDRANT_EMBEDDING_DIM,
            )
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=settings.QDRANT_EMBEDDING_DIM, distance=Distance.COSINE
                ),
            )
            logger.info("Kolekcija '%s' uspesno kreirana.", settings.QDRANT_COLLECTION)
        else:
            # Kolekcija postoji — proveri da li vektorska dimenzija odgovara
            collection_info = qdrant_client.get_collection(settings.QDRANT_COLLECTION)
            vectors_config = collection_info.config.params.vectors
            if isinstance(vectors_config, dict):
                # Qdrant >=1.12 vraća dict[str, VectorParams] za named vectors
                existing_dim = next(iter(vectors_config.values())).size
            elif vectors_config is not None:
                existing_dim = vectors_config.size
            else:
                # None je praktično nemoguć za postojeću kolekciju
                existing_dim = settings.QDRANT_EMBEDDING_DIM
            if existing_dim != settings.QDRANT_EMBEDDING_DIM:
                logger.warning(
                    "Kolekcija '%s' ima dimenziju %d, a potrebna je %d "
                    "(embedding model je promenjen sa bge-small-en-v1.5 na "
                    "text-embedding-3-small). Brisem staru i kreiram novu...",
                    settings.QDRANT_COLLECTION,
                    existing_dim,
                    settings.QDRANT_EMBEDDING_DIM,
                )
                qdrant_client.delete_collection(
                    collection_name=settings.QDRANT_COLLECTION
                )
                logger.info(
                    "Stara kolekcija '%s' obrisana.", settings.QDRANT_COLLECTION
                )
                qdrant_client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=VectorParams(
                        size=settings.QDRANT_EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(
                    "Nova kolekcija '%s' kreirana (vektor_size=%d).",
                    settings.QDRANT_COLLECTION,
                    settings.QDRANT_EMBEDDING_DIM,
                )

        # Uvek pokusavamo da kreiramo payload index na 'source' polju
        # (potrebno za filtriranje po source-u prilikom brisanja)
        try:
            qdrant_client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION,
                field_name="source",
                field_schema=PayloadSchemaType.KEYWORD,
            )
            logger.info("Payload index na 'source' polju kreiran (ili vec postoji).")
        except Exception as index_e:
            # Index verovatno vec postoji - to nije greska
            logger.debug("Payload index na 'source' polju: %s", index_e)

        # Payload index na 'required_role_id' polju (INTEGER)
        # Potreban za MetadataFilters sa operatorom LTE u RBAC filtriranju
        try:
            qdrant_client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION,
                field_name="required_role_id",
                field_schema=PayloadSchemaType.INTEGER,
            )
            logger.info(
                "Payload index na 'required_role_id' polju kreiran (ili vec postoji)."
            )
        except Exception as index_e:
            logger.debug("Payload index na 'required_role_id' polju: %s", index_e)
    except Exception as e:
        logger.warning("Ne mogu da proverim/kreiram Qdrant kolekciju: %s", e)

    logger.info("=" * 50)

    yield  # Aplikacija je aktivna odavde do gašenja

    # ── SHUTDOWN ─────────────────────────────────────────────
    logger.info("=" * 50)
    logger.info("Aplikacija se gasi...")
    logger.info("Resursi se ciste.")
    logger.info("=" * 50)


app = FastAPI(title="Modularni RAG Chatbot (Qdrant Cloud)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Uključujemo rute pod api prefiksom
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "poruka": "Modularni FastAPI RAG sistem je aktivan!"}
