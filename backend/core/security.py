import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer

from core.config import settings

# Secret ključ za JWT - učitava se iz settings-a
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

# FastAPI klasa koja kaže Swagger-u gde se nalazi login ruta
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict) -> str:
    """Kreira JWT token sa prosleđenim podacima (payload)."""
    to_encode = data.copy()
    # Postavljanje vremena isteka tokena
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # Generisanje tokena
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
