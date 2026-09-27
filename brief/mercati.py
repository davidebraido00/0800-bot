"""Quotazioni da Yahoo Finance: prezzo, variazione giornaliera e a 5 sedute."""
from __future__ import annotations

import tempfile

import yfinance as yf

from .fmt import GIORNI_BREVI, numero, perc

# Cache privata per evitare "database is locked" con altri processi yfinance
yf.set_tz_cache_location(tempfile.mkdtemp(prefix="yf-"))


def _riga(nome: str, serie) -> str:
    serie = serie.dropna()
    if len(serie) < 2:
        return f"▫️ {nome}: n.d."
    ultimo = float(serie.iloc[-1])
    var1 = (ultimo / float(serie.iloc[-2]) - 1) * 100
    var5 = (ultimo / float(serie.iloc[-6]) - 1) * 100 if len(serie) >= 6 else None
    pallino = "🟢" if var1 > 0.05 else "🔴" if var1 < -0.05 else "⚪"
    decimali = 4 if ultimo < 10 else 2
    riga = f"{pallino} {nome}: {numero(ultimo, decimali)} ({perc(var1)}"
    if var5 is not None:
        riga += f" · 5g {perc(var5)}"
    return riga + ")"


def sezione(cfg: dict, tz: str, oggi) -> str:
    gruppi = cfg["gruppi"]
    tickers = sorted({sym for g in gruppi.values() for sym in g.values()})
    close = yf.download(tickers, period="1mo", interval="1d", progress=False,
                        auto_adjust=True, threads=False)["Close"]

    out = []
    for i, (titolo, simboli) in enumerate(gruppi.items()):
        # Data dell'ultima chiusura del primo simbolo del gruppo (utile nel weekend)
        primo = close[next(iter(simboli.values()))].dropna()
        data = f" _chiusura {GIORNI_BREVI[primo.index[-1].weekday()]} {primo.index[-1]:%d/%m}_" if len(primo) else ""
        intestazione = f"*📈 Mercati*\n\n*{titolo}*{data}" if i == 0 else f"*{titolo}*{data}"
        righe = [intestazione] + [_riga(nome, close[sym]) for nome, sym in simboli.items()]
        out.append("\n".join(righe))
    out.append("_Dati informativi, non sono consigli d'investimento._")
    return "\n\n".join(out)
