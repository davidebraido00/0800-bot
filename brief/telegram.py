"""Invio su Telegram con la Bot API ufficiale (parse_mode HTML).

Configurazione: TELEGRAM_BOT_TOKEN (da @BotFather) e TELEGRAM_CHAT_ID.
Per trovare il chat id: scrivi /start al bot, poi `python -m brief.telegram`.
"""
from __future__ import annotations

import html
import os
import re
import sys
import time
from pathlib import Path

import requests

LIMITE = 4096  # caratteri visibili per messaggio, dopo aver tolto i tag HTML
NUOVO_MESSAGGIO = "\x00"  # blocco segnaposto: forza l'inizio di un nuovo messaggio


def _api(metodo: str, **dati) -> dict:
    token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    r = requests.post(f"https://api.telegram.org/bot{token}/{metodo}", json=dati, timeout=30)
    risposta = r.json()
    if not risposta.get("ok"):
        raise RuntimeError(f"Telegram {metodo}: {risposta.get('description', r.text[:200])}")
    return risposta["result"]


def _visibili(testo_html: str) -> int:
    """Telegram conta il limite sul testo dopo aver interpretato i tag, quindi i link non pesano."""
    return len(html.unescape(re.sub(r"<[^>]+>", "", testo_html)))


def impacchetta(blocchi: list[str], limite: int = LIMITE - 96) -> list[str]:
    """Unisce i blocchi in messaggi sotto il limite, senza mai spezzare un blocco (e i suoi tag)."""
    messaggi, corrente = [], ""
    for b in blocchi:
        if b == NUOVO_MESSAGGIO:
            if corrente:
                messaggi.append(corrente)
            corrente = ""
            continue
        candidato = f"{corrente}\n\n{b}" if corrente else b
        if corrente and _visibili(candidato) > limite:
            messaggi.append(corrente)
            corrente = b
        else:
            corrente = candidato
    if corrente:
        messaggi.append(corrente)
    return messaggi


def configurato() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def invia(messaggi: list[str]) -> None:
    for i, testo in enumerate(messaggi):
        if i:
            time.sleep(1)  # Telegram consiglia al massimo ~1 messaggio al secondo nella stessa chat
        _api(
            "sendMessage",
            chat_id=os.environ["TELEGRAM_CHAT_ID"].strip(),
            text=testo,
            parse_mode="HTML",
            link_preview_options={"is_disabled": True},
            disable_notification=i > 0,  # suona solo il primo messaggio
        )


def _configura() -> int:
    """Trova il chat id dagli ultimi messaggi ricevuti dal bot e lo salva in .env."""
    from dotenv import load_dotenv

    env = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env)
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("Manca TELEGRAM_BOT_TOKEN nel file .env (te lo dà @BotFather).")
        return 1
    bot = _api("getMe")
    print(f"Bot: @{bot['username']} ({bot['first_name']})")
    chat = {}
    for u in _api("getUpdates"):
        msg = u.get("message") or u.get("edited_message") or {}
        if msg.get("chat", {}).get("type") == "private":
            c = msg["chat"]
            chat[c["id"]] = c.get("first_name", "") + (f" (@{c['username']})" if c.get("username") else "")
    if not chat:
        print(f"Nessun messaggio trovato: apri https://t.me/{bot['username']}, premi Avvia (/start) e riprova.")
        return 1
    chat_id, nome = list(chat.items())[-1]
    print(f"Chat trovata: {nome} → {chat_id}")
    testo = env.read_text(encoding="utf-8") if env.exists() else ""
    if re.search(r"^TELEGRAM_CHAT_ID=.*$", testo, flags=re.M):
        testo = re.sub(r"^TELEGRAM_CHAT_ID=.*$", f"TELEGRAM_CHAT_ID={chat_id}", testo, flags=re.M)
    else:
        testo += f"\nTELEGRAM_CHAT_ID={chat_id}\n"
    env.write_text(testo, encoding="utf-8")
    print("Salvato in .env come TELEGRAM_CHAT_ID.")
    return 0


if __name__ == "__main__":
    sys.exit(_configura())
