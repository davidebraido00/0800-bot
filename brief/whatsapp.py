"""Invio messaggi WhatsApp. Provider scelto con la variabile WHATSAPP_PROVIDER."""
from __future__ import annotations

import os
import re
import time

import requests


def _callmebot(testo: str) -> None:
    # Gratuito, per uso personale: https://www.callmebot.com/blog/free-api-whatsapp-messages/
    # CallMeBot elimina l'apostrofo dritto: lo sostituiamo con quello tipografico.
    testo = testo.replace("'", "\u2019")
    r = requests.get(
        "https://api.callmebot.com/whatsapp.php",
        params={
            "phone": os.environ["WHATSAPP_TO"],
            "text": testo,
            "apikey": os.environ["CALLMEBOT_APIKEY"],
        },
        timeout=60,
    )
    r.raise_for_status()
    # CallMeBot risponde sempre 200: l'esito è nel testo (es. limite di 50 messaggi ogni 4 ore)
    if "queued" not in r.text.lower():
        raise RuntimeError(f"CallMeBot: {re.sub(r'<[^>]+>', ' ', r.text)[:300]}")


def _twilio(testo: str) -> None:
    sid = os.environ["TWILIO_ACCOUNT_SID"]
    r = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        auth=(sid, os.environ["TWILIO_AUTH_TOKEN"]),
        data={
            "From": f"whatsapp:{os.environ['TWILIO_FROM']}",
            "To": f"whatsapp:{os.environ['WHATSAPP_TO']}",
            "Body": testo,
        },
        timeout=30,
    )
    r.raise_for_status()


PROVIDERS = {"callmebot": _callmebot, "twilio": _twilio}


def impacchetta(sezioni: list[str], max_caratteri: int) -> list[str]:
    """Unisce le sezioni in messaggi senza superare max_caratteri e senza spezzarle a metà."""
    # Una sezione da sola troppo lunga viene spezzata riga per riga
    pezzi = []
    for s in sezioni:
        if len(s) <= max_caratteri:
            pezzi.append(s)
            continue
        # Le righe indentate (es. il link di una notizia) restano attaccate alla precedente
        righe = []
        for riga in s.split("\n"):
            if riga.startswith("  ") and righe:
                righe[-1] += "\n" + riga
            else:
                righe.append(riga)
        blocco = ""
        for riga in righe:
            if blocco and len(blocco) + 1 + len(riga) > max_caratteri:
                pezzi.append(blocco)
                blocco = riga
            else:
                blocco = f"{blocco}\n{riga}" if blocco else riga
        pezzi.append(blocco)

    messaggi, corrente = [], ""
    for s in pezzi:
        if corrente and len(corrente) + 2 + len(s) > max_caratteri:
            messaggi.append(corrente)
            corrente = s
        else:
            corrente = f"{corrente}\n\n{s}" if corrente else s
    if corrente:
        messaggi.append(corrente)
    return messaggi


def invia(messaggi: list[str], pausa_secondi: float) -> None:
    fn = PROVIDERS[os.environ.get("WHATSAPP_PROVIDER", "callmebot").lower()]
    for i, m in enumerate(messaggi):
        if i:
            # CallMeBot unisce (e tronca) i messaggi ravvicinati: li distanziamo
            time.sleep(pausa_secondi)
        fn(m)
