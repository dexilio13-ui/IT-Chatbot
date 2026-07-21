"""Generička PostgreSQL konekcija preko SQLModel/SQLAlchemy.

Koristi DATABASE_URL iz okruženja (.env) za povezivanje na bilo koji
PostgreSQL provajder (Neon, ElephantSQL, AWS RDS, lokalni, itd.).
"""

from collections.abc import Generator
from sqlmodel import Session, create_engine

from core.config import settings

# echo=True omogućava praćenje SQL upita u konzoli tokom razvoja
engine = create_engine(settings.DATABASE_URL, echo=True)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
