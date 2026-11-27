# Risposte ai DM Instagram in modo ufficiale (guida 27/11/2026)

Scopo: il titolare approva ogni risposta dalla dashboard; l'app invia solo dopo il suo OK.
Fonti: solo documentazione Meta/Instagram, lette il 27/11/2026. Ciò che non ho letto è marcato "non verificato".
Le pagine sono state lette tramite un riassuntore automatico: i numeri critici vanno ricontrollati sull'URL prima di fidarsene.

## 1. Account Creator o Business
- L'API serve account professionali (Business o Creator). Un account personale non funziona. [F1]
- Passaggio in app: Impostazioni e attività > Tipo di account e strumenti > passa a professionale > Creator o Business.
  Se l'account è privato diventa pubblico. Si può tornare personale in ogni momento. [F2]
- Per un PR va bene Creator. Differenze di funzioni fra i due tipi per i DM: non verificato.

## 2. Pagina Facebook
- Con "Instagram API with Instagram Login" NON serve collegare una Pagina Facebook. [F1]
- Serve solo con la variante "Facebook Login" (webhook sulla Pagina collegata). [F4]
- Scelta consigliata: Instagram Login (host graph.instagram.com).

## 3. App Meta
- Tipo app: Business. Dashboard > Instagram > "API setup with Instagram business login". [F3]
- Ruoli/tester: i tester devono avere un ruolo nell'app e nell'account Instagram. [F5] Procedura passo passo non verificata.
- Non ho creato alcun account o app.

## 4. Permessi (scope)
- instagram_business_basic (obbligatorio) e instagram_business_manage_messages (invio/lettura DM). [F5]
- Gli scope vecchi (business_basic ecc.) sono deprecati dal 27/01/2025. [F1][F6]
- Chiedere solo questi due: niente content_publish né manage_comments.

## 5. Token e durata
- Dal pulsante "Generate token" in dashboard: token valido 60 giorni, per i propri account. [F3]
- Con login utente: authorization code e token short-lived valgono 1 ora; long-lived 60 giorni. [F7][F6]
- Scambio: GET graph.instagram.com/access_token?grant_type=ig_exchange_token (solo lato server, usa app secret). [F6]
- Rinnovo: GET graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token. Condizioni: token con almeno 24 h,
  non scaduto, permesso instagram_business_basic. Aggiunge altri 60 giorni. Non rinnovato entro 60 giorni = scade per sempre,
  serve nuova autorizzazione. [F6]
- La dashboard deve rinnovare ogni ~30 giorni e tenere il token fuori dal repository.

## 6. Webhook (messaggi in arrivo)
- Serve un endpoint HTTPS pubblico con certificato TLS valido; i self-signed non sono supportati. [F8]
- Verifica: GET con hub.mode=subscribe, hub.challenge, hub.verify_token; rispondere col valore di hub.challenge. [F8]
- Firma: header X-Hub-Signature-256 = sha256= HMAC del corpo con l'App Secret; validarla sempre. [F8]
- Rispondere 200 subito, deduplicare (Meta ritenta fino a 36 ore); nessuno storico delle notifiche: salvarle noi. [F8][F9]
- Sottoscrizione per account: POST graph.instagram.com/{IG_ID}/subscribed_apps?subscribed_fields=messages (token utente IG). [F8]
- Campi messaggistica: messages, messaging_optins, messaging_postbacks, messaging_reactions, messaging_referrals, messaging_seen. [F5]
- L'app deve essere Live per ricevere notifiche di utenti dell'app (dettaglio modalità Development non documentato). [F8]
- URL pubblico dal PC (queste due strade NON sono documentate da Meta, quindi non verificate qui):
  Tailscale Funnel o Cloudflare Tunnel verso la porta locale della dashboard. Controllare che il certificato sia pubblico valido
  (non self-signed) e che il PC sia acceso quando arrivano i messaggi.
- Polling: esiste GET /me/conversations?platform=instagram (Conversations API, 2 chiamate/s per account) [F10][F7].
  Meta la cita come alternativa ai webhook, ma NON ho letto la pagina: parametri e permessi non verificati.
  Meta raccomanda comunque i webhook per evitare i rate limit. [F7]

