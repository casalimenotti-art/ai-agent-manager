#!/usr/bin/env python3
"""Hook PostToolUse: se l'utilizzo di Claude (5 ore o settimana) supera la soglia, ricorda a Claude
di scrivere il passaggio di lavoro per Codex (registro/passa.py) e fare push.

Legge ~/.claude/guardian/usage.json (scritto dalla barra di stato di Guardian). Avvisa una volta
per sessione e per soglia. Non blocca mai Claude: ogni errore viene ignorato.
Soglia: variabile GUARDIAN_SOGLIA_PASSAGGIO (default 60: il titolare tiene il 40% per le sue richieste).
"""
import json
import os
import sys
import time


def messaggio(usage: dict, soglia: float, ora: float) -> str | None:
    if not usage or ora - float(usage.get("ts", 0)) > 900:   # dati vecchi di oltre 15 minuti: non mi fido
        return None
    picchi = [(k, float((usage.get(k) or {}).get("pct", 0))) for k in ("five_hour", "seven_day")]
    k, pct = max(picchi, key=lambda x: x[1])
    if pct < soglia:
        return None
    nome = "5 ore" if k == "five_hour" else "settimana"
    return (f"ATTENZIONE: utilizzo Claude al {pct:.0f}% ({nome}). Prima che finisca, scrivi il passaggio per Codex: "
            "python registro/passa.py apri --da menotti --per chiunque --compito \"...\" --fatto \"...\" --prossimi \"...\" --file ... "
            "poi commit e push sul tuo branch, e avvisa il titolare. Il restante 40% e' riservato alle richieste dirette del titolare: non continuare il lavoro lungo.")


def main() -> int:
    try:
        d = json.load(sys.stdin)
        base = os.path.expanduser("~/.claude/guardian")
        with open(os.environ.get("GUARDIAN_USAGE_FILE") or os.path.join(base, "usage.json"), encoding="utf-8") as f:
            usage = json.load(f)
        soglia = float(os.environ.get("GUARDIAN_SOGLIA_PASSAGGIO") or 60)
        msg = messaggio(usage, soglia, time.time())
        if not msg:
            return 0
        segno = os.path.join(base, f"passaggio_avvisato_{d.get('session_id', 'x')}_{int(soglia)}")
        if os.path.exists(segno):
            return 0
        open(segno, "w").close()
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
