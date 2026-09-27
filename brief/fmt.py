"""Piccoli helper di formattazione all'italiana."""
from __future__ import annotations

import time


def numero(x: float, decimali: int = 2) -> str:
    """1234567.891 -> '1.234.567,89'"""
    s = f"{x:,.{decimali}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def perc(x: float) -> str:
    return f"{x:+.1f}%".replace(".", ",")


def fa_quanto(ts: float) -> str:
    """Timestamp -> '3 ore fa'"""
    minuti = int((time.time() - ts) / 60)
    if minuti < 60:
        return f"{max(minuti, 1)} min fa"
    ore = minuti // 60
    return "1 ora fa" if ore == 1 else f"{ore} ore fa" if ore < 24 else "ieri"


GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
GIORNI_BREVI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
        "agosto", "settembre", "ottobre", "novembre", "dicembre"]
