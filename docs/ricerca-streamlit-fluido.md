# Streamlit 1.67: app fluida e reattiva - 12 tecniche

Fonti lette (docs 1.67): F=https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment
FC=https://docs.streamlit.io/develop/concepts/architecture/fragments
C=https://docs.streamlit.io/develop/concepts/architecture/caching
SS=https://docs.streamlit.io/develop/concepts/architecture/session-state
H=https://docs.streamlit.io/develop/api-reference/text/st.html
CH=https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v1.html
V2=https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component
N=https://docs.streamlit.io/develop/concepts/multipage-apps/page-and-navigation
Non letti: forum e GitHub (non verificato). Nessuna pagina doc fornisce benchmark <100 ms.

## 1. Fragment per aggiornare solo una parte (F, FC)
Un widget dentro un fragment rilancia solo quel fragment (da 1.37).
```python
@st.fragment
def pannello():
    if st.button("+1"): st.session_state.n += 1
```
## 2. Live update con run_every (F, FC)
Accetta secondi, stringa "10s" o timedelta; gira anche senza input.
```python
@st.fragment(run_every="2s")
def live(): st.line_chart(get_data())
```
## 3. st.rerun(scope="fragment") invece di st.rerun() (F)
st.rerun() senza scope dentro un fragment fa rerun COMPLETO.
```python
if cambiato: st.rerun(scope="fragment")
```
## 4. Fragment con key + st.rerun("key") da callback (F, FC)
Da un widget esterno aggiorna solo il fragment mirato; non chiamabile dal corpo.
```python
@st.fragment(key="charts")
def charts(): ...
st.selectbox("Filtro", L, on_change=lambda: st.rerun("charts"))
```
## 5. parallel=True per fragment lenti e indipendenti (F, FC)
Thread pool nei rerun completi. Non possono scrivere in contenitori esterni; servono key distinte o lock.
```python
@st.fragment(parallel=True, run_every="10s")
def meteo(): ...
```
## 6. st.cache_data per dati (C)
Copia per chiamata; usare ttl e max_entries.
```python
@st.cache_data(ttl=30, max_entries=100, show_spinner=False)
def get_prices(sym): return fetch(sym)
```
## 7. st.cache_resource per oggetti condivisi (C)
Connessioni/modelli: una sola istanza, deve essere thread-safe. Param con "_" esclusi dall'hash.
```python
@st.cache_resource
def db(): return connect()
```
Attenzione: la doc sconsiglia di usare cache e fragment sulla stessa funzione (FC). Metti la cache sulle funzioni dati chiamate dal fragment, non sul fragment.

## 8. Callback on_click/on_change + session_state (SS)
Inizializza una volta, modifica lo stato nel callback e leggilo poi nel corpo. Il momento esatto di esecuzione rispetto al rerun non e' spiegato nelle pagine lette: non verificato.
```python
if "n" not in st.session_state: st.session_state.n = 0
def inc(): st.session_state.n += 1
st.button("Add", on_click=inc)
```
## 9. Stato condiviso tra fragment via session_state (FC)
I valori di ritorno sono ignorati nei rerun di fragment: passa i dati tramite session_state; i fragment non rilevano cambi di input.

## 10. Navigazione tra "spazi": st.navigation + st.Page (N)
Una sola chiamata nell'entrypoint; solo la pagina scelta gira con .run(). Elementi nell'entrypoint sono la cornice comune. Resta un rerun dello script, non una SPA: tieni leggero l'entrypoint e la cache/stato fuori dalle pagine. Alternativa: "spazi" come st.tabs/contenitori dentro fragment (non verificato per costo di rerun).
```python
pg = st.navigation([st.Page("home.py"), st.Page("spazio2.py")])
pg.run()
```
## 11. Sfondi animati e HTML: st.html, non components.v1.html (H, CH)
- components.v1.html e' DEPRECATO dalla 1.56.0 (iframe con JS e same-origin); successore st.iframe (CH).
- st.html: sanitizzato con DOMPurify, senza iframe; JS ignorato salvo unsafe_allow_javascript=True; se contiene solo <style> non occupa layout (H).
- Sfondo CSS animato (solo transform/opacity, pointer-events:none) e' leggero; canvas/JS richiede unsafe_allow_javascript o componente v2. Prestazioni del canvas: non verificato nelle doc.
```python
st.html("<style>.bg{position:fixed;inset:0;z-index:-1;animation:m 20s linear infinite}</style><div class='bg'></div>")
```
## 12. Interattivita' bidirezionale solo con componenti v2 (V2)
st.components.v2.component(name, html, css, js): senza iframe, shadow root di default; JS invia eventi con setTriggerValue (evento) e setStateValue (stato); Python legge result.attr e puo' usare on_<nome>_change. Il click in JS e' locale (immediato); solo cio' che serve a Python fa rerun.
```python
btn = st.components.v2.component("b", js=JS)
r = btn(on_clicked_change=lambda: None)
if r.clicked: ...
```

## Sui tempi < 100 ms
Nessuna fonte letta garantisce <100 ms per i clic. Ogni widget fuori da fragment rilancia lo script intero via websocket: per restare reattivi usa fragment, cache, calcoli leggeri nel corpo e animazioni lato browser (CSS/JS). Misura nel tuo ambiente (non verificato).

## Sicurezza
HTML/JS di st.html(unsafe) e componenti non e' sandboxed: mai passare input non fidato (H, CH, V2).
