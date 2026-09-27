# 0800 ☕

Ogni mattina alle 8 ti arriva su **WhatsApp** e via **email**:

- **🌤️ Meteo Conegliano**: min/max, mattina/pomeriggio/sera, pioggia, vento, UV, alba e tramonto
- **📅 Agenda**: i tuoi appuntamenti di oggi da Google Calendar
- **📈 Mercati**: Piazza Affari, USA, ETF/oro/petrolio/cambi, crypto; variazione del giorno e a 5 sedute, con grafico dell'ultimo mese nell'email
- **🌱 Crescita personale**: una frase di inglese, una pillola di cultura e i tuoi obiettivi settimanali
- **📰 Notizie**: economia, Italia, esteri, tech/AI, Conegliano e Treviso, con i link

Il messaggio WhatsApp arriva in circa 7 parti, una per area, distanziate di 10 secondi. L'email invece è una pagina unica impaginata, con tabelle e grafici.

## 1. WhatsApp (CallMeBot, gratis)

1. Segui https://www.callmebot.com/blog/free-api-whatsapp-messages/: aggiungi il numero del bot ai contatti e mandagli `I allow callmebot to send me messages`.
2. Ti risponde con la tua **apikey**.

> ⚠️ Il servizio gratuito consegna subito fino a **16 messaggi ogni 4 ore**. Oltre quella soglia li mette in coda, li raggruppa e li consegna in ritardo. Per l'uso quotidiano va bene, ma evita di fare troppi test di fila.

## 2. Email (Gmail)

Serve una **password per le app** di Google, cioè una password di 16 lettere valida solo per 0800 (non è la password del tuo account):

1. Attiva la verifica in due passaggi se non l'hai già: https://myaccount.google.com/signinoptions/two-step-verification
2. Apri https://myaccount.google.com/apppasswords, scrivi come nome `0800` e premi **Crea**.
3. Copia la password che compare e mettila in `EMAIL_APP_PASSWORD`.

Puoi revocarla in qualsiasi momento dalla stessa pagina, senza toccare la password dell'account.

## 3. Google Calendar

1. Apri https://calendar.google.com → ⚙️ **Impostazioni** → clicca il tuo calendario nella colonna di sinistra.
2. **Integra calendario** → copia **Indirizzo segreto in formato iCal**.
3. Per più calendari, separa i link con una virgola.

⚠️ Chiunque abbia quel link può leggere il calendario: mettilo solo in `.env` e nei secret di GitHub.

## 4. Prova in locale

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                       # compila i valori
.venv/bin/python main.py --dry-run         # anteprima: WhatsApp a schermo + anteprima.html
.venv/bin/python main.py --canali email    # invia solo l'email
.venv/bin/python main.py                   # invia su tutti i canali
```

## 5. Automatizza con GitHub Actions

In *Settings → Secrets and variables → Actions* aggiungi questi secret:

| Secret | Valore |
|---|---|
| `WHATSAPP_TO` | il tuo numero, es. `+393331234567` |
| `CALLMEBOT_APIKEY` | l'apikey di CallMeBot |
| `GOOGLE_CALENDAR_ICS` | i link iCal segreti, separati da virgola |
| `EMAIL_FROM` | l'indirizzo Gmail da cui inviare |
| `EMAIL_TO` | il destinatario (può essere lo stesso indirizzo) |
| `EMAIL_APP_PASSWORD` | la password per le app di Google |

Se un canale non è configurato viene saltato, gli altri partono comunque. Se un invio fallisce, GitHub ti manda un'email.

Il workflow parte alle 06:00 e alle 07:00 UTC e invia solo quando in Italia sono le 8, così copre sia l'ora legale che quella solare. Puoi lanciarlo a mano da *Actions → 0800 → Run workflow*.

## Personalizza

Tutto si modifica in [config.yaml](config.yaml):

- **Canali e ordine**: le chiavi `canali` e `ordine`.
- **Titoli**: i gruppi di `mercati`. I simboli sono quelli di Yahoo Finance: `.MI` = Milano, `.DE` = Xetra, `-EUR` = crypto in euro.
- **Notizie**: numero per argomento, feed RSS, nuovi argomenti. Per un argomento locale puoi usare Google News: `https://news.google.com/rss/search?q=PAROLA+when:1d&hl=it&gl=IT&ceid=IT:it`
- **Obiettivi**: in `crescita.obiettivi` indica nome, parole da cercare nei titoli degli eventi del calendario e quante volte a settimana. Il conteggio va dal lunedì alla domenica, e il lunedì c'è anche il resoconto della settimana precedente.
- **Inglese e pillole**: aggiungi voci in [data/inglese.yaml](data/inglese.yaml) e [data/pillole.yaml](data/pillole.yaml). Ne esce una al giorno, a rotazione.

I dati di mercato sono informativi (ultima chiusura disponibile) e non sono consigli d'investimento.
