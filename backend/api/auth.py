import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from core.security import create_access_token
from core.db import get_session
from models.user import User

router = APIRouter()


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    """Autentifikuje korisnika i vraća JWT token sa njegovom rolom iz baze."""

    # 1. Traženje korisnika u PostgreSQL bazi
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()

    # 2. Provera lozinke (bcrypt hash)
    if not user or not bcrypt.checkpw(
        form_data.password.encode("utf-8"),
        user.hashed_password.encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pogrešan username ili lozinka",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Kreiranje JWT tokena
    access_token = create_access_token(
        data={
            "sub": user.username,
            "role_id": user.role_id,
            "is_admin": user.is_admin,
        }
    )

    # 4. Standardni OAuth2 format odgovora
    return {"access_token": access_token, "token_type": "bearer"}
