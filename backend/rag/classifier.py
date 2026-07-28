# backend/rag/classifier.py

"""
Klasifikator poruka za pametnu detekciju caskanja.

Omogucava da se svaka poruka pojedinacno klasifikuje kao
caskanje (pozdrav, opsti razgovor) ili tehnicko pitanje,
cime se dinamicki bira odgovarajuci prompt i temperatura za LLM.
"""

import re
from typing import Pattern

# ── Regex obrasci za prepoznavanje caskanja ───────────────────────

# Srpski pozdravi i uzvici (podrzava i dijakritike: cao = cao)
_GREETINGS: list[Pattern[str]] = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"^\s*(cao|caooo|cao|caooo|zdravo|zdravooo|hej|hey|hello|hi|pozdrav|pozz|pozzz)\b",
        r"^\s*(dobar dan|dobro jutro|dobro vece|laku noc)\b",
        r"^\s*(dovidjenja|dovidjenja|vidimo se|cao cao|cao cao|pozdrav svima)\b",
    ]
]

# Raspitivanje i opsti razgovor (podrzava i dijakritike)
_INQUIRIES: list[Pattern[str]] = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"\b(kako si|kako ste|kako ide|kako je|kako zivot|kako posao|sta ima|sta ima|sta novo)\b",
        r"\b(sta radis|sta radis|sta radite|sta radite|cime se bavis|cime se bavis)\b",
        r"\b(gde si|gde ste|gdje si|odakle si|otkud ti)\b",
        r"\b(jesi li tu|jesi tu|jel si tu|da li si tu)\b",
    ]
]

# Zahvale i ljubaznosti
_POLITENESS: list[Pattern[str]] = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"\b(hvala|puno hvala|hvala lepo|hvala ti|hvala vam|tnx|thanks|thank you)\b",
        r"\b(izvini|izvinite|oprosti|oprostite|pardon|molim te|molim vas)\b",
        r"\b(nema problema|nema na cemu|nema na cemu|sve ok|u redu)\b",
    ]
]

# Pitanja o asistentu (podrzava i dijakritike)
_ABOUT_ASSISTANT: list[Pattern[str]] = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"\b(ko si ti|sta si ti|sta si ti|sta mozes|sta mozes|kako se zoves|kako se zoves)\b",
        r"\b(ko te je napravio|ko te napravio|gde zivis|gde zivis|imas li ime|imas li ime)\b",
        r"\b(koliko imas godina|koliko imas godina|sta volis|sta volis)\b",
    ]
]

# Emotikoni i pozitivne reakcije
_REACTIONS: list[Pattern[str]] = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"\b(super|odlicno|odlicno|savrseno|savrseno|fenomenalno|bravo|svaka cast|svaka cast)\b",
        r"\b(kul|cool|strava|vrh|top)\b",
        r"([:;Xx8][\-oO]?[)DpP/\\@\|])",
    ]
]

# Opsti komentari koji nisu tehnicka pitanja
_GENERAL_CHITCHAT: list[Pattern[str]] = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"^\s*(samo pitam|samo rekoh|zanimljivo|interesantno|ma dobro|e pa dobro)\b",
        r"^\s*(ok|okej|u redu|vazi|jasno|razumem)\b",
    ]
]

# Kombinujemo sve obrasce
_ALL_CHITCHAT_PATTERNS: list[Pattern[str]] = (
    _GREETINGS + _INQUIRIES + _POLITENESS + _ABOUT_ASSISTANT + _REACTIONS + _GENERAL_CHITCHAT
)


def is_chitchat_query(message: str) -> bool:
    """
    Klasifikuje korisnicku poruku kao caskanje ili tehnicko pitanje.

    Koristi regex obrasce za prepoznavanje pozdrava, raspitivanja,
    zahvala, pitanja o asistentu i emotikona. Ako nista ne detektuje,
    smatra se tehnickim pitanjem i vraca False.

    Args:
        message: Korisnicka poruka (raw string).

    Returns:
        True ako poruka izgleda kao caskanje/pozdrav.
        False ako je verovatno tehnicko pitanje.
    """
    if not message or not message.strip():
        return False

    for pattern in _ALL_CHITCHAT_PATTERNS:
        if pattern.search(message):
            return True

    return False
