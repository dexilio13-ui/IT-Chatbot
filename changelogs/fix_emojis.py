#!/usr/bin/env python3
"""Dodaje emoji ikonice u create_uputstvo.py."""
import sys
from pathlib import Path

path = Path(__file__).resolve().parent / "create_uputstvo.py"
content = path.read_text(encoding="utf-8")

content = content.replace(
    'r = p.add_run("mentor sledeci tekst:")',
    'r = p.add_run("\U0001f4dd \u0160ta govori\u0161 mentoru:")',
)

content = content.replace(
    'add_label(doc, "Sta da pokazes u kodu (Ctrl+F): ", "")',
    'add_label(doc, "\U0001f50d \u0160ta da poka\u017ee\u0161 u kodu (Ctrl+F): ", "")',
)

path.write_text(content, encoding="utf-8")
print("Emojis added successfully!")
