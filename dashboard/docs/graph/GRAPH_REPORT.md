# Graph Report - gg2  (2026-11-26)

## Corpus Check
- 22 files · ~11,711 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 267 nodes · 445 edges · 21 communities (9 shown, 12 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- skill.py
- app.py
- theme.py
- fonte.py
- clienti.py
- FonteRemota
- Fonte
- Indice
- Risposta
- cacciatore-clienti.md
- scopritore-problemi.md
- analista-presenza-online.md
- analista-risultati.md
- architetto-squadra.md
- collaudatore-agenti.md
- curatore-skill.md
- forgiatore-agenti.md
- ottimizzatore-prompt.md
- redattore-outreach.md
- azienda.template.md
- compilatore-schede-visita.md

## God Nodes (most connected - your core abstractions)
1. `FonteRemota` - 28 edges
2. `Fonte` - 26 edges
3. `FonteLocale` - 25 edges
4. `esc()` - 11 edges
5. `Indice` - 9 edges
6. `_Stato` - 8 edges
7. `installa_catalogo_locale()` - 8 edges
8. `vista_statistiche()` - 7 edges
9. `esegui_locale()` - 7 edges
10. `imposta_visita()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `vista_statistiche()` --calls--> `riepilogo_token()`  [EXTRACTED]
  app.py → monitor.py
- `get_fonte()` --calls--> `crea_fonte()`  [EXTRACTED]
  app.py → fonte.py
- `esegui_e_mostra()` --references--> `Risposta`  [EXTRACTED]
  app.py → chat.py
- `vista_statistiche()` --calls--> `grafico_cpu()`  [EXTRACTED]
  app.py → theme.py
- `vista_statistiche()` --calls--> `legenda_cpu()`  [EXTRACTED]
  app.py → theme.py

## Import Cycles
- None detected.

## Communities (21 total, 12 thin omitted)

### Community 0 - "skill.py"
Cohesion: 0.09
Nodes (14): FonteLocale, catalogo_locale(), elenca_skill(), _git(), installa_catalogo_locale(), installa_graphify_locale(), installa_locale(), installa_squadra_locale() (+6 more)

### Community 1 - "app.py"
Cohesion: 0.09
Nodes (7): fa(), Campionatore, e_processo_claude(), _file_ricavi(), leggi_ricavi(), riepilogo_token(), scrivi_ricavo()

### Community 2 - "theme.py"
Cohesion: 0.13
Nodes (16): vista_agenti(), vista_costi(), vista_statistiche(), barre_orizzontali(), card_skill(), card_store(), esc(), grafico_costi() (+8 more)

### Community 3 - "fonte.py"
Cohesion: 0.11
Nodes (4): costo(), prezzo_modello(), costruisci_comando(), esegui_locale()

### Community 4 - "clienti.py"
Cohesion: 0.14
Nodes (12): clienti(), _file_stati(), foto(), imposta_visita(), leggi_leads(), leggi_stati(), _righe_csv(), salva_foto() (+4 more)

### Community 6 - "Fonte"
Cohesion: 0.08
Nodes (3): get_fonte(), crea_fonte(), Fonte

### Community 7 - "Indice"
Cohesion: 0.15
Nodes (4): Indice, parse_ts(), _Stato, _testo()

### Community 9 - "cacciatore-clienti.md"
Cohesion: 0.50
Nodes (3): Come lavori, Consegna, Prima di iniziare

### Community 10 - "scopritore-problemi.md"
Cohesion: 0.50
Nodes (3): Consegna, Cosa cerchi, Regole

## Knowledge Gaps
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FonteRemota` connect `FonteRemota` to `fonte.py`, `Fonte`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Should `skill.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09146341463414634 - nodes in this community are weakly interconnected._
- **Why does `Fonte` connect `Fonte` to `skill.py`, `fonte.py`, `FonteRemota`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Should `app.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08602150537634409 - nodes in this community are weakly interconnected._
- **Why does `FonteLocale` connect `skill.py` to `app.py`, `fonte.py`, `clienti.py`, `Fonte`?**
  _High betweenness centrality (0.121) - this node is a cross-community bridge._
- **Should `theme.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1330049261083744 - nodes in this community are weakly interconnected._
- **Should `fonte.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11384615384615385 - nodes in this community are weakly interconnected._