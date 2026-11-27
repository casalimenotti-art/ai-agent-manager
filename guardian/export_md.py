"""Esporta lo stato del database in GUARDIAN_TASKS.md, solo tra i marcatori, senza toccare il testo scritto a mano.

  python -m guardian.export_md                 # modalità locale (GUARDIAN_DB o ~/.guardian/hub.db)
  python -m guardian.export_md --db hub.db --file GUARDIAN_TASKS.md

Con Supabase si usa dall'Hub (stessa funzione `sezione_task`): qui niente credenziali.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from guardian.core.models import REPO, TASK_TERMINALI, adesso

INIZIO, FINE = "<!-- guardian:export -->", "<!-- /guardian:export -->"


def sezione_task(store) -> str:
    progetti = {p["id"]: p["nome"] for p in store.projects()}
    aperti = [t for t in store.tasks() if t["stato"] not in TASK_TERMINALI]
    righe = [f"## Task aperti nel database (esportati {adesso()})", "",
             "| # | Stato | Priorità | Titolo | Progetto | Responsabile / agente | Prossimo passo |", "|---|---|---|---|---|---|---|"]
    for t in aperti:
        cella = lambda v: str(v or "—").replace("|", "/").replace("\n", " ")[:120]  # noqa: E731
        righe.append(f"| {t['id']} | {t['stato']} | {t['priorita']} | {cella(t['titolo'])} | "
                     f"{cella(progetti.get(t.get('project_id')))} | "
                     f"{cella(t.get('assigned_agent_id') or t.get('responsabile'))} | {cella(t.get('next_step'))} |")
    if not aperti:
        righe.append("| — | — | — | nessun task aperto | — | — | — |")
    return "\n".join(righe)


def aggiorna_file(path: Path, contenuto: str) -> None:
    testo = path.read_text(encoding="utf-8") if path.exists() else ""
    blocco = f"{INIZIO}\n{contenuto}\n{FINE}"
    if INIZIO in testo and FINE in testo:
        prima, resto = testo.split(INIZIO, 1)
        testo = prima + blocco + resto.split(FINE, 1)[1]
    else:
        testo = testo.rstrip() + ("\n\n" if testo else "") + blocco + "\n"
    path.write_text(testo, encoding="utf-8")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Esporta i task aperti in GUARDIAN_TASKS.md")
    p.add_argument("--db", default=os.environ.get("GUARDIAN_DB") or str(Path.home() / ".guardian" / "hub.db"))
    p.add_argument("--file", default=str(REPO / "GUARDIAN_TASKS.md"))
    a = p.parse_args(argv)
    from guardian.core.store_sqlite import SqliteStore
    aggiorna_file(Path(a.file), sezione_task(SqliteStore(a.db)))
    print(f"Aggiornata la sezione esportata in {a.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
