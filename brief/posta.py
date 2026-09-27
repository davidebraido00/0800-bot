"""Versione email: HTML impaginato con grafici, inviato via Gmail (SMTP + password per le app)."""
from __future__ import annotations

import base64
import io
import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, make_msgid
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # nessun display, solo PNG
import matplotlib.pyplot as plt  # noqa: E402
from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402

from .fmt import GIORNI, GIORNI_BREVI, MESI, fa_quanto, numero, perc  # noqa: E402
from .mercati import data_breve, migliore_peggiore  # noqa: E402

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
VERDE, ROSSO, GRIGIO = "#1a7f37", "#cf222e", "#6e7781"


def _sparkline(serie: list[float]) -> bytes:
    """Mini grafico dell'ultimo mese, 2x per schermi retina (mostrato a 104x28)."""
    colore = VERDE if serie[-1] >= serie[0] else ROSSO
    fig = plt.figure(figsize=(2.08, 0.56), dpi=100)
    ax = fig.add_axes([0.02, 0.08, 0.94, 0.84])
    x = range(len(serie))
    ax.plot(x, serie, color=colore, linewidth=1.8, solid_capstyle="round")
    ax.fill_between(x, serie, min(serie), color=colore, alpha=0.10, linewidth=0)
    ax.plot([len(serie) - 1], [serie[-1]], "o", color=colore, markersize=3.2)
    ax.set_xlim(-0.3, len(serie) - 0.7)
    ax.axis("off")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", transparent=True)
    plt.close(fig)
    return buf.getvalue()


def _colore(v) -> str:
    if v is None or abs(v) < 0.05:
        return GRIGIO
    return VERDE if v > 0 else ROSSO


def componi(dati: dict, errori: list[str], oggi, cfg: dict, inline: bool = False):
    """Restituisce (oggetto, html, immagini). inline=True incorpora le immagini (anteprima nel browser)."""
    immagini = []  # (cid, png)

    def grafico(serie):
        if len(serie) < 2:
            return None
        png = _sparkline(serie)
        if inline:
            return "data:image/png;base64," + base64.b64encode(png).decode()
        cid = make_msgid(domain="0800")[1:-1]
        immagini.append((cid, png))
        return f"cid:{cid}"

    m = dati.get("mercati")
    if m:
        for g in m["gruppi"]:
            for r in g["righe"]:
                r["grafico"] = grafico(r["serie"])
    migliore, peggiore = migliore_peggiore(m) if m else (None, None)

    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html"]))
    env.filters.update(numero=numero, perc=perc, colore=_colore, fa_quanto=fa_quanto, data_breve=data_breve)
    html = env.get_template("email.html").render(
        d=dati, errori=errori, cfg=cfg, migliore=migliore, peggiore=peggiore,
        data=f"{GIORNI[oggi.weekday()]} {oggi.day} {MESI[oggi.month - 1]}",
    )

    # Oggetto informativo: si capisce la giornata già dalla lista delle email
    parti = [f"☕ 0800 · {GIORNI_BREVI[oggi.weekday()]} {oggi.day} {MESI[oggi.month - 1][:3]}"]
    if dati.get("meteo"):
        parti.append(f"{dati['meteo']['emoji']} {dati['meteo']['tmax']}°")
    if m and m["gruppi"] and m["gruppi"][0]["righe"][0]["var1"] is not None:
        r = m["gruppi"][0]["righe"][0]
        parti.append(f"{r['nome']} {perc(r['var1'])}")
    return " · ".join(parti), html, immagini


def configurata() -> bool:
    return bool(os.environ.get("EMAIL_FROM") and os.environ.get("EMAIL_APP_PASSWORD"))


def invia(oggetto: str, html: str, testo: str, immagini: list) -> None:
    mittente = os.environ["EMAIL_FROM"]
    msg = EmailMessage()
    msg["Subject"] = oggetto
    msg["From"] = formataddr(("0800", mittente))
    msg["To"] = os.environ.get("EMAIL_TO") or mittente
    msg.set_content(testo)
    msg.add_alternative(html, subtype="html")
    parte_html = msg.get_payload()[1]
    for cid, png in immagini:
        parte_html.add_related(png, maintype="image", subtype="png", cid=f"<{cid}>")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as s:
        s.login(mittente, os.environ["EMAIL_APP_PASSWORD"].replace(" ", ""))
        s.send_message(msg)
