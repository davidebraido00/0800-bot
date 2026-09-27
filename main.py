"""0800: raccoglie i dati del mattino e li invia su WhatsApp e via email.

Uso:
    python main.py --dry-run                # anteprima: WhatsApp a schermo + anteprima.html
    python main.py                          # invia su tutti i canali configurati
    python main.py --canali email           # invia solo l'email (utile per i test)
    python main.py --solo-alle 8            # invia solo se nel fuso configurato sono le 8 (GitHub Actions)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv

from brief import agenda, crescita, meteo, mercati, news, posta, whatsapp
from brief.fmt import GIORNI, MESI

# Ogni modulo espone raccogli(cfg, tz, oggi) -> dati | None e whatsapp(dati) -> str | list[str]
SEZIONI = {"meteo": meteo, "agenda": agenda, "mercati": mercati, "crescita": crescita, "news": news}

log = logging.getLogger("0800")


def raccogli(cfg: dict, oggi: datetime) -> tuple[dict, list[str]]:
    dati, errori = {}, []
    for chiave in cfg["ordine"]:
        if chiave not in cfg:
            continue
        try:
            dati[chiave] = SEZIONI[chiave].raccogli(cfg[chiave] or {}, cfg["timezone"], oggi)
        except Exception:  # una sezione rotta non deve bloccare le altre
            log.exception("Sezione %s fallita", chiave)
            dati[chiave] = None
            errori.append(chiave)
    return dati, errori


def blocchi_whatsapp(dati: dict, errori: list[str], oggi: datetime) -> list[str]:
    blocchi = [f"☕ *Buongiorno! {GIORNI[oggi.weekday()]} {oggi.day} {MESI[oggi.month - 1]}*"]
    for chiave, d in dati.items():
        if chiave in errori:
            blocchi.append(f"_({chiave}: dati non disponibili oggi)_")
        elif d:
            testo = SEZIONI[chiave].whatsapp(d)
            blocchi.extend([testo] if isinstance(testo, str) else testo)
    return blocchi


def whatsapp_configurato() -> bool:
    if os.environ.get("WHATSAPP_PROVIDER", "callmebot").lower() == "twilio":
        return bool(os.environ.get("TWILIO_AUTH_TOKEN"))
    return bool(os.environ.get("CALLMEBOT_APIKEY"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="anteprima senza inviare")
    ap.add_argument("--canali", help="es. 'email' o 'whatsapp,email' (default: da config.yaml)")
    ap.add_argument("--solo-alle", type=int, metavar="ORA", help="esci se non è quest'ora locale")
    ap.add_argument("--config", default=Path(__file__).with_name("config.yaml"))
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv(Path(__file__).with_name(".env"))
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    oggi = datetime.now(ZoneInfo(cfg["timezone"]))

    if args.solo_alle is not None and oggi.hour != args.solo_alle:
        log.info("Sono le %s, non le %s: niente invio.", oggi.strftime("%H:%M"), args.solo_alle)
        return 0

    canali = args.canali.split(",") if args.canali else cfg.get("canali", ["whatsapp"])
    dati, errori = raccogli(cfg, oggi)
    wa = cfg.get("whatsapp") or {}
    blocchi = blocchi_whatsapp(dati, errori, oggi)
    messaggi = whatsapp.impacchetta(blocchi, wa.get("max_caratteri", 1500))

    if args.dry_run:
        for i, m in enumerate(messaggi, 1):
            print(f"\n──────── messaggio {i}/{len(messaggi)} · {len(m)} caratteri ────────\n{m}")
        oggetto, html, _ = posta.componi(dati, errori, oggi, cfg, inline=True)
        anteprima = Path(__file__).with_name("anteprima.html")
        anteprima.write_text(html, encoding="utf-8")
        print(f"\n──────── email ────────\nOggetto: {oggetto}\nAnteprima: {anteprima}")
        return 0

    falliti = []
    if "whatsapp" in canali:
        if not whatsapp_configurato():
            log.warning("WhatsApp non configurato: salto.")
        else:
            try:
                whatsapp.invia(messaggi, wa.get("pausa_secondi", 10))
                log.info("WhatsApp: inviati %d messaggi.", len(messaggi))
            except Exception:
                log.exception("Invio WhatsApp fallito")
                falliti.append("whatsapp")
    if "email" in canali:
        if not posta.configurata():
            log.warning("Email non configurata (EMAIL_FROM / EMAIL_APP_PASSWORD): salto.")
        else:
            try:
                oggetto, html, immagini = posta.componi(dati, errori, oggi, cfg)
                posta.invia(oggetto, html, "\n\n".join(blocchi), immagini)
                log.info("Email inviata: %s", oggetto)
            except Exception:
                log.exception("Invio email fallito")
                falliti.append("email")
    return 1 if falliti else 0  # exit code ≠ 0 -> GitHub ti avvisa via email


if __name__ == "__main__":
    sys.exit(main())
