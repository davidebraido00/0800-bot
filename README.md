# 0800 ☕

Ogni mattina alle 8 ti arriva su **Telegram** e via **email**:

- **🌤️ Meteo Conegliano**: min/max, mattina/pomeriggio/sera, pioggia, vento, UV, alba e tramonto
- **📅 Agenda**: i tuoi appuntamenti di oggi da Google Calendar
- **📈 Mercati**: Piazza Affari, USA, ETF/oro/petrolio/cambi, crypto; variazione del giorno e a 5 sedute, con grafico dell'ultimo mese nell'email
- **🌱 Crescita personale**: una frase di inglese, una pillola di cultura e i tuoi obiettivi settimanali
- **📰 Notizie**: economia, Italia, esteri, tech/AI, Conegliano e Treviso, con i link

Su Telegram arrivano 2 messaggi: il primo con meteo, agenda, mercati e crescita personale, il secondo con le notizie (titoli cliccabili, elenchi che si espandono con un tocco). Suona solo il primo. L'email invece è una pagina unica impaginata, con tabelle e grafici.

## 1. Telegram

1. Su Telegram apri [@BotFather](https://t.me/BotFather), scrivi `/newbot` e scegli un nome (es. `0800`) e uno username che finisca in `bot` (es. `davide_0800_bot`).
2. BotFather ti risponde con il **token** (tipo `123456789:AA...`): mettilo in `.env` come `TELEGRAM_BOT_TOKEN`.
3. Apri la chat con il tuo nuovo bot e premi **Avvia** (o scrivi `/start`): un bot non può scriverti finché non lo contatti tu.
4. Esegui `.venv/bin/python -m brief.telegram`: trova il tuo chat id e lo salva in `.env` come `TELEGRAM_CHAT_ID`.

> WhatsApp (CallMeBot) è ancora supportato: aggiungi `whatsapp` a `canali` in `config.yaml` e configura `WHATSAPP_TO` e `CALLMEBOT_APIKEY`. Il servizio gratuito però consegna subito solo fino a 16 messaggi ogni 4 ore, poi li mette in coda e li raggruppa.

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
| `TELEGRAM_BOT_TOKEN` | il token di @BotFather |
| `TELEGRAM_CHAT_ID` | il tuo chat id (da `python -m brief.telegram`) |
| `GOOGLE_CALENDAR_ICS` | i link iCal segreti, separati da virgola |
| `EMAIL_FROM` | l'indirizzo Gmail da cui inviare |
| `EMAIL_TO` | il destinatario (può essere lo stesso indirizzo) |
| `EMAIL_APP_PASSWORD` | la password per le app di Google |

Se un canale non è configurato viene saltato, gli altri partono comunque. Se un invio fallisce, GitHub ti manda un'email.

Puoi lanciarlo a mano da *Actions → 0800 → Run workflow*: invia subito.

## 6. Avvio puntuale alle 8 (cron-job.org)

Il cron integrato di GitHub su questo repository parte con ore di ritardo o non parte affatto, quindi l'avvio lo dà un servizio esterno e gratuito, [cron-job.org](https://cron-job.org), che alle 7:50 chiede a GitHub di lanciare il workflow (come il pulsante "Run workflow", che parte subito). Lo script attende le 8:00 e invia.

1. **Token GitHub**: *Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token*
   - Repository access: *Only select repositories* → `0800-bot`
   - Permissions → Repository permissions → **Actions: Read and write**
2. **cron-job.org** → *Create cronjob*:
   - URL: `https://api.github.com/repos/davidebraido00/0800-bot/actions/workflows/morning.yml/dispatches`
   - Orario: ogni giorno alle **07:50**, fuso **Europe/Rome**
   - *Advanced*: metodo **POST**, header `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, corpo `{"ref":"main","inputs":{"programmato":"true"}}`

GitHub risponde `204 No Content` quando accetta la richiesta. I cron di GitHub restano come riserva: un segno salvato nella cache evita di inviare due volte nello stesso giorno, e gli avvii arrivati dopo le 11 vengono saltati.

## Personalizza

Tutto si modifica in [config.yaml](config.yaml):

- **Canali e ordine**: le chiavi `canali` e `ordine`.
- **Titoli**: i gruppi di `mercati`. I simboli sono quelli di Yahoo Finance: `.MI` = Milano, `.DE` = Xetra, `-EUR` = crypto in euro.
- **Notizie**: numero per argomento, feed RSS, nuovi argomenti. Per un argomento locale puoi usare Google News: `https://news.google.com/rss/search?q=PAROLA+when:1d&hl=it&gl=IT&ceid=IT:it`
- **Obiettivi**: in `crescita.obiettivi` indica nome, parole da cercare nei titoli degli eventi del calendario e quante volte a settimana. Il conteggio va dal lunedì alla domenica, e il lunedì c'è anche il resoconto della settimana precedente.
- **Inglese e pillole**: aggiungi voci in [data/inglese.yaml](data/inglese.yaml) e [data/pillole.yaml](data/pillole.yaml). Ne esce una al giorno, a rotazione.

I dati di mercato sono informativi (ultima chiusura disponibile) e non sono consigli d'investimento.
