#!/usr/bin/env python3
"""
rename_subtitles.py - Preimenuje .srt fajlove da odgovaraju .mkv fajlovima.

Koristi se za uskladjivanje titlova sa video fajlovima tako sto uparuje
broj epizode (S06EXX) izmedju .mkv i .srt fajlova.

Primer:
  .mkv:  Diagnosis.Murder.S06E10.Murder.x.4.DVDRip.DD2.0.x264-vetis.mkv
  .srt:  Diagnosis Murder (1993) - S06E10 - Murder x 4 [...].srt
  ->     Diagnosis.Murder.S06E10.Murder.x.4.DVDRip.DD2.0.x264-vetis.srt

Ako postoji vise .srt fajlova za istu epizodu (npr. fajl.srt i fajl_2.srt),
preimenuje se onaj bez _2 (smatra se boljim/primarnim).
Ako postoji samo _2 verzija, preimenuje se ta.
"""

import os
import re
from pathlib import Path


def nadji_epizodu(ime_fajla: str) -> str | None:
    """
    Izvlaci broj epizode iz imena fajla.

    Primeri:
      "Diagnosis.Murder.S06E10.Murder.x.4.DVDRip.DD2.0.x264-vetis.mkv" -> "S06E10"
      "Diagnosis Murder (1993) - S06E10 - Murder x 4 [...].srt"        -> "S06E10"
    """
    match = re.search(r'S\d{2}E\d{2}', ime_fajla, re.IGNORECASE)
    return match.group(0).upper() if match else None


def main():
    # Putanja do direktorijuma sa fajlovima
    dir_path = Path(
        r"D:\Download\Temporary files\TV Series"
        r"\Diagnosis.Murder.S06.DVDRip.DD2.0.x264-vetis[rartv]"
    )

    if not dir_path.exists():
        print(f"X Direktorijum ne postoji: {dir_path}")
        return

    # Prikupi sve .mkv i .srt fajlove (ukljucujuci poddirektorijume)
    mkv_fajlovi = list(dir_path.glob("*.mkv"))
    srt_fajlovi = list(dir_path.rglob("*.srt"))

    print(f"Pronadjeno .mkv fajlova: {len(mkv_fajlovi)}")
    print(f"Pronadjeno .srt fajlova: {len(srt_fajlovi)}")
    print()

    if not mkv_fajlovi:
        print("X Nema .mkv fajlova.")
        return

    # Mapiraj: epizoda -> .mkv fajl
    mkv_po_epizodi: dict[str, Path] = {}
    for mkv in mkv_fajlovi:
        ep = nadji_epizodu(mkv.name)
        if ep:
            mkv_po_epizodi[ep] = mkv
            print(f"  .mkv  {ep} -> {mkv.name}")

    print()

    # Mapiraj: epizoda -> lista .srt fajlova
    srt_po_epizodi: dict[str, list[Path]] = {}
    for srt in srt_fajlovi:
        ep = nadji_epizodu(srt.name)
        if ep:
            if ep not in srt_po_epizodi:
                srt_po_epizodi[ep] = []
            srt_po_epizodi[ep].append(srt)

    # Preimenuj
    preimenovano = 0
    preskoceno = 0
    greske = 0

    for ep, mkv in mkv_po_epizodi.items():
        srt_lista = srt_po_epizodi.get(ep, [])

        if not srt_lista:
            print(f"  ?  {ep}: Nema .srt fajla za {mkv.name}")
            preskoceno += 1
            continue

        # Ocekivano ime .srt fajla (isto kao .mkv samo sa .srt)
        expected_srt_name = mkv.stem + ".srt"

        # Ako vec postoji .srt sa tacno tim imenom, preskoci
        if (dir_path / expected_srt_name).exists():
            print(f"  OK {ep}: Vec postoji {expected_srt_name}")
            preskoceno += 1
            continue

        # Ako postoji vise .srt-ova, preferiraj onaj bez _2
        izabrani_srt = None
        ostali_srt = []

        for srt in srt_lista:
            if "_2.srt" in srt.name:
                ostali_srt.append(srt)
            else:
                izabrani_srt = srt  # Ako nadjemo bez _2, to je primarni

        # Ako nema bez _2, uzmi prvi sa _2
        if izabrani_srt is None and ostali_srt:
            izabrani_srt = ostali_srt[0]
            ostali_srt.remove(izabrani_srt)

        if izabrani_srt is None:
            print(f"  ?  {ep}: Nema .srt fajlova")
            preskoceno += 1
            continue

        novi_put = dir_path / expected_srt_name

        try:
            # Preimenuj (pomeri) .srt da odgovara .mkv imenu
            os.rename(str(izabrani_srt), str(novi_put))
            print(f"  +  {ep}: {izabrani_srt.name}")
            print(f"         -> {expected_srt_name}")
            preimenovano += 1
        except Exception as e:
            print(f"  -  {ep}: Greska pri preimenovanju: {e}")
            greske += 1

    print()
    print("=" * 60)
    print(f"  Preimenovano: {preimenovano}")
    print(f"  Preskoceno (ima ili nema): {preskoceno}")
    print(f"  Greske: {greske}")
    print("=" * 60)
    print()
    print("Ako zelis da proveris sta je preimenovano, otvori folder.")
    print("Stari fajlovi su preimenovani (ne kopirani), nema duplikata.")


if __name__ == "__main__":
    main()
