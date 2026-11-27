# 06 — Criteri di accettazione, test, consegna e avvio di Streamlit

## Criteri di accettazione (misurabili)
Ogni riga si verifica con una misura o un test e si registra nel report. Senza il numero, non è "fatto".

**Dati e tempo reale**
- AC-1 Il campionatore aggiorna i contatori ogni 1 s; la UI mostra il nuovo valore con latenza p95 ≤ 1,5 s (misurata con timestamp iniettato).
- AC-2 Sommando le UC dei punti a 1 s si ottiene lo stesso valore del ricalcolo da zero (differenza < 0,001).
- AC-3 Il blocco di 5 ore inizia/termina come in `02 §3` su 10 scenari sintetici (inclusi pausa ≥ 5 h, due blocchi nel giorno, cambio ora legale).
- AC-4 La settimana (mobile o ancorata) è corretta a cavallo di mezzanotte e del cambio ora legale.
- AC-5 Con calibrazione (es. 37 % a un istante) la percentuale stimata in quell'istante è 37 % e le successive crescono in proporzione; senza calibrazione mostra solo UC e lo dice.
- AC-6 Nessun uso di endpoint non documentati né di token di accesso di Claude (ricerca nel codice: zero occorrenze).
- AC-7 Budget: campionatore + UI aperta < 3 % di un core con 20 sessioni recenti (misura su 5 minuti); memoria dei buffer < 50 MB.
- AC-8 Riavvio: le serie ricompaiono entro 5 s senza buchi.

**Interfaccia**
- AC-9 La linea settimanale è centrale, la linea 5 h è subito sotto, con asse tempo e crosshair sincronizzati.
- AC-10 Ogni valore mostra provenienza (`misurato/calibrato/stimato`) ed età; con campionatore fermo compare "dato vecchio" entro 5 s.
- AC-11 Nessun salto di layout durante l'aggiornamento (spostamento cumulativo ≈ 0 misurato in browser).
- AC-12 `prefers-reduced-motion` disattiva glitch e count-up; contrasto testo ≥ 4,5:1, grafici ≥ 3:1; palette dati validata con lo script.
- AC-13 Nessuna richiesta di rete a runtime (verifica con il registro rete di Playwright: solo `localhost`).
- AC-14 390 px senza scroll orizzontale; tabelle con scroll interno.

**Agenti e manager**
- AC-15 La macchina a stati produce `lavora/fermo/bloccato/aspetta approvazione/finito` corretti su 6 sequenze di eventi finti.
- AC-16 Ogni card mostra compito, strumento, durata, chi l'ha avviato, UC e file prodotti; il drawer mostra la cronologia.
- AC-17 Il manager Guardian risponde dalla tab, mostra gli agenti avviati e le approvazioni aperte; il costo della richiesta compare in Costi.
- AC-18 Nessuna azione verso l'esterno parte da Guardian; le approvazioni non si auto-approvano mai.
- AC-19 Il cancello (se implementato) nega davvero uno strumento in una sessione di prova e consente quando `control.json` manca o è rotto.

**Clienti e sicurezza**
- AC-20 La tab Clienti mostra imbuto, filtri e scheda; stato e note si salvano; foto rifiutate senza consenso.
- AC-21 Nessun testo di agente arriva in HTML senza escape; i link `javascript:`/`data:` sono neutralizzati (test esistenti verdi).
- AC-22 `pytest -q` verde (tutti i test esistenti + i nuovi); nessun segreto nel diff (scansione con grep sui pattern comuni).
- AC-23 `avvia.bat` e `avvia.sh` avviano Guardian da zero su una cartella pulita.

**Costi**
- AC-24 Report finale con il costo reale per milestone (da Guardian) e la lista di dove si è speso di più.

