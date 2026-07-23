import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any
import jwt

# Uvozimo RAG engine (get_chat_engine) i parametre za dekodiranje tokena
from rag.engine import get_chat_engine
from core.security import oauth2_scheme, SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)

router = APIRouter()

# Fraza koju LLM vraća kada nema podatak u bazi znanja
_NO_DATA_PHRASE = "Nemam taj podatak u bazi znanja"


def _clamp_score(score: float | None) -> float | None:
    """
    Ograničava skor na opseg [0.0, 1.0] za korektan prikaz u procentima.

    Različiti retriveri vraćaju skorove u različitim opsezima:
      - Cosine similarity: [-1, 1] (ali u praksi 0-1)
      - BM25: neograničen (može biti 10+, 20+)
      - RRF: 0.0 – ~0.033

    Frontend prikazuje `Math.round(score * 100)%`, tako da sve preko 1.0
    daje > 100% što je zbunjujuće za korisnika.
    """
    if score is None:
        return None
    return round(min(max(score, 0.0), 1.0), 3)


class SourceInfo(BaseModel):
    source: str
    required_role_id: int | str
    score: float | None = None
    content: str = ""  # Tekst izvora za prikaz na klik


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceInfo] = []


# Dependency funkcija koja proverava JWT token
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    try:
        # Dekodiranje tokena
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role_id: int | None = payload.get("role_id")
        is_admin: bool = payload.get("is_admin", False)

        if username is None or role_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nevalidan token (nedostaju podaci)",
            )
        # Od ove tacke nadalje mypy zna da su username: str i role_id: int
        return {"username": username, "role_id": role_id, "is_admin": is_admin}

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token je istekao. Ulogujte se ponovo.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nevalidan token.",
        )


# Zasticena ruta: Zahteva da get_current_user uspesno prodje
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    try:
        # Prikazujemo u konzoli ko pita (dokaz da Auth radi)
        logger.info(
            "Korisnik: %s | Role ID: %s postavlja pitanje.",
            current_user["username"],
            current_user["role_id"],
        )

        chat_engine = get_chat_engine(
            username=current_user["username"],
            role_id=current_user["role_id"],
            is_admin=current_user.get("is_admin", False),
        )
        response = chat_engine.chat(request.message)

        # Ekstrakcija source_nodes u citate — prikazujemo samo 1 najbolji izvor
        response_text = str(response)
        sources: list[SourceInfo] = []

        # Ako LLM kaže da nema podatak, ne saljemo izvore
        if _NO_DATA_PHRASE not in response_text:
            for ns in (response.source_nodes or [])[:1]:
                sources.append(
                    SourceInfo(
                        source=ns.node.metadata.get("source", "Nepoznat"),
                        required_role_id=ns.node.metadata.get("required_role_id", "?"),
                        score=_clamp_score(ns.score),
                        content=ns.node.get_content()[:2000],  # Celi tekst + limit
                    )
                )

        return ChatResponse(response=response_text, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> StreamingResponse:
    """SSE streaming endpoint."""
    logger.info(
        "[SSE] Korisnik: %s | Role ID: %s streamuje pitanje.",
        current_user["username"],
        current_user["role_id"],
    )

    try:
        chat_engine = get_chat_engine(
            username=current_user["username"],
            role_id=current_user["role_id"],
            is_admin=current_user.get("is_admin", False),
        )
        streaming_response = chat_engine.stream_chat(request.message)
    except Exception as e:
        logger.error(
            "Greška pri inicijalizaciji strima (Qdrant kolekcija nedostaje?): %s", e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Baza znanja trenutno nije dostupna ili kolekcija ne postoji. Kontaktirajte administratora.",
        )

    def event_generator():
        try:
            # 1. Tokeni u realnom vremenu — skupljamo ih da znamo pun odgovor
            full_response: list[str] = []
            for token in streaming_response.response_gen:
                full_response.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            # 2. Sources (citations) — prikazujemo samo 1 najbolji izvor,
            #    ALI samo ako LLM nije rekao da nema podatak u bazi znanja
            response_text = "".join(full_response)
            if _NO_DATA_PHRASE in response_text:
                sources: list[dict[str, Any]] = []
            else:
                sources = [
                    {
                        "source": ns.node.metadata.get("source", "Nepoznat"),
                        "required_role_id": ns.node.metadata.get("required_role_id", "?"),
                        "score": _clamp_score(ns.score),
                        "content": ns.node.get_content()[:2000],  # Celi tekst + limit
                    }
                    for ns in (streaming_response.source_nodes or [])[:1]
                ]
            yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"

            # 3. Done signal
            yield 'data: {"type": "done"}\n\n'
        except Exception as e:
            logger.error("SSE greska: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
