"""Quotazioni da Yahoo Finance: prezzo, variazione a 1 giorno, 5 sedute e 1 mese."""
from __future__ import annotations

import tempfile

import yfinance as yf

from .fmt import GIORNI_BREVI, esc, numero, perc

# Cache privata per evitare "database is locked" con altri processi yfinance
yf.set_tz_cache_location(tempfile.mkdtemp(prefix="yf-"))


def _var(serie, sedute: int):
    return (serie[-1] / serie[-1 - sedute] - 1) * 100 if len(serie) > sedute else None


def raccogli(cfg: dict, tz: str, oggi) -> dict:
    gruppi = cfg["gruppi"]
    tickers = sorted({sym for g in gruppi.values() for sym in g.values()})
    close = yf.download(tickers, period="1mo", interval="1d", progress=False,
                        auto_adjust=True, threads=False)["Close"]
    out = []
    for titolo, simboli in gruppi.items():
        righe, data = [], None
        for nome, sym in simboli.items():
            s = close[sym].dropna()
            serie = [float(x) for x in s]
            if data is None and len(s):
                data = s.index[-1].date()
            righe.append({
                "nome": nome,
                "simbolo": sym,
                "serie": serie,
                "prezzo": serie[-1] if serie else None,
                "decimali": 4 if serie and serie[-1] < 10 else 2,
                "var1": _var(serie, 1),
                "var5": _var(serie, 5),
                "var1m": (serie[-1] / serie[0] - 1) * 100 if len(serie) > 1 else None,
            })
        out.append({"titolo": titolo, "data": data, "righe": righe})
    return {"gruppi": out}


def migliore_peggiore(m: dict):
    righe = [r for g in m["gruppi"] for r in g["righe"] if r["var1"] is not None]
    if not righe:
        return None, None
    ordinate = sorted(righe, key=lambda r: r["var1"])
    return ordinate[-1], ordinate[0]


def data_breve(d) -> str:
    return f"{GIORNI_BREVI[d.weekday()]} {d:%d/%m}" if d else ""


def whatsapp(m: dict) -> str:
    blocchi = []
    for i, g in enumerate(m["gruppi"]):
        data = f" _chiusura {data_breve(g['data'])}_" if g["data"] else ""
        righe = [f"*📈 Mercati*\n\n*{g['titolo']}*{data}" if i == 0 else f"*{g['titolo']}*{data}"]
        for r in g["righe"]:
            if r["var1"] is None:
                righe.append(f"▫️ {r['nome']}: n.d.")
                continue
            pallino = "🟢" if r["var1"] > 0.05 else "🔴" if r["var1"] < -0.05 else "⚪"
            riga = f"{pallino} {r['nome']}: {numero(r['prezzo'], r['decimali'])} ({perc(r['var1'])}"
            if r["var5"] is not None:
                riga += f" · 5g {perc(r['var5'])}"
            righe.append(riga + ")")
        blocchi.append("\n".join(righe))
    blocchi.append("_Dati informativi, non sono consigli d'investimento._")
    return "\n\n".join(blocchi)


def telegram(m: dict) -> str:
    blocchi = ["<b>📈 Mercati</b>"]
    migliore, peggiore = migliore_peggiore(m)
    if migliore and peggiore:
        blocchi[0] += (f"\n▲ {esc(migliore['nome'])} <b>{perc(migliore['var1'])}</b>"
                       f" · ▼ {esc(peggiore['nome'])} <b>{perc(peggiore['var1'])}</b>")
    for g in m["gruppi"]:
        data = f" <i>· chiusura {data_breve(g['data'])}</i>" if g["data"] else ""
        righe = [f"<b>{esc(g['titolo'])}</b>{data}"]
        for r in g["righe"]:
            if r["var1"] is None:
                righe.append(f"▫️ {esc(r['nome'])}: n.d.")
                continue
            pallino = "🟢" if r["var1"] > 0.05 else "🔴" if r["var1"] < -0.05 else "⚪"
            riga = f"{pallino} {esc(r['nome'])} {numero(r['prezzo'], r['decimali'])} <b>{perc(r['var1'])}</b>"
            if r["var5"] is not None:
                riga += f" <i>· 5g {perc(r['var5'])}</i>"
            righe.append(riga)
        blocchi.append("\n".join(righe))
    blocchi.append("<i>Dati informativi, non sono consigli d'investimento.</i>")
    return "\n\n".join(blocchi)
