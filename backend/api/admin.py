import logging
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, select

from core.db import get_session
from core.config import settings
from models.user import User

# Dependency za proveru tokena (koristimo istu kao u chat.py)
from api.chat import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Admin dependency ───────────────────────────────────────
async def require_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Dependency koja dozvoljava pristup samo admin korisnicima."""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Samo admin može pristupiti ovoj ruti.",
        )
    return current_user


# ── Rute ───────────────────────────────────────────────────


@router.get("/users")
async def list_users(
    session: Session = Depends(get_session),
    _admin: dict[str, Any] = Depends(require_admin),
) -> list[dict[str, Any]]:
    """Vraća listu svih korisnika (samo za admina)."""
    statement = select(User)
    users = session.exec(statement).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "role_id": u.role_id,
            "role_name": u.role_name,
            "is_admin": u.is_admin,
        }
        for u in users
    ]


@router.get("/documents")
async def list_documents(
    _admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    """Vraća listu indeksiranih dokumenata iz Qdrant-a (samo za admina)."""
    from qdrant_client import QdrantClient

    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    try:
        collection_info = client.get_collection(settings.QDRANT_COLLECTION)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Kolekcija '{settings.QDRANT_COLLECTION}' nije pronađena: {e}",
        )

    points, _ = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        limit=10000,
        with_payload=True,
        with_vectors=False,
    )

    documents: list[dict[str, Any]] = []
    seen_sources: set[str] = set()

    for point in points:
        payload = point.payload or {}
        source = payload.get("source", "Nepoznat")
        required_role_id = payload.get("required_role_id", "?")
        text_preview = (payload.get("text", "") or "")[:120]

        # Grupišemo po source-u da ne dupliramo
        if source not in seen_sources:
            seen_sources.add(source)
            documents.append(
                {
                    "id": str(point.id) if point.id else "?",
                    "source": source,
                    "required_role_id": required_role_id,
                    "chunks": 1,
                    "text_preview": text_preview,
                }
            )
        else:
            # Uvećavamo broj chunkova za postojeći source
            for doc in documents:
                if doc["source"] == source:
                    doc["chunks"] += 1
                    break

    return {
        "collection": settings.QDRANT_COLLECTION,
        "total_points": collection_info.points_count,
        "documents": documents,
    }


@router.delete("/documents/source/{source_name}")
async def delete_documents_by_source(
    source_name: str,
    _admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    """
    Briše sve point-e iz Qdrant-a koji pripadaju datom source-u (samo za admina).

    Ovo je korisnije od brisanja pojedinačnih point-ova, jer jedan dokument
    može imati više chunk-ova koji dele isti source naziv.

    Args:
        source_name: Naziv izvora (source) za brisanje (case-sensitive).
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import FieldCondition, Filter, MatchValue

    from rag.engine import invalidate_bm25_cache

    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    # 1. Pronađi sve point-ove sa datim source-om
    try:
        points, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            limit=10000,
            with_payload=False,
            with_vectors=False,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source_name),
                    )
                ]
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Greška pri pretrazi Qdrant-a: {e}",
        )

    if not points:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source '{source_name}' nije pronađen u kolekciji.",
        )

    point_ids = [str(p.id) for p in points if p.id]
    logger.info(
        "Admin brise %d point-ova za source '%s'.",
        len(point_ids),
        source_name,
    )

    # 2. Obriši ih
    try:
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=point_ids,  # type: ignore[arg-type]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Greška pri brisanju point-ova: {e}",
        )

    # 3. Invalidiraj BM25 cache
    invalidate_bm25_cache()

    return {
        "status": "ok",
        "message": f"Source '{source_name}' obrisan: {len(point_ids)} chunk(ova).",
        "source": source_name,
        "deleted_chunks": len(point_ids),
    }


@router.delete("/documents/{point_id}")
async def delete_document(
    point_id: str,
    _admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    """Briše jedan point iz Qdrant kolekcije (samo za admina)."""
    from qdrant_client import QdrantClient
    from qdrant_client.http.exceptions import UnexpectedResponse

    client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    try:
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=[point_id],
        )
        logger.info(
            "Admin je obrisao point %s iz kolekcije %s",
            point_id,
            settings.QDRANT_COLLECTION,
        )
        return {"status": "ok", "message": f"Point {point_id} obrisan."}
    except UnexpectedResponse as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Point {point_id} nije pronađen: {e}",
        )


