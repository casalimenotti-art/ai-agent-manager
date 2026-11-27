# Miglioramenti suggeriti (self-improvement, 26/11/2026)

Analisi di questa sessione: loop notturno e pomeridiano sulla dashboard Guardian (circa 40 giri), più la scaletta per aprire l'azienda.
Da rivedere: **nulla è stato applicato** tranne dove scritto "già fatto".

## 1. Gli agenti dicono "fatto" senza averlo visto

**Problema:** in molti giri gli agenti hanno consegnato codice corretto per i test ma sbagliato a schermo. Esempi:
- CSS `.stButton > button`, che non colpisce i bottoni con `help`;
- schede con altezze diverse perché le griglie erano costruite per colonne;
- colonne `column-reverse` con `justify-content: start`, per cui la risposta di Guardian finiva fuori vista;
- glyph `\x15` dentro il CSS.

Lo si scopriva solo con uno screenshot o con `getComputedStyle` via JS.

**Proposta, per un nuovo `ai-agent-manager/CLAUDE.md`:**
```markdown
## Verifica a schermo (obbligatoria per la dashboard)
- Un giro è finito solo dopo: riavvio del server (theme.py NON si ricarica a caldo), screenshot in Chrome e controllo con JS (`getComputedStyle`, `offsetHeight`) della cosa cambiata.
- Vista telefono: iframe largo 390px dentro la pagina (resize_window non funziona a finestra massimizzata).
- Concorrenza: aprire 2-3 iframe della dashboard insieme e contare `[data-testid=stException]`.
- Prova d'uso reale: inviare una domanda vera a Guardian. Due bug gravi (claude.cmd non trovato, risposta invisibile) passavano tutti i test.
```

## 2. Lezioni Streamlit 1.67 da non riscoprire

**Proposta, in `dashboard/agenti-sviluppo/sviluppatore-dashboard.md`** (in parte già fatto il 26/11):
```markdown
- I bottoni con help= stanno dentro stTooltipHoverTarget: selettori discendenti, non ">". (già fatto)
- La classe st-key-<key> sta SUL blocco del contenitore, non su un figlio.
- Griglie: un nuovo st.columns(3) ogni 3 voci, mai uno solo per tutta la lista.
- st.cache_resource / oggetti di modulo sono condivisi tra le schede del browser: lock per ogni stato mutabile.
- Su Windows i comandi npm sono .cmd: usare shutil.which().
```

## 3. Report degli agenti e brief

**Cosa ha funzionato:** brief completi con file, difetto visto, regole ("solo Edit mirati"), verifiche con output reale e rapporto in N righe. Un agente alla volta, poi verifica mia. Da mantenere.

**Proposta, nella memoria `agenti-con-ruolo`:** aggiungere "nel brief, incolla il difetto come si vede a schermo (testo o misura), non solo come pensi sia nel codice".

## 4. Stato del progetto che invecchia

**Problema:** Guardian ha risposto con informazioni vecchie (voce bloccata, 7 test falliti) perché STATO.md non era aggiornato.

**Proposta, in CLAUDE.md:** "a fine sessione aggiornare STATO.md: è quello che legge Guardian".

## 5. Soglie di utilizzo

Il titolare cambia le soglie durante la sessione (5 ore 85% → 97%; settimana 40%).

**Proposta, nella memoria `risparmio-token-e-ripresa`:** "le soglie valide sono le ultime dette dal titolare: annotarle subito in CONTINUA.md". Il resto (stato su file, ripresa) c'è già.

---

## Già a posto

| Tema | Dove |
|---|---|
| Chiamarlo "fratello", italiano | memoria `chiamami-fratello` |
| Ripresa da CONTINUA.md/STATO.md | memoria `progetto-guardian` |
| Agenti con ruolo, mai general-purpose | memoria `agenti-con-ruolo` |
| Edit mirati, niente splice | CONTINUA.md (LEZIONE 2) + agente sviluppatore-dashboard |
| Report in graphify-out/GRAPH_REPORT.md | agente sviluppatore-dashboard (corretto il 26/11) |

## Skill possibili (da non installare senza ok)

| Skill | Scopo |
|---|---|
| `verifica-dashboard` (locale, da scrivere) | Una sola procedura: riavvio, screenshot, controlli JS, iframe telefono, 3 sessioni, una domanda a Guardian |

## Frasi del titolare (contesto)

- "Devi farlo tu la dashboard"
- "cerca di arrivare tipo al 97% dell'utilizzo giornaliero"
- "utilizza al massimo il 40% dell'utilizzo settimanale"
