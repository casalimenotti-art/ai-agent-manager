#!/usr/bin/env python3
"""Hook Claude Code -> ~/.claude/guardian/events.jsonl (letto dal Guardian Bridge).

Stesso formato di dashboard/hooks/guardian_hook.py (plancia locale), più l'evento Notification.
Registrare su: UserPromptSubmit, PreToolUse, PostToolUse, Notification, Stop, SubagentStop
(vedi `python bridge/install_hooks.py`). Non registra mai input/output dei tool, solo il nome;
il prompt è troncato a 200 caratteri. Non stampa nulla e non blocca mai Claude.
"""
import json
import os
import sys
import time

try:
    d = json.load(sys.stdin)
    path = os.path.expanduser(os.environ.get("GUARDIAN_EVENTS_FILE", "~/.claude/guardian/events.jsonl"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ev = {"ts": time.time(), "event": d.get("hook_event_name", ""), "session_id": d.get("session_id", ""),
          "cwd": d.get("cwd", ""), "tool": d.get("tool_name", "")}
    if ev["event"] == "UserPromptSubmit":
        ev["prompt"] = str(d.get("prompt", ""))[:200]
    if ev["event"] == "Notification":
        ev["message"] = str(d.get("message", ""))[:200]
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
except Exception:
    pass
sys.exit(0)
