#!/usr/bin/env python3
"""Hook Claude Code -> eventi JSONL per Guardian.

Registrato su UserPromptSubmit, PreToolUse, PostToolUse, Stop. Legge il JSON dallo stdin,
accoda UNA riga a GUARDIAN_EVENTS_FILE (default ~/.claude/guardian/events.jsonl) ed esce con 0.
Non registra mai il contenuto dei tool (solo il nome) e tronca il prompt a 200 caratteri.
Non stampa nulla e non blocca mai Claude: ogni errore viene ignorato.
"""
import json
import os
import sys
import time

try:
    d = json.load(sys.stdin)
    path = os.path.expanduser(os.environ.get("GUARDIAN_EVENTS_FILE", "~/.claude/guardian/events.jsonl"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ev = {
        "ts": time.time(),
        "event": d.get("hook_event_name", ""),
        "session_id": d.get("session_id", ""),
        "cwd": d.get("cwd", ""),
        "tool": d.get("tool_name", ""),
    }
    if ev["event"] == "UserPromptSubmit":
        ev["prompt"] = str(d.get("prompt", ""))[:200]
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
except Exception:
    pass
sys.exit(0)
