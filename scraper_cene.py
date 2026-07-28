#!/usr/bin/env python3
"""
scraper_cene.py — Skrejpovanje cena sa Orion Computers konfiguratora.

Skida podatke sa http://www.orioncomputers.rs/konfigurator_nov.aspx
i generise komponente.json u formatu koji configurator ocekuje.

Koristi se kroz GitHub Action (daily_scrape.yml) koji:
  1. Pokrece ovaj skript
  2. Push-uje komponente.json na Hugging Face Space

Kategorije koje se skrejpuju:
  - Maticna ploca  → motherboard
  - Procesor       → cpu
  - RAM            → ram
  - SSD/HDD        → storage
  - Graficka karta → gpu
  - Kuciste        → case
  - Napajanje      → psu

Format izlaza: {"components": {"cpu": [...], "motherboard": [...], ...}}

Zahteva: requests, beautifulsoup4
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import sys

# ── Konstante ────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "http://www.orioncomputers.rs/konfigurator_nov.aspx",
}

# Mapa:  Orion dropdown ID → kategorija u komponente.json
KATEGORIJE = {
    "DropDownList1": "motherboard",   # Maticna ploca
    "DropDownList2": "cpu",           # Procesor
    "DropDownList3": "ram",           # RAM
    "DropDownList5": "storage",       # SSD/HDD
    "DropDownList7": "gpu",           # Graficka karta
    "DropDownList10": "case",          # Kuciste
    "DropDownList18": "psu",          # Napajanje
}

# Okvirna konverzija RSD → EUR (1 EUR ≈ 117 RSD, lepo zaokruzeno)
RSD_U_EUR = 117


def dohvati_cenu(dropdown_id: str, sifra: str) -> float | None:
    """
    Dohvata cenu za dati dropdown i sifru komponente.

    Orion konfigurator koristi ASP.NET Web Forms sa __VIEWSTATE-om.
    """
    session = requests.Session()
    try:
        r1 = session.get(
            "http://www.orioncomputers.rs/konfigurator_nov.aspx",
            headers=HEADERS,
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"  [GRESKA] Ne mogu da ucitam stranicu: {e}", file=sys.stderr)
        return None

    soup1 = BeautifulSoup(r1.text, "html.parser")

    # Izvuci ASP.NET hidden polja
    viewstate = soup1.find("input", id="__VIEWSTATE")
    viewstategen = soup1.find("input", id="__VIEWSTATEGENERATOR")
    eventvalidation = soup1.find("input", id="__EVENTVALIDATION")

    data = {
        "__EVENTTARGET": dropdown_id,
        "__EVENTARGUMENT": "",
        "__VIEWSTATE": viewstate["value"] if viewstate else "",
        "__VIEWSTATEGENERATOR": viewstategen["value"] if viewstategen else "",
        "__EVENTVALIDATION": eventvalidation["value"] if eventvalidation else "",
        dropdown_id: sifra,
    }

    try:
        r2 = session.post(
            "http://www.orioncomputers.rs/konfigurator_nov.aspx",
            headers=HEADERS,
            data=data,
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"  [GRESKA] Ne mogu da postujem zahtev: {e}", file=sys.stderr)
        return None

    if "Server Error" in r2.text:
        return None

    soup2 = BeautifulSoup(r2.text, "html.parser")
    label = soup2.find("span", id="LabelSuma")

    if label:
        cena_tekst = label.text.strip()
        try:
            return float(cena_tekst.replace(",", ""))
        except ValueError:
            return None
    return None


def proceni_nivo(cena_eur: float) -> str:
    """Procenjuje nivo (grade) komponente na osnovu cene u EUR."""
    if cena_eur < 300:
        return "mid"
    elif cena_eur < 600:
        return "high"
    else:
        return "enthusiast"


def skrepuj_sve() -> dict:
    """
    Glavna funkcija za skrejpovanje.

    Parsira pocetnu stranicu, izvlaci opcije iz svakog dropdown-a,
    dohvata cene i vraca dictionary u formatu za komponente.json.
    """
    try:
        r = requests.get(
            "http://www.orioncomputers.rs/konfigurator_nov.aspx",
            headers=HEADERS,
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"GRESKA: Ne mogu da ucitam pocetnu stranicu: {e}", file=sys.stderr)
        return {"components": {}}

    soup = BeautifulSoup(r.text, "html.parser")

    # Izbroj ukupno komponenti za napredak
    ukupno = 0
    for dropdown_id in KATEGORIJE:
        select = soup.find("select", id=dropdown_id)
        if not select:
            continue
        for o in select.find_all("option"):
            val = o.get("value", "")
            txt = o.text.strip()
            if val and val != "nista" and txt not in ("---", "xxxxxx", ""):
                ukupno += 1

    print(f"Ukupno komponenti za skrejpovanje: {ukupno}\n")

    rezultat: dict[str, list[dict]] = {kat: [] for kat in KATEGORIJE.values()}
    brojac = 0

    for dropdown_id, kategorija in KATEGORIJE.items():
        select = soup.find("select", id=dropdown_id)
        if not select:
            print(f"[{kategorija}] — NEMA dropdown-a (ID: {dropdown_id})")
            continue

        opcije = []
        for o in select.find_all("option"):
            val = o.get("value", "")
            txt = o.text.strip()
            if val and val != "nista" and txt not in ("---", "xxxxxx", ""):
                opcije.append((val, txt))

        print(f"[{kategorija}] — {len(opcije)} komponenti")

        for sifra, naziv in opcije:
            brojac += 1
            cena_rsd = dohvati_cenu(dropdown_id, sifra)

            if cena_rsd is not None:
                cena_eur = round(cena_rsd / RSD_U_EUR, 2)
               # Zaokruzi na najblizu .99
                if cena_eur > 5:
                    cena_eur = round(cena_eur * 1.0)
                    cena_eur = float(int(cena_eur) + 0.99)
                status = f"{cena_rsd:.0f} RSD (~{cena_eur:.0f} EUR)"
            else:
                cena_eur = 0
                status = "nema cene"

            print(f"  [{brojac}/{ukupno}] {naziv[:55]} → {status}")

            komponenta = {
                "name": naziv,
                "price": cena_eur,
            }

            # Dodaj procenjeni nivo ako imamo cenu
            if cena_eur > 0:
                komponenta["grade"] = proceni_nivo(cena_eur)

            rezultat[kategorija].append(komponenta)

            # Ne preteruj sa zahtevima — 0.5s pauza
            time.sleep(0.5)

    return {"components": rezultat}


# ── Main ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  ORION COMPUTERS — Skrejpovanje cena komponenti")
    print("=" * 60)
    print()

    podaci = skrepuj_sve()
    ukupno_komponenti = sum(
        len(items) for items in podaci["components"].values()
    )

    with open("komponente.json", "w", encoding="utf-8") as f:
        json.dump(podaci, f, indent=2, ensure_ascii=False)

    print()
    print(f"✓ Gotovo! {ukupno_komponenti} komponenti sacuvano u komponente.json")
    print()
    print("Kategorije po broju komponenti:")
    for kat, items in podaci["components"].items():
        print(f"  {kat}: {len(items)}")
