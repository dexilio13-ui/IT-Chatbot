import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any
import jwt

# Uvozimo RAG engine (get_chat_engine) i parametre za dekodiranje tokena
from rag.engine import get_chat_engine
from rag.classifier import is_chitchat_query
from rag.configurator import is_config_query
from core.security import oauth2_scheme, SECRET_KEY, ALGORITHM
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Fraza koju LLM vraca kada nema podatak u bazi znanja
_NO_DATA_PHRASE = "Nemam taj podatak u bazi znanja"


def _clamp_score(score: float | None) -> float | None:
    """
    Ogranicava skor na opseg [0.0, 1.0] za korektan prikaz u procentima.
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


class GuestChatRequest(BaseModel):
    message: str
    session_id: str  # UUID koji frontend generise za gosta


class ChatResponse(BaseModel):
    response: str
    sources: list[SourceInfo] = []


# ----------------------------------------------------------------
# Dependency funkcija koja proverava JWT token
# ----------------------------------------------------------------
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role_id: int | None = payload.get("role_id")
        is_admin: bool = payload.get("is_admin", False)

        if username is None or role_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nevalidan token (nedostaju podaci)",
            )
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


# ================================================================
# ZASTICENE RUTE (zahtevaju JWT)
# ================================================================

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    """Chat endpoint sa JWT autentifikacijom."""
    try:
        msg = request.message
        use_chitchat = settings.ENABLE_CHITCHAT and is_chitchat_query(msg)
        use_config = settings.ENABLE_CHITCHAT and is_config_query(msg)

        logger.info(
            "Korisnik: %s | Role ID: %s | Chitchat: %s | Config: %s | Poruka: %.50s",
            current_user["username"],
            current_user["role_id"],
            use_chitchat,
            use_config,
            msg,
        )

        chat_engine = get_chat_engine(
            username=current_user["username"],
            role_id=current_user["role_id"],
            is_admin=current_user.get("is_admin", False),
            chitchat_enabled=use_chitchat,
            config_mode=use_config,
        )
        response = chat_engine.chat(msg)

        response_text = str(response)
        sources: list[SourceInfo] = []

        if _NO_DATA_PHRASE not in response_text:
            for ns in (response.source_nodes or [])[:1]:
                sources.append(
                    SourceInfo(
                        source=ns.node.metadata.get("source", "Nepoznat"),
                        required_role_id=ns.node.metadata.get("required_role_id", "?"),
                        score=_clamp_score(ns.score),
                        content=ns.node.get_content()[:2000],
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
    """SSE streaming endpoint sa JWT autentifikacijom."""
    msg = request.message
    use_chitchat = settings.ENABLE_CHITCHAT and is_chitchat_query(msg)
    use_config = settings.ENABLE_CHITCHAT and is_config_query(msg)

    logger.info(
        "[SSE] Korisnik: %s | Role ID: %s | Chitchat: %s | Config: %s | Poruka: %.50s",
        current_user["username"],
        current_user["role_id"],
        use_chitchat,
        use_config,
        msg,
    )

    try:
        chat_engine = get_chat_engine(
            username=current_user["username"],
            role_id=current_user["role_id"],
            is_admin=current_user.get("is_admin", False),
            chitchat_enabled=use_chitchat,
            config_mode=use_config,
        )
        streaming_response = chat_engine.stream_chat(msg)
    except Exception as e:
        logger.error(
            "Greska pri inicijalizaciji strima (Qdrant kolekcija nedostaje?): %s", e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Baza znanja trenutno nije dostupna ili kolekcija ne postoji. Kontaktirajte administratora.",
        )

    def event_generator():
        try:
            full_response: list[str] = []
            for token in streaming_response.response_gen:
                full_response.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            response_text = "".join(full_response)
            if _NO_DATA_PHRASE in response_text:
                sources: list[dict[str, Any]] = []
            else:
                sources = [
                    {
                        "source": ns.node.metadata.get("source", "Nepoznat"),
                        "required_role_id": ns.node.metadata.get("required_role_id", "?"),
                        "score": _clamp_score(ns.score),
                        "content": ns.node.get_content()[:2000],
                    }
                    for ns in (streaming_response.source_nodes or [])[:1]
                ]
            yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"
            yield 'data: {"type": "done"}\n\n'
        except Exception as e:
            logger.error("SSE greska: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ================================================================
# GUEST ENDPOINTS (bez JWT autentifikacije)
# ================================================================

@router.post("/chat/guest", response_model=ChatResponse)
async def chat_guest_endpoint(
    request: GuestChatRequest,
) -> Any:
    """Chat endpoint za goste (bez login-a)."""
    try:
        msg = request.message
        session_id = request.session_id
        use_chitchat = settings.ENABLE_CHITCHAT and is_chitchat_query(msg)
        use_config = settings.ENABLE_CHITCHAT and is_config_query(msg)

        logger.info(
            "[GUEST] Session: %s | Chitchat: %s | Config: %s | Poruka: %.50s",
            session_id[:8],
            use_chitchat,
            use_config,
            msg,
        )

        chat_engine = get_chat_engine(
            username=f"guest_{session_id}",
            role_id=1,  # Gost vidi samo javne dokumente
            is_admin=False,
            chitchat_enabled=use_chitchat,
            config_mode=use_config,
        )
        response = chat_engine.chat(msg)

        response_text = str(response)
        sources: list[SourceInfo] = []

        if _NO_DATA_PHRASE not in response_text:
            for ns in (response.source_nodes or [])[:1]:
                sources.append(
                    SourceInfo(
                        source=ns.node.metadata.get("source", "Nepoznat"),
                        required_role_id=ns.node.metadata.get("required_role_id", "?"),
                        score=_clamp_score(ns.score),
                        content=ns.node.get_content()[:2000],
                    )
                )

        return ChatResponse(response=response_text, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/guest/stream")
async def chat_guest_stream_endpoint(
    request: GuestChatRequest,
) -> StreamingResponse:
    """SSE streaming endpoint za goste (bez login-a)."""
    msg = request.message
    session_id = request.session_id
    use_chitchat = settings.ENABLE_CHITCHAT and is_chitchat_query(msg)
    use_config = settings.ENABLE_CHITCHAT and is_config_query(msg)

    logger.info(
        "[GUEST/SSE] Session: %s | Chitchat: %s | Config: %s | Poruka: %.50s",
        session_id[:8],
        use_chitchat,
        use_config,
        msg,
    )

    try:
        chat_engine = get_chat_engine(
            username=f"guest_{session_id}",
            role_id=1,
            is_admin=False,
            chitchat_enabled=use_chitchat,
            config_mode=use_config,
        )
        streaming_response = chat_engine.stream_chat(msg)
    except Exception as e:
        logger.error(
            "[GUEST/SSE] Greska pri inicijalizaciji strima: %s", e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Baza znanja trenutno nije dostupna.",
        )

    def event_generator():
        try:
            full_response: list[str] = []
            for token in streaming_response.response_gen:
                full_response.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            response_text = "".join(full_response)
            if _NO_DATA_PHRASE in response_text:
                sources: list[dict[str, Any]] = []
            else:
                sources = [
                    {
                        "source": ns.node.metadata.get("source", "Nepoznat"),
                        "required_role_id": ns.node.metadata.get("required_role_id", "?"),
                        "score": _clamp_score(ns.score),
                        "content": ns.node.get_content()[:2000],
                    }
                    for ns in (streaming_response.source_nodes or [])[:1]
                ]
            yield f"data: {json.dumps({'type': 'sources', 'content': sources})}\n\n"
            yield 'data: {"type": "done"}\n\n'
        except Exception as e:
            logger.error("[GUEST/SSE] Greska: %s", e)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
