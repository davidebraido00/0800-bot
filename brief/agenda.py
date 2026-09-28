"""Appuntamenti dal link iCal privato di Google Calendar."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events
import requests

from .fmt import esc


def calendari() -> list[str]:
    return [u.strip() for u in os.environ.get("GOOGLE_CALENDAR_ICS", "").split(",") if u.strip()]


@lru_cache(maxsize=None)
def _scarica(url: str) -> icalendar.Calendar:
    # In cache: agenda e obiettivi leggono gli stessi calendari una volta sola
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return icalendar.Calendar.from_ical(r.content)


def eventi_tra(inizio: date, fine: date, tz: ZoneInfo) -> list[dict]:
    """Eventi di tutti i calendari con inizio in [inizio, fine), ordinati."""
    eventi = []
    for url in calendari():
        for ev in recurring_ical_events.of(_scarica(url)).between(inizio, fine):
            start = ev["DTSTART"].dt
            end = ev["DTEND"].dt if "DTEND" in ev else None
            e = {
                "titolo": str(ev.get("SUMMARY", "(senza titolo)")),
                "luogo": str(ev.get("LOCATION", "")).split(",")[0].strip(),
                "tutto_il_giorno": not isinstance(start, datetime),
                "inizio": "",
                "fine": "",
            }
            if isinstance(start, datetime):
                start = start.astimezone(tz) if start.tzinfo else start.replace(tzinfo=tz)
                e["giorno"] = start.date()
                e["inizio"] = start.strftime("%H:%M")
                if isinstance(end, datetime):
                    e["fine"] = (end.astimezone(tz) if end.tzinfo else end).strftime("%H:%M")
            else:
                e["giorno"] = start
            eventi.append(e)
    return sorted(eventi, key=lambda e: (e["giorno"], not e["tutto_il_giorno"], e["inizio"]))


def raccogli(cfg: dict, tz: str, oggi: datetime) -> dict | None:
    if not calendari():
        return None  # agenda non configurata: sezione saltata in silenzio
    giorno = oggi.date()
    return {
        "eventi": eventi_tra(giorno, giorno + timedelta(days=1), ZoneInfo(tz)),
        "mostra_luogo": cfg.get("mostra_luogo", True),
    }


def whatsapp(a: dict) -> str:
    righe = ["*📅 Agenda di oggi*"]
    if not a["eventi"]:
        righe.append("Nessun impegno in calendario 🎉")
    for e in a["eventi"]:
        quando = f"{e['inizio']}–{e['fine']}" if e["inizio"] else "Tutto il giorno"
        riga = f"• {quando} {e['titolo']}"
        if e["luogo"] and a["mostra_luogo"]:
            riga += f" 📍{e['luogo']}"
        righe.append(riga)
    return "\n".join(righe)


def telegram(a: dict) -> str:
    righe = ["<b>📅 Agenda di oggi</b>"]
    if not a["eventi"]:
        righe.append("Nessun impegno in calendario 🎉")
    for e in a["eventi"]:
        quando = f"{e['inizio']}–{e['fine']}" if e["inizio"] else "Tutto il giorno"
        riga = f"• <b>{quando}</b> {esc(e['titolo'])}"
        if e["luogo"] and a["mostra_luogo"]:
            riga += f" <i>📍 {esc(e['luogo'])}</i>"
        righe.append(riga)
    return "\n".join(righe)