## Piano dei test
1. **Unitari** (veloci, `pytest -q -x`): parser JSONL, finestre, calibrazione, macchina a stati, coda approvazioni, clienti, sicurezza.
2. **Dati sintetici**: `tests/gen_jsonl.py` con orologio iniettabile; golden files per le serie.
3. **Carico**: 10.000 eventi/s su un tick < 50 ms; 20 sessioni × 2.000 righe.
4. **UI** con Playwright (screenshot 1×, 1400 e 390 px; misura latenza, layout shift, richieste di rete, CPU).
5. **Sicurezza**: input ostili (HTML, `javascript:`, path traversal, CSV con formule, righe enormi), prompt injection in file di agenti.
6. **Prova reale a mano** (solo ciò che i test non coprono): cancello in una sessione vera, avvio da zero, `/voice`.

## Esecuzione per milestone (ordine consigliato)
- **M0** Setup e lettura: grafico (`docs/graph/GRAPH_REPORT.md`), `STATO.md`, `docs/spec/01` e `02`. Nessun codice.
- **M1** Livello dati: campionatore, buffer, finestre, calibrazione, `Fonte.live/finestre`. Test AC-1…8.
- **M2** Pannello Consumi (linee settimanale + 5 h) e contatori live con lo **spike A/B** del `03 §6`. Decisione scritta. AC-9…14.
- **M3** Agenti: stato, corsie, card, albero, feed. AC-15, 16.
- **M4** Manager Guardian: agente, tab, approvazioni, (cancello). AC-17…19.
- **M5** Clienti: imbuto, filtri, schede, (SQLite se conviene). AC-20, 21.
- **M6** Rifinitura visiva, accessibilità, prestazioni, ricerca esempi online e adattamenti. AC-12…14.
- **M7** Chiusura: README, test completi, grafico aggiornato, report, **avvio di Streamlit** (sotto).
Ogni milestone: test, `graphify update .`, commit, `STATO.md`, `/compact`. Al massimo una notifica all'ora (solo fine milestone/blocchi/decisioni).

## Formato del report (max 8 righe)
`Fatto · Misure (AC verificati, con numeri) · Bloccato · Serve la tua approvazione · Prossimo · Costo della milestone`.

## Chiusura: aprire Streamlit e farla vedere al titolare
Alla fine di **M7**, e solo dopo che i test sono verdi:
1. Aggiorna il progetto e verifica lo stato: `git status` pulito, commit fatto, push sul branch `claude/quirky-ritchie-u85igr`.
2. **Non lanciare `avvia.bat` da PowerShell con redirect** (`cmd /c "…< NUL > log"`): le virgolette annidate lo rompono. Avvia Guardian in uno di questi modi, in ordine:
   a. Se `dashboard\.venv\Scripts\streamlit.exe` esiste, da PowerShell:
      `Start-Process -FilePath "$PWD\.venv\Scripts\streamlit.exe" -ArgumentList "run","app.py","--server.address","localhost","--server.port","8501","--server.headless","true" -WorkingDirectory "$PWD" -WindowStyle Minimized`
      (eseguendo dalla cartella `dashboard`).
   b. Altrimenti dì al titolare di fare **doppio clic su `dashboard\avvia.bat`** (prepara l'ambiente al primo avvio, 1–2 minuti).
3. Verifica che risponda: `Invoke-WebRequest -UseBasicParsing http://localhost:8501/_stcore/health` deve dare `ok` (attendi fino a 60 s, riprova ogni 5).
4. Apri il browser: `Start-Process "http://localhost:8501"`.
5. Scrivi nel report l'indirizzo, l'ora di avvio e come fermarlo (chiudere la finestra o `Stop-Process -Name streamlit`). Se dopo 90 s non risponde, **non rilanciare in loop**: leggi il log, correggi una volta, e dimmelo.
6. Controlla che l'avviso `"app.theme" is not a valid config option` (se compare) abbia una causa verificata: chiedi `streamlit --version`, controlla `C:\Users\<utente>\.streamlit\config.toml` e `streamlit config show`; correggi solo dopo.

## Ripristino se qualcosa va storto
Ogni milestone è un commit: `git revert` del commit della milestone. Non usare `git reset --hard` né force-push. Se un test rosso non si risolve in 3 tentativi, ferma la milestone, annota in `STATO.md` e passa alla successiva.
