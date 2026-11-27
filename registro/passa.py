#!/usr/bin/env python3
"""Passaggio di lavoro tra agenti (Claude Code <-> Codex), tramite file nel repo.

  python registro/passa.py apri --da menotti --per chiunque --compito "..." --fatto "..." --prossimi "..." --file x
  python registro/passa.py prendi passaggi/<file>.md --chi amico1
  python registro/passa.py chiudi passaggi/<file>.md --chi amico1
  python registro/passa.py aperti

Ogni comando scrive anche una riga nel registro. Dopo: commit e push sul proprio branch.
"""
import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scrivi  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CARTELLA = REPO / "passaggi"
STATI = ("aperto", "preso", "chiuso")
_STATO = re.compile(r"^- stato: *(\w+)", re.MULTILINE)


def testo_passaggio(da, agente, per, compito, fatto, prossimi, file, branch, ora) -> str:
    righe_file = "\n".join(f"- {f}" for f in file) or "- (nessuno indicato)"
    return (f"# Passaggio di lavoro: {compito}\n\n- stato: aperto\n- da: {da} ({agente})\n- per: {per}\n"
            f"- branch: {branch or '?'}\n- creato: {ora}\n\n## Cosa stavo facendo\n{compito}\n\n"
            f"## Fatto finora\n{fatto or '(niente di indicato)'}\n\n## Prossimi passi\n{prossimi or '(da decidere)'}\n\n"
            f"## File toccati\n{righe_file}\n\n## Note di chi lo prende\n")


def stato(testo: str) -> str:
    m = _STATO.search(testo or "")
    return m.group(1) if m else "?"


def cambia_stato(testo: str, nuovo: str, chi: str, ora: str) -> str:
    if nuovo not in STATI:
        raise ValueError(nuovo)
    return _STATO.sub(f"- stato: {nuovo}", testo, count=1) + f"- {ora}: {nuovo} da {chi}\n"


def aperti(cartella: Path = CARTELLA) -> list[Path]:
    return [p for p in sorted(cartella.glob("*.md")) if stato(p.read_text(encoding="utf-8")) in ("aperto", "preso")]


def _ora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _registra(chi, agente, azione, file, esito):
    voce = scrivi.crea_voce(chi, agente, azione, file, esito, scrivi.branch_attuale())
    with open(scrivi.CARTELLA / f"{chi}.jsonl", "a", encoding="utf-8", newline="\n") as f:
        import json
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Passaggi di lavoro tra agenti")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apri")
    a.add_argument("--da", required=True)
    a.add_argument("--agente", default="claude-code")
    a.add_argument("--per", default="chiunque")
    a.add_argument("--compito", required=True)
    a.add_argument("--fatto", default="")
    a.add_argument("--prossimi", default="")
    a.add_argument("--file", action="append", default=[])
    for nome in ("prendi", "chiudi"):
        s = sub.add_parser(nome)
        s.add_argument("percorso")
        s.add_argument("--chi", required=True)
        s.add_argument("--agente", default="codex")
    sub.add_parser("aperti")
    x = p.parse_args(argv)
    try:
        if x.cmd == "aperti":
            for f in aperti():
                print(f"{f.relative_to(REPO)}  [{stato(f.read_text(encoding='utf-8'))}]")
            return 0
        if x.cmd == "apri":
            ora = _ora()
            testo = testo_passaggio(x.da, x.agente, x.per, x.compito, x.fatto, x.prossimi, x.file, scrivi.branch_attuale(), ora)
            if scrivi._SEGRETO.search(testo):
                raise ValueError("Sembra esserci una password o una chiave: non va nel passaggio.")
            CARTELLA.mkdir(exist_ok=True)
            f = CARTELLA / f"{ora[:16].replace(':', '').replace('-', '')}-{x.da}.md"
            f.write_text(testo, encoding="utf-8", newline="\n")
            _registra(x.da, x.agente, f"Passaggio aperto per {x.per}: {x.compito}", [str(f.relative_to(REPO))], "in corso")
            print(f"Creato {f.relative_to(REPO)}. Ora: commit e push.")
            return 0
        f = (REPO / x.percorso) if not Path(x.percorso).is_absolute() else Path(x.percorso)
        nuovo = "preso" if x.cmd == "prendi" else "chiuso"
        f.write_text(cambia_stato(f.read_text(encoding="utf-8"), nuovo, x.chi, _ora()), encoding="utf-8", newline="\n")
        _registra(x.chi, x.agente, f"Passaggio {nuovo}: {f.name}", [str(f.relative_to(REPO))], "in corso" if nuovo == "preso" else "fatto")
        print(f"{f.name}: {nuovo}. Ora: commit e push.")
        return 0
    except (ValueError, OSError) as e:
        print(e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
