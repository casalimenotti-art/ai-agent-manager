"""Collector Claude Code: legge gli eventi scritti dall'hook (bridge/hooks/claude_hook.py, stesso formato
di dashboard/hooks/guardian_hook.py) e l'utilizzo reale scritto dalla statusline (usage.json).

Stato derivato SOLO dagli eventi:
- UserPromptSubmit / PreToolUse / PostToolUse -> working
- Notification (Claude chiede un permesso o aspetta l'utente) -> needs_approval / waiting
- Stop / SubagentStop -> idle
- nessun evento da più di INATTIVO_MIN minuti -> unknown (Claude potrebbe essere chiuso: non si sa)
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .base import CodaJsonl, Lettura, iso, redigi

EVENTI_FILE = "~/.claude/guardian/events.jsonl"
USAGE_FILE = "~/.claude/guardian/usage.json"
INATTIVO_MIN = 30
USAGE_MAX_ETA = 900  # secondi: dati di utilizzo più vecchi non vengono inviati

STATO_DA_EVENTO = {"UserPromptSubmit": "working", "PreToolUse": "working", "PostToolUse": "working",
                   "Stop": "idle", "SubagentStop": "working"}


def stato_da_eventi(eventi: list[dict]) -> str | None:
    for e in reversed(eventi):
        ev = e.get("event", "")
        if ev == "Notification":
            msg = str(e.get("message", "")).lower()
            return "needs_approval" if ("permission" in msg or "permesso" in msg) else "waiting"
        if ev in STATO_DA_EVENTO:
            return STATO_DA_EVENTO[ev]
    return None


def log_da_evento(e: dict, condividi_prompt: bool) -> dict | None:
    ev = e.get("event", "")
    if ev == "UserPromptSubmit":
        msg = "Richiesta all'agente" + (f": {redigi(e.get('prompt', ''))}" if condividi_prompt and e.get("prompt") else "")
    elif ev in ("PreToolUse", "PostToolUse"):
        if ev == "PostToolUse":
            return None  # basta un log per strumento (PreToolUse): meno rumore
        msg = f"Strumento: {redigi(e.get('tool', '?'), 60)}"
    elif ev == "Notification":
        msg = f"In attesa: {redigi(e.get('message', ''), 120)}"
    elif ev in ("Stop", "SubagentStop"):
        msg = "Turno completato" if ev == "Stop" else "Subagente completato"
    else:
        return None
    return {"level": "warning" if ev == "Notification" else "info", "source": "hook", "message": msg,
            "ts": iso(e.get("ts"))}


def leggi_usage(path: str | Path = USAGE_FILE, ora: float | None = None) -> dict | None:
    try:
        u = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(u, dict) or (ora or time.time()) - float(u.get("ts", 0)) > USAGE_MAX_ETA:
        return None
    out = {}
    for k in ("five_hour", "seven_day"):
        w = u.get(k)
        if isinstance(w, dict) and isinstance(w.get("pct"), (int, float)):
            out[k] = {"pct": round(float(w["pct"]), 1), "resets_at": w.get("resets_at")}
    return out or None


class ClaudeCodeCollector:
    tipo = "claude-code"

    def __init__(self, casa: Path, eventi=EVENTI_FILE, usage=USAGE_FILE, condividi_prompt: bool = True):
        self.coda = CodaJsonl(eventi, casa / "offset-claude")
        self.usage_path, self.condividi = usage, condividi_prompt
        self.ultimo_evento: float | None = None

    def leggi(self, ora: float | None = None) -> Lettura:
        ora = ora or time.time()
        eventi = self.coda.nuove()
        r = Lettura(usage=leggi_usage(self.usage_path, ora))
        if eventi:
            self.ultimo_evento = max(float(e.get("ts", ora)) if isinstance(e.get("ts"), (int, float)) else ora
                                     for e in eventi)
            r.stato = stato_da_eventi(eventi)
            r.logs = [x for x in (log_da_evento(e, self.condividi) for e in eventi) if x]
        elif self.ultimo_evento is None or ora - self.ultimo_evento > INATTIVO_MIN * 60:
            r.stato = "unknown"
        if r.usage and max(w["pct"] for w in r.usage.values()) >= 100:
            r.error = "Limite di utilizzo raggiunto"
        return r
