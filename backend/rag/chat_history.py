"""Pomoćne funkcije za čuvanje i učitavanje istorije razgovora iz PostgreSQL."""

import logging
from datetime import datetime, timezone

from sqlmodel import Session, select

from models.chat_history import ChatHistory

logger = logging.getLogger(__name__)

# Maksimalan broj poruka koje se učitavaju iz baze (da ne preoptereti memoriju)
MAX_HISTORY_MESSAGES = 50


def load_chat_history(
    session: Session,
    username: str,
    max_messages: int = MAX_HISTORY_MESSAGES,
) -> list[ChatHistory]:
    """Učitava poslednjih `max_messages` poruka za korisnika iz PostgreSQL."""
    statement = (
        select(ChatHistory)
        .where(ChatHistory.username == username)
        .order_by(ChatHistory.created_at.asc())  # type: ignore[attr-defined]
        .limit(max_messages)
    )
    results = session.exec(statement).all()
    logger.debug(
        "Učitano %d poruka istorije za korisnika '%s'.", len(results), username
    )
    return list(results)


def save_chat_messages(
    session: Session,
    username: str,
    user_message: str,
    assistant_message: str,
) -> None:
    """Čuva korisničku poruku i asistentov odgovor u PostgreSQL."""
    now_user = datetime.now(timezone.utc)
    now_assistant = datetime.now(timezone.utc)

    user_entry = ChatHistory(
        username=username,
        role="user",
        content=user_message,
        created_at=now_user,
    )
    assistant_entry = ChatHistory(
        username=username,
        role="assistant",
        content=assistant_message,
        created_at=now_assistant,
    )

    session.add(user_entry)
    session.add(assistant_entry)
    session.commit()

    logger.debug("Sačuvane 2 poruke istorije za korisnika '%s'.", username)
