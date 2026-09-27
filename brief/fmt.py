"""Piccoli helper di formattazione all'italiana."""
from __future__ import annotations


def numero(x: float, decimali: int = 2) -> str:
    """1234567.891 -> '1.234.567,89'"""
    s = f"{x:,.{decimali}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def perc(x: float) -> str:
    return f"{x:+.1f}%".replace(".", ",")


GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
GIORNI_BREVI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
