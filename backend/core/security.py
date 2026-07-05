import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer

# Za početak koristimo hardkodovanu tajnu (kasnije ide u .env fajl)
SECRET_KEY = "0fe03762f40c338b348de62963516b296817dcde0a3b3e615fb37442c4daf45c"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

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
