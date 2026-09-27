"""Appuntamenti di oggi dal link iCal privato di Google Calendar."""
from __future__ import annotations

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events
import requests


def _eventi(url: str, giorno: date, tz: ZoneInfo) -> list[tuple]:
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    cal = icalendar.Calendar.from_ical(r.content)
    eventi = []
    for ev in recurring_ical_events.of(cal).at(giorno):
        inizio = ev["DTSTART"].dt
        fine = ev["DTEND"].dt if "DTEND" in ev else None
        titolo = str(ev.get("SUMMARY", "(senza titolo)"))
        luogo = str(ev.get("LOCATION", "")).split(",")[0].strip()
        if isinstance(inizio, datetime):
            inizio = inizio.astimezone(tz) if inizio.tzinfo else inizio.replace(tzinfo=tz)
            fine = fine.astimezone(tz) if isinstance(fine, datetime) and fine.tzinfo else fine
            eventi.append((inizio.strftime("%H:%M"), fine.strftime("%H:%M") if fine else "", titolo, luogo))
        else:  # evento di tutto il giorno
            eventi.append(("", "", titolo, luogo))
    return eventi


def sezione(cfg: dict, tz_nome: str, oggi: datetime) -> str | None:
    urls = [u.strip() for u in os.environ.get("GOOGLE_CALENDAR_ICS", "").split(",") if u.strip()]
    if not urls:
        return None  # agenda non configurata: sezione saltata in silenzio
    tz = ZoneInfo(tz_nome)
    eventi = sorted(e for u in urls for e in _eventi(u, oggi.date(), tz))

    righe = ["*📅 Agenda di oggi*"]
    if not eventi:
        righe.append("Nessun impegno in calendario 🎉")
    for inizio, fine, titolo, luogo in eventi:
        quando = f"{inizio}–{fine}" if inizio else "Tutto il giorno"
        riga = f"• {quando} {titolo}"
        if luogo and cfg.get("mostra_luogo", True):
            riga += f" 📍{luogo}"
        righe.append(riga)
    return "\n".join(righe)
