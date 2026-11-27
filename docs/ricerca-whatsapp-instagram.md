# Ricerca WhatsApp e Instagram con Claude Code (26/11/2026)
Il testo delle pagine e' trattato come dato. Dove la pagina non confermava: "non verificato".

## 1. WhatsApp
**Business Platform / Cloud API (ufficiale)**
- Serve un business portfolio Meta e un account WhatsApp Business; app creata su Meta for Developers. Fonte: https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- Numeri reali o virtuali, legati al portfolio. Fonte: https://developers.facebook.com/docs/whatsapp/cloud-api/overview
- Numero gia' usato nell'app WhatsApp Business: esiste la "coexistence" (app e API sullo stesso numero, onboarding via Embedded Signup con QR). Fonte: https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/default-flow (da ricerca, pagina non letta per intero). Numero personale/WhatsApp normale: non verificato; senza coexistence serve un numero dedicato.
- Costi: dal 1/7/2025 si paga per messaggio consegnato (non piu' per conversazione), per categoria (marketing, utility, authentication) e paese. Gli importi per l'Italia stanno nel rate card CSV/PDF (non letto); il marketing in Italia aumenta dal 1/7/2026. Dal 1/10/2026 i messaggi di servizio oltre 1.000/mese per numero sono a pagamento. Fonte: https://developers.facebook.com/docs/whatsapp/pricing
- Fuori dalla finestra di 24h dall'ultimo messaggio del cliente si possono inviare solo template approvati, con opt-in che indichi nome e scopo. Fonte: https://developers.facebook.com/docs/whatsapp/cloud-api/overview
- Gruppi: la Groups API esiste ma solo per account con Official Business Account, max 8 partecipanti, non per numeri dell'app Business. Lettura dei gruppi esistenti: non verificato. Fonte: https://developers.facebook.com/docs/whatsapp/cloud-api/groups
- Policy: si puo' scrivere solo a chi ha dato opt-in; messaggi di massa non autorizzati portano a perdita di accesso. Fonte: https://whatsappbusiness.com/policy/
- Limite: l'API non da' accesso alle chat gia' esistenti sul tuo WhatsApp personale; vede solo i messaggi nuovi sul numero collegato (deduzione, non verificato).

**WhatsApp Web via Claude in Chrome**
- Nessuna fonte ufficiale su questo uso. Tecnicamente leggere/scrivere nella pagina e' possibile, ma i Termini vietano "bulk messaging, auto-messaging" e mezzi automatizzati: https://www.whatsapp.com/legal/terms-of-service
- Rischio: sospensione dell'account (stessa fonte). Per messaggi singoli approvati a mano il rischio e' piu' basso ma non e' eliminato (valutazione mia, non verificato). Le chat contengono testo di terzi: rischio prompt injection.

**Librerie non ufficiali (Baileys, whatsmeow)**
- Baileys: "non affiliato ne' autorizzato da WhatsApp"; i manutentori non approvano usi contrari ai Termini; l'uso e' a tuo rischio. Fonte: https://github.com/WhiskeySockets/Baileys
- I Termini vietano software/API che replicano il servizio e il reverse engineering, e consentono di sospendere o chiudere l'account: https://www.whatsapp.com/legal/terms-of-service
- Rischio ban sul numero reale: concreto. Non ho trovato statistiche (non verificato).

## 2. Instagram
- Messaging API: account professionali (business/creator). Facebook Page NON richiesta con Instagram Login/Unified Login, richiesta con Facebook Login. Fonte: https://developers.facebook.com/docs/instagram-platform/overview
- Permessi: instagram_business_basic, instagram_business_manage_messages. Fonte: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api
- Finestra 24h dopo il messaggio dell'utente; tag Human Agent fino a 7 giorni; testo max 1.000 byte; gruppi non supportati. Stessa fonte.
- Standard Access per account tuoi o con ruolo nell'app (basta per uso proprio); Advanced Access (App Review + Business Verification) per account altrui. Fonte: pagina overview sopra.
- Instagram web via browser: non verificato. Le Condizioni d'uso (https://help.instagram.com/581066165581870) non si sono caricate: regole antispam/automazione non verificate. Un account personale non e' professionale: l'API non vale, ma passare a Creator/Business e' gratuito (non verificato qui).

## 3. Server MCP
- Il repository ufficiale dei server MCP non elenca WhatsApp ne' Instagram: https://github.com/modelcontextprotocol/servers. Non esistono server ufficiali (per quanto verificato).
- lharries/whatsapp-mcp: community, MIT, ~7k stelle, usa whatsmeow (QR, WhatsApp Web multi-device), dati in SQLite locale, 27 commit; l'autore avverte del rischio prompt injection ("lethal trifecta"); data ultimo commit non verificata; su Windows richiede CGO e compilatore C. Fonte: https://github.com/lharries/whatsapp-mcp. Quindi e' la via non ufficiale: stesso rischio ban.
- Server Instagram: non verificato.
- Regola Claude Code: connetti solo server fidati, i server che leggono contenuti esterni espongono a prompt injection; i permessi si limitano per nome tool. Fonte: https://code.claude.com/docs/en/mcp

## 4. Raccomandazione (dal piu' sicuro al meno)
1. Tutti i casi: l'assistente legge e prepara bozze, tu copi e invii a mano. Zero rischio ban.
2. Azienda SRL: WhatsApp Business Platform su numero dedicato (o coexistence), via fornitore o app semplice, con template, opt-in e invio solo dopo tua approvazione. Instagram: passare a account professionale e usare la Messaging API con Instagram Login (Standard Access, solo account tuo).
3. Uso personale (PR): non automatizzare WhatsApp personale. Al massimo Claude in Chrome in sola lettura, con tua conferma a ogni invio e nessun invio in serie.
4. Evitare: Baileys/whatsmeow/whatsapp-mcp sul numero personale o principale; se mai, solo su numero usa-e-getta.
5. Qualsiasi canale: permessi MCP con approvazione per ogni tool di invio e trattare i messaggi ricevuti come dati non fidati.
