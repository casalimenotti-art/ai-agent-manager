#!/usr/bin/env python3
"""Aggiunge UNA riga al registro condiviso: registro/<chi>.jsonl.

Uso (da qualsiasi cartella del repo, solo libreria standard):
    python registro/scrivi.py --chi amico1 --agente codex "Preparate 5 bozze di contatto" --file leads/x.csv --esito fatto

Ognuno scrive SOLO nel proprio file: niente conflitti git tra le persone.
Non scrivere mai password, chiavi, token o dati personali dei clienti nel registro.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CARTELLA = Path(__file__).resolve().parent
ESITI = ("fatto", "in corso", "bloccato", "fallito")
_SEGRETO = re.compile(r"(sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[bp]-[A-Za-z0-9-]{10,}"
                      r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*\S+)",
                      re.IGNORECASE)


def persone() -> list[str]:
    try:
        return [p["id"] for p in json.loads((CARTELLA / "persone.json").read_text(encoding="utf-8"))]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def branch_attuale() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=CARTELLA, capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def crea_voce(chi: str, agente: str, azione: str, file=(), esito: str = "fatto", branch: str = "", ora: datetime | None = None) -> dict:
    azione = " ".join((azione or "").split())
    if not azione:
        raise ValueError("Scrivi cosa è stato fatto.")
    if len(azione) > 300:
        azione = azione[:297] + "..."
    testo = azione + " " + " ".join(file)
    if _SEGRETO.search(testo):
        raise ValueError("Sembra esserci una password o una chiave nel testo: non va nel registro.")
    if esito not in ESITI:
        raise ValueError(f"Esito non valido: usa uno tra {', '.join(ESITI)}.")
    ora = ora or datetime.now(timezone.utc)
    return {"ts": ora.astimezone(timezone.utc).isoformat(timespec="seconds"), "chi": chi, "agente": agente,
            "azione": azione, "file": [str(f) for f in file][:20], "esito": esito, "branch": branch}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Scrive una riga nel registro condiviso.")
    p.add_argument("azione", help="Cosa è stato fatto, in una frase")
    p.add_argument("--chi", required=True, help="Il tuo id in registro/persone.json (es. menotti, amico1, amico2)")
    p.add_argument("--agente", default="", help="claude-code, codex, oppure 'a mano'")
    p.add_argument("--file", action="append", default=[], help="File toccato (ripetibile)")
    p.add_argument("--esito", default="fatto", choices=ESITI)
    a = p.parse_args(argv)
    ids = persone()
    if ids and a.chi not in ids:
        print(f"'{a.chi}' non è in registro/persone.json ({', '.join(ids)}).", file=sys.stderr)
        return 2
    try:
        voce = crea_voce(a.chi, a.agente, a.azione, a.file, a.esito, branch_attuale())
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    with open(CARTELLA / f"{a.chi}.jsonl", "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(voce, ensure_ascii=False) + "\n")
    print(f"Registrato in registro/{a.chi}.jsonl. Ricorda: commit e push sul tuo branch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
