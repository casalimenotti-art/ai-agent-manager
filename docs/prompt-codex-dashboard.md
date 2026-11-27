# Prompt per Codex: Guardian più dinamica, visibile e con un "corpo"

Incolla tutto questo a Codex (branch di partenza: `claude/dashboard-pc`, o `main` dopo il merge).

```
Sei lo sviluppatore della dashboard Guardian (Streamlit) in dashboard/. Leggi prima AGENTS.md, dashboard/README.md,
dashboard/docs/spec/*.md e dashboard/docs/decisioni.md. Il tuo id nel registro te lo dico io (amico1/amico2).

OBIETTIVO
Il titolare trova il design statico e "freddo". Vuole: 1) una dashboard molto più dinamica e spettacolare;
2) vedere IN DIRETTA ogni cosa che fanno gli agenti; 3) un avatar animato di Guardian (un "corpo") che reagisce ai comandi.

PIANO (un passo alla volta: dopo ogni passo test verdi, commit, riga nel registro, push sul tuo branch codex/dashboard)
1. Analisi: elenca in 10 righe cosa rende il layout attuale statico (theme.py, plancia.py, app.py). Niente codice.
2. Diretta degli agenti: una "timeline live" in cima allo spazio Agenti, una riga per evento (strumento usato, file, ricerca web)
   con animazione di entrata, colore per tipo e contatore; dati da fonte.py / monitor.py (già esistenti), aggiornamento con st.fragment.
3. Avatar di Guardian: componente HTML/SVG+CSS (o canvas) in dashboard/componenti/avatar/ caricato con components.html.
   Stati: fermo (respira), ascolta (microfono attivo), pensa (agente al lavoro), parla (voce attiva), felice (compito finito), errore.
   Comandi testuali e vocali già passati dalla chat di Guardian: "guarda a destra/sinistra/su/giù", "saluta", "annuisci",
   "vieni al centro": l'avatar gira la testa/occhi, si sposta, anima. Mappa i comandi in una funzione pura testabile
   (es. avatar.comando_da_testo("guarda a destra") -> {"azione":"guarda","dir":"destra"}).
   Gli occhi seguono il mouse quando è fermo. Nessuna risorsa esterna da CDN: tutto locale.
4. Design più vivo: transizioni tra spazi, micro-animazioni su card e pulsanti, sfondo animato leggero, numeri che contano,
   rispetta prefers-reduced-motion. Mantieni il tema scuro ciano esistente; mobile ok (larghezza telefono).
5. Collegamenti: lo stato dell'avatar segue i dati reali (agente attivo -> pensa; voce -> parla; compito finito -> felice).

REGOLE
- Non rompere i test esistenti (cd dashboard && python -m pytest -q); aggiungi test per ogni funzione nuova.
- Non toccare accesso.py, PIN, .env, hooks di sicurezza. Gli ospiti restano in sola lettura (vedi accesso.e_ospite).
- Nessun invio esterno, nessuna nuova dipendenza senza chiederlo nella pull request.
- Se ti fermi a metà: python registro/passa.py apri ... (vedi AGENTS.md) e push.

CRITERI DI ACCETTAZIONE
- Avviando dashboard/avvia.bat si vede l'avatar animato; scrivendo "guarda a destra" nella chat si gira a destra entro 1 s.
- Lo spazio Agenti mostra la timeline live che si aggiorna da sola mentre un agente lavora.
- Tutti i test passano; pull request verso main con screenshot/GIF e cosa provare.
```
