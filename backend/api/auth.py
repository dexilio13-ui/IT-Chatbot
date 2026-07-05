from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from core.security import create_access_token

router = APIRouter()

# Dummy baza korisnika (Dok ne uvedemo PostgreSQL i SQLModel)
# Oponašamo 3 različite role iz tvog opisa
FAKE_DB = {
    "serviser": {"password": "123", "role_id": 3, "role_name": "Technician"},
    "prodavac": {"password": "123", "role_id": 2, "role_name": "Sales"},
    "kupac": {"password": "123", "role_id": 1, "role_name": "Customer"},
}


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Autentifikuje korisnika i vraća JWT token sa njegovom rolom."""

    # 1. Provera da li korisnik postoji u našoj dummy bazi
    user = FAKE_DB.get(form_data.username)

    # 2. Provera lozinke (bez heširanja za sada)
    if not user or form_data.password != user["password"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pogrešan username ili lozinka",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Kreiranje JWT tokena (ubacujemo role_id da bismo kasnije filtrirali RAG)
    access_token = create_access_token(
        data={"sub": form_data.username, "role_id": user["role_id"]}
    )

    # 4. Standardni OAuth2 format odgovora
    return {"access_token": access_token, "token_type": "bearer"}
