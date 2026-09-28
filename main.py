"""0800: raccoglie i dati del mattino e li invia su WhatsApp e via email.

Uso:
    python main.py --dry-run                # anteprima: WhatsApp a schermo + anteprima.html
    python main.py                          # invia su tutti i canali configurati
    python main.py --canali email           # invia solo l'email (utile per i test)
    python main.py --alle 8 --offset 2      # invio programmato (GitHub Actions): attende le 8 se in anticipo
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
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


def attendi_orario(tz: ZoneInfo, ora: int, offset: int | None) -> bool:
    """Per l'avvio programmato: False se questo avvio va saltato, altrimenti attende l'orario.

    GitHub avvia i cron con ritardi anche lunghi: partiamo in anticipo e aspettiamo qui.
    """
    adesso = datetime.now(tz)
    if offset is not None and adesso.utcoffset() != timedelta(hours=offset):
        # Ci sono due cron (ora legale e solare): ognuno gira solo nel suo periodo dell'anno
        log.info("Avvio per UTC+%d, ma ora siamo a UTC%s: salto.", offset, adesso.strftime("%z"))
        return False
    obiettivo = adesso.replace(hour=ora, minute=0, second=0, microsecond=0)
    if not obiettivo - timedelta(hours=2) <= adesso <= obiettivo + timedelta(hours=3):
        log.info("Sono le %s, fuori dalla finestra delle %d: salto.", adesso.strftime("%H:%M"), ora)
        return False
    attesa = (obiettivo - timedelta(minutes=1) - adesso).total_seconds()  # 1 min per raccogliere i dati
    if attesa > 0:
        log.info("Sono le %s: attendo fino alle %02d:00.", adesso.strftime("%H:%M"), ora)
        time.sleep(attesa)
    elif adesso > obiettivo + timedelta(minutes=5):
        log.info("Avvio alle %s, dopo le %02d:00: invio subito.", adesso.strftime("%H:%M"), ora)
    return True


def whatsapp_configurato() -> bool:
    if os.environ.get("WHATSAPP_PROVIDER", "callmebot").lower() == "twilio":
        return bool(os.environ.get("TWILIO_AUTH_TOKEN"))
    return bool(os.environ.get("CALLMEBOT_APIKEY"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="anteprima senza inviare")
    ap.add_argument("--canali", help="es. 'email' o 'whatsapp,email' (default: da config.yaml)")
    ap.add_argument("--alle", type=int, metavar="ORA", help="invio programmato: attende quest'ora locale")
    ap.add_argument("--offset", type=int, metavar="ORE", help="con --alle: differenza da UTC attesa (2 legale, 1 solare)")
    ap.add_argument("--segna", metavar="FILE", help="crea questo file se almeno un canale è stato inviato")
    ap.add_argument("--config", default=Path(__file__).with_name("config.yaml"))
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv(Path(__file__).with_name(".env"))
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    tz = ZoneInfo(cfg["timezone"])
    if args.alle is not None and not attendi_orario(tz, args.alle, args.offset):
        return 0
    oggi = datetime.now(tz)

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

    inviati, falliti = [], []
    if "whatsapp" in canali:
        if not whatsapp_configurato():
            log.warning("WhatsApp non configurato: salto.")
        else:
            try:
                whatsapp.invia(messaggi, wa.get("pausa_secondi", 10))
                log.info("WhatsApp: inviati %d messaggi.", len(messaggi))
                inviati.append("whatsapp")
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
                inviati.append("email")
            except Exception:
                log.exception("Invio email fallito")
                falliti.append("email")
    if args.segna and inviati:
        Path(args.segna).write_text(f"{oggi:%Y-%m-%d} {','.join(inviati)}\n")
    if not inviati and not falliti:
        log.error("Nessun canale configurato: niente è stato inviato.")
        return 1
    return 1 if falliti else 0  # exit code ≠ 0 -> GitHub ti avvisa via email


if __name__ == "__main__":
    sys.exit(main())
