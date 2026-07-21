"""
Centralizovana logging konfiguracija za ceo backend.

Koristi se standardni Python `logging` modul.
Pozvati `setup_logging()` jednom prilikom pokretanja aplikacije (u lifespan),
a u svim modulima koristiti `logging.getLogger(__name__)`.
"""

import logging
import sys

# Format log poruke: vreme - ime_logera - nivo - poruka
_LOG_FORMAT = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Nivo logovanja (može se prebaciti na DEBUG po potrebi)
_DEFAULT_LEVEL = logging.INFO


def setup_logging(*, level: int = _DEFAULT_LEVEL) -> None:
    """Podešava root logger sa konzolnim handlerom i konzistentnim formatom.

    Ovu funkciju treba pozvati tačno jednom, prilikom startovanja aplikacije.
    Ako je root logger već konfigurisan (handlers), poziv je no-op.
    """
    root_logger = logging.getLogger()

    # Sprečavamo duplo konfigurisanje ako je setup_logging već pozvan
    if root_logger.handlers:
        return

    root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)

    logger = logging.getLogger("core.logger")
    logger.info(
        "Logging sistem inicijalizovan (nivo: %s).", logging.getLevelName(level)
    )
