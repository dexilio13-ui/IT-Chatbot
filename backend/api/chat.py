from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any
import jwt

# Uvozimo RAG engine i parametre za dekodiranje tokena
from rag.engine import engine
from core.security import oauth2_scheme, SECRET_KEY, ALGORITHM

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


# Dependency funkcija koja proverava JWT token
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    try:
        # Dekodiranje tokena
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role_id: int | None = payload.get("role_id")

        if username is None or role_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nevalidan token (nedostaju podaci)",
            )
        # Od ove tacke nadalje mypy zna da su username: str i role_id: int
        return {"username": username, "role_id": role_id}

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
        print(
            f"Korisnik: {current_user['username']} | "
            f"Role ID: {current_user['role_id']} postavlja pitanje."
        )

        # Kasnije cemo current_user['role_id'] prosledjivati LlamaIndexu za filtriranje!
        response = engine.chat(request.message)

        return ChatResponse(response=str(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))