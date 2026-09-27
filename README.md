# 0800 ☕

Ogni mattina alle 8 ti arrivano su WhatsApp:

- **🌤️ Meteo Conegliano**: min/max, mattina/pomeriggio/sera, pioggia, vento, UV, alba e tramonto
- **📅 Agenda**: i tuoi appuntamenti di oggi da Google Calendar
- **📈 Mercati**: Piazza Affari, USA, ETF/oro/petrolio/cambi, crypto, con variazione del giorno e a 5 sedute
- **📰 Notizie**: economia, Italia, esteri, tech/AI, Conegliano e Treviso, con i link

Il messaggio viene diviso in più parti (circa 6), perché WhatsApp tramite API ha dei limiti di lunghezza.

## 1. Attiva WhatsApp (CallMeBot, gratis)

1. Segui https://www.callmebot.com/blog/free-api-whatsapp-messages/: aggiungi il numero del bot ai contatti e mandagli `I allow callmebot to send me messages`.
2. Ti risponde con la tua **apikey**.

> In alternativa: Twilio (`WHATSAPP_PROVIDER=twilio`). È più robusto ma a pagamento, e fuori dalla finestra di 24h richiede template approvati.

## 2. Collega Google Calendar

1. Apri https://calendar.google.com → ⚙️ **Impostazioni** → nella colonna di sinistra clicca il tuo calendario.
2. Scorri fino a **Integra calendario** → copia **Indirizzo segreto in formato iCal**.
3. Per più calendari, separa i link con una virgola.

⚠️ Chiunque abbia quel link può leggere il calendario: mettilo solo in `.env` e nei secret di GitHub, mai nel codice.

## 3. Prova in locale

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                 # compila i valori
.venv/bin/python main.py --dry-run   # anteprima, non invia nulla
.venv/bin/python main.py             # invio reale
```

## 4. Automatizza con GitHub Actions

1. Crea un repository **privato** su GitHub e fai push di questa cartella (il file `.env` è escluso da `.gitignore`).
2. *Settings → Secrets and variables → Actions → New repository secret*. Aggiungi:
   - `WHATSAPP_TO`: il tuo numero, es. `+393331234567`
   - `CALLMEBOT_APIKEY`
   - `GOOGLE_CALENDAR_ICS`
3. *Actions → 0800 → Run workflow* per un test immediato.

Il workflow parte alle 06:00 e alle 07:00 UTC e invia solo quando in Italia sono le 8, così copre sia l'ora legale che quella solare. GitHub può ritardare l'avvio di qualche minuto. Se un invio fallisce, GitHub ti manda un'email.

## Personalizza

Tutto si modifica in [config.yaml](config.yaml):

- **Titoli**: aggiungi o togli righe nei gruppi di `mercati`. I simboli sono quelli di Yahoo Finance: `.MI` = Milano, `.DE` = Xetra, `-EUR` = crypto in euro.
- **Notizie**: numero per argomento, feed RSS, nuovi argomenti. Per un argomento locale puoi usare Google News: `https://news.google.com/rss/search?q=PAROLA+when:1d&hl=it&gl=IT&ceid=IT:it`
- **Ordine delle sezioni**: la chiave `ordine`.

I dati di mercato sono informativi (ultima chiusura disponibile) e non sono consigli d'investimento.
