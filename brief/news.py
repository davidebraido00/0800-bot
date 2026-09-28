"""Notizie per argomento da feed RSS: unite, deduplicate, ordinate dalla più recente."""
from __future__ import annotations

import calendar
import logging
import re
import time
from urllib.parse import urlparse

import feedparser

from .fmt import esc, fa_quanto, href

log = logging.getLogger(__name__)

FONTI = {
    "ansa.it": "ANSA",
    "ilsole24ore.com": "Il Sole 24 Ore",
    "hwupgrade.it": "HWUpgrade",
}


def _normalizza(titolo: str) -> str:
    return re.sub(r"\W+", " ", titolo.lower()).strip()[:60]


def _fonte_e_titolo(titolo: str, link: str) -> tuple[str, str]:
    dominio = urlparse(link).netloc.removeprefix("www.")
    if dominio == "news.google.com" and " - " in titolo:
        # Google News mette la fonte in coda al titolo: "Titolo - Fonte"
        titolo, fonte = titolo.rsplit(" - ", 1)
        return fonte, titolo
    return FONTI.get(dominio, dominio), titolo


def _articoli(feed_urls: list[str], max_ore: float, gia_mostrati: set) -> list[dict]:
    limite = time.time() - max_ore * 3600
    visti, articoli = set(gia_mostrati), []
    for url in feed_urls:
        parsed = feedparser.parse(url)
        if not parsed.entries:
            log.warning("Feed vuoto o irraggiungibile: %s", url)
        for e in parsed.entries:
            ts = e.get("published_parsed") or e.get("updated_parsed")
            quando = calendar.timegm(ts) if ts else 0
            chiave = _normalizza(e.get("title", ""))
            if not chiave or chiave in visti or (ts and quando < limite):
                continue
            visti.add(chiave)
            link = e.get("link", "")
            fonte, titolo = _fonte_e_titolo(e.title.strip(), link)
            articoli.append({"titolo": titolo, "fonte": fonte, "link": link, "ts": quando})
    return sorted(articoli, key=lambda a: a["ts"], reverse=True)


def raccogli(cfg: dict, tz: str, oggi) -> dict:
    argomenti, visti = [], set()  # visti condiviso: niente doppioni tra argomenti
    for arg in cfg["argomenti"]:
        n = arg.get("per_argomento", cfg.get("per_argomento", 5))
        articoli = _articoli(arg["feed"], cfg.get("max_ore", 36), visti)[:n]
        visti.update(_normalizza(a["titolo"]) for a in articoli)
        if articoli:
            argomenti.append({"nome": arg["nome"], "link": arg.get("link", True), "articoli": articoli})
    return {"argomenti": argomenti}


def whatsapp(n: dict) -> list[str]:
    """Un blocco per argomento, così lo split in più messaggi resta pulito."""
    out = []
    for arg in n["argomenti"]:
        righe = [f"*{arg['nome']}*"]
        for a in arg["articoli"]:
            righe.append(f"• {a['titolo']} - {a['fonte']}")
            if arg["link"] and a["link"]:
                righe.append(f"  {a['link']}")
        out.append("\n".join(righe))
    return out


def telegram(n: dict) -> list[str]:
    """Le notizie in un messaggio a parte: un blocco per argomento, titoli cliccabili, elenco espandibile."""
    from .telegram import NUOVO_MESSAGGIO

    out = [NUOVO_MESSAGGIO, "<b>📰 Notizie</b> <i>· tocca un elenco per espanderlo</i>"]
    for arg in n["argomenti"]:
        voci = []
        for a in arg["articoli"]:
            titolo = f'<a href="{href(a["link"])}">{esc(a["titolo"])}</a>' if a["link"] else esc(a["titolo"])
            quando = f" · {fa_quanto(a['ts'])}" if a["ts"] else ""
            voci.append(f"• {titolo} <i>— {esc(a['fonte'])}{quando}</i>")
        out.append(f"<b>{esc(arg['nome'])}</b>\n<blockquote expandable>" + "\n".join(voci) + "</blockquote>")
    return out
