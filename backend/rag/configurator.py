# backend/rag/configurator.py

"""
Konfigurator modul za PC komponente i cene.

Omogucava detekciju upita za konfiguraciju racunara
i ucitavanje kataloga komponenti.

Redosled ucitavanja:
  1. komponente.json u korenu HF Space-a (pushereno od strane GitHub Action-a)
  2. backend/data/components.json (lokalni sample fajl)
  3. Ako nijedan ne postoji, vraca prazan katalog
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Putanje do fajlova sa cenama ─────────────────────────────────

# Putanja do backend/data/components.json (lokalni sample fajl)
_COMPONENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "components.json"

# Putanja do komponente.json u korenu HF Space-a
# Na HF:  app.py i komponente.json su u istom korenom direktorijumu
# Lokalno (kad se pokrene python hf/app.py): isto vazi
# Ovaj Path racuna: configurator.py -> ../../komponente.json
_HF_PRICE_LIST_PATH = (
    Path(__file__).resolve().parent.parent.parent / "komponente.json"
)


# ── Regex obrasci za prepoznavanje upita za konfiguraciju ─────────

_CONFIG_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"\b(napravi|sastavi|predlozi|napisi)\b.*\b(konfiguraciju|kompjuter|racunar|konfig|pc|config)\b",
        r"\b(konfiguracija|specifikacija)\b.*\b(za|do|oko)\b",
        r"\b(gaming|gejmerski|radna stanica|office|kancelarijski)\b.*\b(pc|racunar|kompjuter|config)\b",
        r"\b(koji cpu|koja graficka|koji procesor|koju maticnu|koliko rama)\b.*\b(za|sa)\b",
        r"\b(budzet|budget)\b.*\b(eur|eura|euro|dinara|rsd)\b",
        r"\b(da li mogu|mogu li)\b.*\b(kombinujem|spojim|uparim|stavim)\b",
        r"\b(da li je kompatibilno|da li odgovara|da li radi)\b.*\b(sa|na)\b",
        r"\b(koliko kosta|koja je cena)\b.*\b(konfiguracija|kompjuter|sklop)\b",
        r"\b(komponente|komponenti)\b.*\b(za|do)\b",
    ]
]

# Kategorije komponenti sa srpskim nazivima
CATEGORY_NAMES = {
    "cpu": "procesor (CPU)",
    "motherboard": "maticna ploca",
    "ram": "RAM memorija",
    "gpu": "graficka kartica (GPU)",
    "storage": "disk (SSD/HDD)",
    "psu": "napajanje (PSU)",
    "case": "kuciste",
    "cooler": "hladjenje",
}


# ── Kesiranje (spreca ponovno citanje fajla pri svakom upitu) ────

_cached_components: Optional[dict[str, Any]] = None


def invalidate_cache() -> None:
    """Invalidira kesirani katalog. Sledeci poziv ponovo cita fajl."""
    global _cached_components
    _cached_components = None
    logger.info("Cache za cenovnik invalidiran.")


def _load_components() -> Optional[dict[str, Any]]:
    """
    Ucitava katalog komponenti.

    Redosled (prvi koji postaje se koristi):
      1. komponente.json u korenu HF Space-a (pusheran od GitHub Action)
      2. backend/data/components.json (lokalni sample)

    Returns:
        Dict sa komponentama ili None ako nijedan fajl ne postoji.
    """
    global _cached_components

    if _cached_components is not None:
        return _cached_components

    sources_to_try = [
        ("HF cenovnik", _HF_PRICE_LIST_PATH),
        ("Lokalni sample", _COMPONENTS_PATH),
    ]

    for source_name, path in sources_to_try:
        if not path.exists():
            logger.debug("%s nije pronadjen na: %s", source_name, path)
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            components = data.get("components", {})
            if not components:
                logger.warning("%s nema 'components' kljuc.", source_name)
                continue

            _cached_components = components
            logger.info(
                "%s: %d kategorija komponenti ucitanih iz %s",
                source_name,
                len(components),
                path.name,
            )
            return components

        except (json.JSONDecodeError, OSError) as e:
            logger.warning(
                "Ne mogu da ucitam %s (%s): %s", source_name, path.name, e
            )
            continue

    logger.warning(
        "Nijedan fajl sa cenama nije pronadjen "
        "(trazeno: %s i %s).",
        _HF_PRICE_LIST_PATH,
        _COMPONENTS_PATH,
    )
    return None


def get_components_catalog() -> str:
    """
    Vraca lepo formatiran tekstualni prikaz svih komponenti sa cenama.

    Returns:
        String sa svim komponentama pogodan za ubacivanje u LLM context,
        ili prazan string ako nema podataka.
    """
    components = _load_components()
    if not components:
        return ""

    lines = []
    lines.append("=== KATALOG KOMPONENTI (sa cenama) ===")
    lines.append("")

    for category_key, items in components.items():
        category_name = CATEGORY_NAMES.get(category_key, category_key)
        lines.append(f"--- {category_name.upper()} ---")
        for item in items:
            details = []
            if "socket" in item:
                details.append(f"socket: {item['socket']}")
            if "tdp" in item:
                details.append(f"TDP: {item['tdp']}W")
            if "vram" in item:
                details.append(f"VRAM: {item['vram']}GB")
            if "capacity" in item:
                unit = "GB" if item["capacity"] < 2000 else "TB"
                cap = item["capacity"] if item["capacity"] < 2000 else item["capacity"] // 1000
                details.append(f"kapacitet: {cap}{unit}")
            if "watts" in item:
                details.append(f"snaga: {item['watts']}W")
            if "type" in item and item["type"] in ("DDR4", "DDR5", "NVMe", "HDD", "air", "liquid"):
                details.append(f"tip: {item['type']}")
            if "form_factor" in item:
                details.append(f"format: {item['form_factor']}")
            if "efficiency" in item:
                details.append(f"efikasnost: {item['efficiency']}")
            if "ram_type" in item:
                details.append(f"RAM tip: {item['ram_type']}")
            if "note" in item:
                details.append(f"napomena: {item['note']}")

            details_str = ", ".join(details)
            price_str = f"{item['price']}EUR" if item["price"] > 0 else "besplatno"
            if details_str:
                lines.append(f"  * {item['name']} -- {price_str} ({details_str})")
            else:
                lines.append(f"  * {item['name']} -- {price_str}")
        lines.append("")

    lines.append("=== KRAJ KATALOGA ===")
    return "\n".join(lines)


def is_config_query(message: str) -> bool:
    """
    Detektuje da li korisnik pita za konfiguraciju racunara.

    Args:
        message: Korisnicka poruka.

    Returns:
        True ako poruka lici na upit za konfiguraciju.
    """
    if not message or not message.strip():
        return False

    for pattern in _CONFIG_PATTERNS:
        if pattern.search(message):
            return True

    return False