# ── Dozvoljene ekstenzije za upload ────────────────────────
ALLOWED_UPLOAD_EXTENSIONS: set[str] = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".txt",
    ".md",
    ".csv",
}


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    required_role_id: int = Form(1),
    source_name: str | None = Form(None),
    _admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    """
    Upload dokumenta u bazu znanja (samo za admina).

    Prihvata: PDF, DOCX, TXT, MD, CSV.
    Veličina fajla je ograničena na 50MB (FastAPI default).

    Args:
        file: Fajl za upload.
        required_role_id: 1=Kupac, 2=Prodavac, 3=Serviser.
        source_name: Opcioni naziv izvora (default: ime fajla).
    """
    # ── Validacija ekstenzije ───────────────────────────────
    ext = os.path.splitext(file.filename or "")[1].lower()
    if not ext or ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Nedozvoljena ekstenzija '{ext}'. "
                f"Dozvoljene su: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}."
            ),
        )

    # ── Validacija role_id ──────────────────────────────────
    if required_role_id not in (1, 2, 3):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="required_role_id mora biti 1 (Kupac), 2 (Prodavac) ili 3 (Serviser).",
        )

    # ── Čitanje fajla u memoriju ────────────────────────────
    content = await file.read()

    # Ograničenje veličine fajla (50 MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Fajl je prevelik ({len(content) / 1024 / 1024:.1f} MB). Maksimalna dozvoljena veličina je 50 MB.",
        )

    logger.info(
        "Admin upload-uje '%s' (%d bajtova, role_id=%d).",
        file.filename,
        len(content),
        required_role_id,
    )

    # Bezbedno ime fajla (UUID prefiks da izbegnemo kolizije)
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = upload_dir / safe_filename

    try:
        # Sačuvaj na disk za SimpleDirectoryReader
        file_path.write_bytes(content)

        source = source_name or file.filename or "Nepoznat"

        # LlamaIndex import-i (lokalni da ne usporavaju import modula)
        from llama_index.core import StorageContext, VectorStoreIndex
        from llama_index.core import SimpleDirectoryReader
        from llama_index.core.node_parser import SentenceSplitter, MarkdownNodeParser
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        from qdrant_client import QdrantClient

        from rag.engine import invalidate_bm25_cache

        # ── Odabir parsera na osnovu tipa fajla ─────────────
        # Za PDF, DOCX, PPTX koristimo LlamaParse (čuva tabele i strukturu)
        # Za TXT, MD, CSV koristimo SimpleDirectoryReader + SentenceSplitter
        structured_formats = {".pdf", ".docx", ".doc", ".pptx"}

        if ext in structured_formats:
            from llama_parse import LlamaParse

            parser = LlamaParse(
                result_type="markdown",
                api_key=settings.LLAMA_CLOUD_API_KEY,
                verbose=False,
            )
            documents = parser.load_data(str(file_path))

            # MarkdownNodeParser čuva tabele i strukturu netaknutom
            node_parser: MarkdownNodeParser | SentenceSplitter = MarkdownNodeParser()
            nodes = node_parser.get_nodes_from_documents(documents)
        else:
            # TXT, MD, CSV — standardni SentenceSplitter
            reader = SimpleDirectoryReader(input_files=[str(file_path)])
            documents = reader.load_data()
            node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
            nodes = node_parser.get_nodes_from_documents(documents)

        for node in nodes:
            node.metadata["required_role_id"] = required_role_id
            node.metadata["source"] = source

        # ── Indeksiranje u Qdrant ───────────────────────────
        client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY or None,
        )
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=settings.QDRANT_COLLECTION,
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Kreiramo indeks — konstruktor generiše embeddinge i upisuje u Qdrant
        VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
            show_progress=False,
        )

        # ── Invalidacija BM25 cache-a ───────────────────────
        invalidate_bm25_cache()

        logger.info(
            "Dokument '%s' indeksiran: %d chunkova (role_id=%d).",
            source,
            len(nodes),
            required_role_id,
        )

        return {
            "status": "ok",
            "message": f"Dokument '{source}' je uspešno indeksiran sa {len(nodes)} chunkova.",
            "source": source,
            "chunks": len(nodes),
            "required_role_id": required_role_id,
        }

    except Exception as e:
        logger.error("Greška pri upload-u dokumenta '%s': %s", file.filename, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Greška pri indeksiranju dokumenta: {e}",
        )
    finally:
        # Očisti fajl sa diska posle obrade
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass
