"""Compone il messaggio del mattino e lo invia su WhatsApp.

Uso:
    python main.py --dry-run          # stampa i messaggi senza inviarli
    python main.py                    # invia
    python main.py --solo-alle 8      # invia solo se nel fuso configurato sono le 8 (per GitHub Actions)
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

from brief import agenda, meteo, mercati, news, whatsapp
from brief.fmt import GIORNI, MESI

# Ogni sezione riceve (config della sezione, timezone, datetime di oggi)
# e restituisce una stringa, una lista di stringhe o None per saltarla.
SEZIONI = {
    "meteo": meteo.sezione,
    "agenda": agenda.sezione,
    "mercati": mercati.sezione,
    "news": news.sezioni,
}

log = logging.getLogger("brief")


def componi(cfg: dict, oggi: datetime) -> list[str]:
    blocchi = [f"☕ *Buongiorno! {GIORNI[oggi.weekday()]} {oggi.day} {MESI[oggi.month - 1]}*"]
    for chiave in cfg.get("ordine", SEZIONI):
        if chiave not in cfg:
            continue
        try:
            risultato = SEZIONI[chiave](cfg[chiave] or {}, cfg["timezone"], oggi)
        except Exception:  # una sezione rotta non deve bloccare le altre
            log.exception("Sezione %s fallita", chiave)
            risultato = f"_({chiave}: dati non disponibili oggi)_"
        if isinstance(risultato, str):
            blocchi.append(risultato)
        elif risultato:
            blocchi.extend(risultato)
    return blocchi


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="stampa senza inviare")
    ap.add_argument("--solo-alle", type=int, metavar="ORA", help="esci se non è quest'ora locale")
    ap.add_argument("--config", default=Path(__file__).with_name("config.yaml"))
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    oggi = datetime.now(ZoneInfo(cfg["timezone"]))

    if args.solo_alle is not None and oggi.hour != args.solo_alle:
        log.info("Sono le %s, non le %s: niente invio.", oggi.strftime("%H:%M"), args.solo_alle)
        return 0

    wa = cfg.get("whatsapp") or {}
    messaggi = whatsapp.impacchetta(componi(cfg, oggi), wa.get("max_caratteri", 1500))

    if args.dry_run:
        for i, m in enumerate(messaggi, 1):
            print(f"\n──────── messaggio {i}/{len(messaggi)} · {len(m)} caratteri ────────\n{m}")
        return 0
    whatsapp.invia(messaggi, wa.get("pausa_secondi", 10))
    log.info("Inviati %d messaggi.", len(messaggi))
    return 0


if __name__ == "__main__":
    sys.exit(main())
