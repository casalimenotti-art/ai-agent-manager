#!/usr/bin/env python3
"""Programma `notify` per Codex -> ~/.guardian/codex-events.jsonl (letto dal Guardian Bridge).

In ~/.codex/config.toml:   notify = ["python3", "/percorso/repo/bridge/hooks/codex_notify.py"]
Codex passa un JSON come ultimo argomento (es. {"type": "agent-turn-complete", "input-messages": [...], ...}).
Si salvano solo tipo, ora e la richiesta troncata a 200 caratteri; mai la risposta dell'agente.
"""
import json
import os
import sys
import time

try:
    d = json.loads(sys.argv[-1]) if len(sys.argv) > 1 else {}
    path = os.path.expanduser(os.environ.get("GUARDIAN_CODEX_EVENTS_FILE", "~/.guardian/codex-events.jsonl"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    msgs = d.get("input-messages") or d.get("input_messages") or []
    ev = {"ts": time.time(), "type": str(d.get("type", ""))[:60],
          "prompt": (" ".join(str(m) for m in msgs) if isinstance(msgs, list) else str(msgs))[:200]}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
except Exception:
    pass
sys.exit(0)
