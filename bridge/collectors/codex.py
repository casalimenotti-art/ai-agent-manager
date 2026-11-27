"""Collector Codex: legge gli eventi scritti da bridge/hooks/codex_notify.py, configurato come `notify`
in ~/.codex/config.toml. Codex chiama il programma notify a fine turno (tipo "agent-turn-complete"):
non esiste un evento di inizio, quindi lo stato può essere solo idle (dopo un turno) o unknown.
DA VERIFICARE sui PC degli amici con la loro versione di Codex.
"""
from __future__ import annotations

import time
from pathlib import Path

from .base import CodaJsonl, Lettura, iso, redigi

EVENTI_FILE = "~/.guardian/codex-events.jsonl"
INATTIVO_MIN = 30


class CodexCollector:
    tipo = "codex"

    def __init__(self, casa: Path, eventi=EVENTI_FILE, condividi_prompt: bool = True):
        self.coda = CodaJsonl(eventi, casa / "offset-codex")
        self.condividi = condividi_prompt
        self.ultimo_evento: float | None = None

    def leggi(self, ora: float | None = None) -> Lettura:
        ora = ora or time.time()
        eventi = [e for e in self.coda.nuove() if e.get("type") == "agent-turn-complete"]
        r = Lettura()
        if eventi:
            self.ultimo_evento = ora
            r.stato = "idle"
            for e in eventi:
                testo = redigi(e.get("prompt", "")) if self.condividi and e.get("prompt") else ""
                r.logs.append({"level": "info", "source": "notify", "ts": iso(e.get("ts")),
                               "message": "Turno Codex completato" + (f": {testo}" if testo else "")})
        elif self.ultimo_evento is None or ora - self.ultimo_evento > INATTIVO_MIN * 60:
            r.stato = "unknown"
        return r
