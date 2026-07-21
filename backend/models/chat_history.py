"""SQLModel za čuvanje istorije razgovora u PostgreSQL.

Zamenjuje raniji in-memory `_chat_memories` dict koji je rastao neograničeno.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ChatHistory(SQLModel, table=True):
    """Jedna poruka iz istorije razgovora."""

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, nullable=False)
    role: str = Field(nullable=False)  # "user" ili "assistant"
    content: str = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
