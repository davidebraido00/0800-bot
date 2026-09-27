"""Crescita personale: inglese del giorno, pillola del giorno, obiettivi settimanali dal calendario."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import agenda

DATA = Path(__file__).resolve().parent.parent / "data"


def _del_giorno(file: str, oggi: datetime) -> dict | None:
    voci = yaml.safe_load((DATA / file).read_text(encoding="utf-8")) or []
    # Rotazione deterministica: stesso giorno, stessa voce; giorno dopo, voce successiva
    return voci[oggi.date().toordinal() % len(voci)] if voci else None


def _conta(eventi: list[dict], parole: list[str]) -> int:
    parole = [p.lower() for p in parole]
    return sum(any(p in e["titolo"].lower() for p in parole) for e in eventi)


def _obiettivi(cfg: list[dict], tz: str, oggi: datetime) -> list[dict]:
    if not cfg or not agenda.calendari():
        return []
    giorno = oggi.date()
    lunedi = giorno - timedelta(days=giorno.weekday())
    settimana = agenda.eventi_tra(lunedi - timedelta(days=7), lunedi + timedelta(days=7), ZoneInfo(tz))
    out = []
    for ob in cfg:
        parole = ob.get("parole", [ob["nome"]])
        prima = [e for e in settimana if e["giorno"] < lunedi]
        questa = [e for e in settimana if e["giorno"] >= lunedi]
        out.append({
            "nome": ob["nome"],
            "emoji": ob.get("emoji", "🎯"),
            "obiettivo": ob["a_settimana"],
            "fatte": _conta([e for e in questa if e["giorno"] < giorno], parole),
            "oggi": _conta([e for e in questa if e["giorno"] == giorno], parole),
            "in_programma": _conta([e for e in questa if e["giorno"] > giorno], parole),
            # Il lunedì mostriamo com'è andata la settimana appena chiusa
            "settimana_scorsa": _conta(prima, parole) if giorno.weekday() == 0 else None,
        })
    return out


def raccogli(cfg: dict, tz: str, oggi: datetime) -> dict:
    return {
        "inglese": _del_giorno("inglese.yaml", oggi) if cfg.get("inglese", True) else None,
        "pillola": _del_giorno("pillole.yaml", oggi) if cfg.get("pillola", True) else None,
        "obiettivi": _obiettivi(cfg.get("obiettivi") or [], tz, oggi),
    }


def whatsapp(c: dict) -> str:
    righe = ["*🌱 Crescita personale*"]
    if c["inglese"]:
        i = c["inglese"]
        righe += ["", f"🇬🇧 *{i['frase']}* _({i['tipo']})_", f"= {i['significato']}", f"_\"{i['esempio']}\"_"]
    if c["pillola"]:
        p = c["pillola"]
        righe += ["", f"{p['emoji']} *{p['titolo']}*", p["testo"]]
    if c["obiettivi"]:
        righe += ["", "*🎯 Obiettivi della settimana*"]
        for o in c["obiettivi"]:
            riga = f"{o['emoji']} {o['nome']}: {o['fatte']}/{o['obiettivo']} fatte"
            extra = []
            if o["oggi"]:
                extra.append(f"{o['oggi']} oggi")
            if o["in_programma"]:
                extra.append(f"{o['in_programma']} in programma")
            if extra:
                riga += " · " + ", ".join(extra)
            righe.append(riga)
            if o["settimana_scorsa"] is not None:
                esito = "✅" if o["settimana_scorsa"] >= o["obiettivo"] else "➖"
                righe.append(f"  settimana scorsa: {o['settimana_scorsa']}/{o['obiettivo']} {esito}")
    return "\n".join(righe)