## 7. Finestra 24 ore e regole
- Risposta standard consentita entro 24 ore dall'ultima azione dell'utente. Fino a 7 giorni se parte da un annuncio Click-to-Direct. [F5][F11]
- Human agent tag: risposta di un operatore umano fino a 7 giorni; serve una inbox personalizzata con conferma di consegna.
  È il caso della dashboard con approvazione del titolare, ma l'idoneità all'uso del tag non è verificata. [F5]
- Esperienze automatizzate: dichiarare che si interagisce con un servizio automatico (obbligo di legge in alcuni mercati). [F5]
- Testo max 1000 byte; niente chat di gruppo; richieste inattive da 30 giorni non restituite dalle API. [F5]
- I tag e i messaggi di utility non vanno usati per contenuti promozionali (5.6.c). [F11]

## 8. App Review
- Standard Access (predefinito): basta se l'app serve solo account propri o gestiti, usata da persone con un ruolo nell'app. [F7]
- Advanced Access (App Review + Business Verification): serve solo per account altrui o utenti senza ruolo. [F7]
- Quindi per il solo titolare come admin/tester: App Review non necessaria (fonte F7, F5). Limite da verificare in pratica:
  l'app va in Live per i webhook; se Live richieda comunque review per i DM in Standard: non verificato.

## 9. Limiti di invio
- Send API: 100 chiamate/s per account professionale per testo/link/reazioni/sticker; 10/s per audio e video. [F7]
  Una ricerca web cita un changelog che porta il testo a 300/s dal 23/06/2024: due fonti discordanti, irrilevante per un uso manuale.
- Conversations API: 2/s. Private replies a commenti: 750/ora (post e reel), 100/s (Live). [F7]
- Limite generale: chiamate in 24 h = 4800 x impression dell'account. [F7]
- Allegati: immagini png/jpeg 8 MB (max 10), audio/video/pdf 25 MB. [F5]

## 10. Cosa è vietato (Developer Policies Meta)
- Contattare persone su Instagram senza valido consenso (5.2.a); fornire modi per disattivare i messaggi e rispettarli subito (5.2.b). [F11]
- Spam e bot a frequenze molto elevate, link ingannevoli (5.6.b, 1.4); troppi feedback negativi = limitazioni o sospensione (5.4). [F11]
- Contenuti promozionali via tag/utility (5.6.c). Messaggi precompilati solo se scritti dall'utente o dall'azienda che gestisce l'account (5.6.d). [F11]
- Dati: non usarli oltre il necessario (5.6.4), niente retargeting né profilazione (10.7). [F11]
- Conseguenza: niente invii di massa, niente primo contatto a freddo, niente risposta automatica senza OK. Il flusso con approvazione umana è in linea.

## Raccomandazione per la dashboard
Instagram Login, app Business in Standard Access, 2 scope, webhook con firma verificata, coda "da approvare", invio solo dopo OK
entro 24 h (o human agent tag se verificato), rinnovo token a ~30 giorni. ig-mcp (jlbadano) non serve: si può scrivere un client minimo;
vedi C:\Users\casal\patron-sito\ricerca\curatela-skill.md e skill-instagram.md (ig-mcp: Business + Pagina FB, DM richiedono App Review, voto 7/10).

## Fonti
- F1 https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login
- F2 https://help.instagram.com/502981923235522 (e https://help.instagram.com/138925576505882/), da ricerca, pagina non aperta direttamente
- F3 https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/get-started
- F4 https://developers.facebook.com/docs/instagram-platform/webhooks
- F5 https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api
- F6 https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/business-login
- F7 https://developers.facebook.com/docs/instagram-platform/overview
- F8 https://developers.facebook.com/documentation/instagram-platform/webhooks/setup
- F9 https://developers.facebook.com/documentation/instagram-platform/webhooks/getting-started
- F10 https://developers.facebook.com/documentation/business-messaging/instagram-messaging/features/conversations-api (solo titolo letto)
- F11 https://developers.facebook.com/devpolicy/
