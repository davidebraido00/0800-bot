"""Previsioni del giorno da Open-Meteo (gratuito, senza chiave)."""
from __future__ import annotations

from datetime import datetime

import requests

# Codici meteo WMO -> (emoji, descrizione)
WMO = {
    0: ("☀️", "sereno"), 1: ("🌤️", "poco nuvoloso"), 2: ("⛅", "parz. nuvoloso"),
    3: ("☁️", "coperto"), 45: ("🌫️", "nebbia"), 48: ("🌫️", "nebbia"),
    51: ("🌦️", "pioviggine"), 53: ("🌦️", "pioviggine"), 55: ("🌦️", "pioviggine"),
    56: ("🌧️", "pioggia gelata"), 57: ("🌧️", "pioggia gelata"),
    61: ("🌧️", "pioggia debole"), 63: ("🌧️", "pioggia"), 65: ("🌧️", "pioggia forte"),
    66: ("🌧️", "pioggia gelata"), 67: ("🌧️", "pioggia gelata"),
    71: ("🌨️", "neve debole"), 73: ("🌨️", "neve"), 75: ("❄️", "neve forte"), 77: ("🌨️", "nevischio"),
    80: ("🌦️", "rovesci"), 81: ("🌧️", "rovesci"), 82: ("⛈️", "rovesci forti"),
    85: ("🌨️", "rovesci di neve"), 86: ("🌨️", "rovesci di neve"),
    95: ("⛈️", "temporale"), 96: ("⛈️", "temporale con grandine"), 99: ("⛈️", "temporale con grandine"),
}
FASCE = [("Mattina", 9), ("Pomeriggio", 15), ("Sera", 20)]


def sezione(cfg: dict, tz: str, oggi: datetime) -> str:
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": cfg["lat"],
            "longitude": cfg["lon"],
            "timezone": tz,
            "forecast_days": 1,
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,"
                     "precipitation_probability_max,wind_speed_10m_max,sunrise,sunset,uv_index_max",
            "hourly": "temperature_2m,weathercode,precipitation_probability",
        },
        timeout=15,
    )
    r.raise_for_status()
    dati = r.json()
    d, h = dati["daily"], dati["hourly"]

    emoji, desc = WMO.get(d["weathercode"][0], ("🌡️", ""))
    righe = [
        f"*{emoji} Meteo {cfg['citta']}*",
        f"{desc.capitalize()} · min {d['temperature_2m_min'][0]:.0f}° / max {d['temperature_2m_max'][0]:.0f}°",
    ]
    for nome, ora in FASCE:
        e, _ = WMO.get(h["weathercode"][ora], ("", ""))
        righe.append(f"  {nome}: {e} {h['temperature_2m'][ora]:.0f}° · pioggia {h['precipitation_probability'][ora]}%")

    pioggia = d["precipitation_sum"][0]
    extra = f"💧 {d['precipitation_probability_max'][0]}%"
    if pioggia >= 0.5:
        extra += f" ({pioggia:.0f} mm)"
    extra += f" · 💨 {d['wind_speed_10m_max'][0]:.0f} km/h · UV {d['uv_index_max'][0]:.0f}"
    righe.append(extra)
    righe.append(f"🌅 {d['sunrise'][0][-5:]} · 🌇 {d['sunset'][0][-5:]}")
    if d["precipitation_probability_max"][0] >= 50:
        righe.append("☂️ _Porta l'ombrello!_")
    return "\n".join(righe)
