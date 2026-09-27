"""Notizie per argomento da feed RSS: unite, deduplicate, ordinate dalla più recente."""
from __future__ import annotations

import calendar
import logging
import re
import time

import feedparser

log = logging.getLogger(__name__)


def _normalizza(titolo: str) -> str:
    return re.sub(r"\W+", " ", titolo.lower()).strip()[:60]


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
            articoli.append({"titolo": e.title.strip(), "link": e.get("link", ""), "ts": quando})
    return sorted(articoli, key=lambda a: a["ts"], reverse=True)


def sezioni(cfg: dict, tz: str, oggi) -> list[str]:
    """Una sezione per argomento, così lo split in più messaggi resta pulito."""
    out, visti = [], set()  # visti condiviso: niente doppioni tra argomenti
    for arg in cfg["argomenti"]:
        n = arg.get("per_argomento", cfg.get("per_argomento", 5))
        articoli = _articoli(arg["feed"], cfg.get("max_ore", 36), visti)[:n]
        visti.update(_normalizza(a["titolo"]) for a in articoli)
        if not articoli:
            continue
        righe = [f"*{arg['nome']}*"]
        for a in articoli:
            righe.append(f"• {a['titolo']}")
            if arg.get("link", True) and a["link"]:
                righe.append(f"  {a['link']}")
        out.append("\n".join(righe))
    return out
