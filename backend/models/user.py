from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    role_id: int = Field(
        default=1, nullable=False
    )  # 1: Kupac, 2: Prodavac, 3: Serviser
    role_name: str = Field(default="Customer", nullable=False)
    is_admin: bool = Field(
        default=False, nullable=False
    )  # Admin flag (ortogonalno na role_id)
