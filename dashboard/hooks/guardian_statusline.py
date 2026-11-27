#!/usr/bin/env python3
"""Barra di stato di Claude Code -> utilizzo REALE per Guardian.

Claude Code passa a questo comando (stdin) il JSON della statusLine. Qui si leggono
rate_limits.five_hour / seven_day (used_percentage, resets_at; possono mancare) e si scrive in modo
atomico ~/.claude/guardian/usage.json. In uscita una riga breve: "5h 42% · 7g 18%" (o "-").
Non blocca mai Claude: ogni errore viene ignorato.
"""
import json
import os
import sys
import tempfile
import time


def _finestra(d):
    if not isinstance(d, dict):
        return None
    try:
        pct = float(d["used_percentage"])
    except (KeyError, TypeError, ValueError):
        return None
    ris = d.get("resets_at")
    return {"pct": max(0.0, min(100.0, pct)), "resets_at": ris if isinstance(ris, (int, float, str)) else None}


def elabora(dati, ora=None):
    """(usage | None, riga). usage = {"five_hour", "seven_day", "ts"}; None se non c'è nessun dato."""
    rl = dati.get("rate_limits") if isinstance(dati, dict) else None
    rl = rl if isinstance(rl, dict) else {}
    cinque, sette = _finestra(rl.get("five_hour")), _finestra(rl.get("seven_day"))
    parti = []
    if cinque:
        parti.append(f"5h {cinque['pct']:.0f}%")
    if sette:
        parti.append(f"7g {sette['pct']:.0f}%")
    if not parti:
        return None, "-"
    usage = {"five_hour": cinque, "seven_day": sette, "ts": time.time() if ora is None else ora}
    return usage, " · ".join(parti)


def scrivi_atomico(usage, percorso):
    cartella = os.path.dirname(percorso)
    os.makedirs(cartella, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=cartella, prefix=".usage-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(usage, f)
        os.replace(tmp, percorso)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def main():
    try:
        dati = json.load(sys.stdin)
    except Exception:
        dati = {}
    usage, riga = elabora(dati)
    if usage:
        try:
            scrivi_atomico(usage, os.path.expanduser(os.environ.get("GUARDIAN_USAGE_FILE", "~/.claude/guardian/usage.json")))
        except Exception:
            pass
    print(riga)


if __name__ == "__main__":
    main()
