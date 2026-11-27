"""Adapter degli agenti: come Guardian sa cosa fa un agente.

Attivi oggi (verificati dai test):
- StatusFileAdapter: legge un file JSON locale (~/.guardian/stato.json) scritto a mano, da uno script o da un hook.
- Registro git: bridge/guardian_bridge.py sync-registro importa registro/*.jsonl (vedi AGENTS.md).

NON attivi (solo interfaccia, nessun accesso agli account personali Claude/Codex):
- ClaudeCodeHookAdapter: un hook PostToolUse/Stop di Claude Code potrà scrivere il file di stato.
- CodexAdapter: Codex non espone eventi locali stabili; oggi usa il registro + comandi del bridge.
- GatewayAdapter (FreeLLMAPI o altri): per modelli API gratuiti, da collegare solo con chiavi autorizzate.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

CAMPI_STATO = ("stato", "agent_name", "model", "current_task", "error", "limit_reached")


class AgentAdapter(Protocol):
    nome: str
    attivo: bool

    def stato(self) -> dict:
        """Campi per bridge_heartbeat (sottoinsieme di CAMPI_STATO). {} = nessun dato disponibile."""


class StatusFileAdapter:
    nome, attivo = "file di stato", True

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()

    def stato(self) -> dict:
        try:
            d = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return {k: d[k] for k in CAMPI_STATO if k in d} if isinstance(d, dict) else {}

    def scrivi(self, **campi) -> None:
        """Usato da script/hook locali per aggiornare lo stato senza rete."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        attuale = self.stato()
        attuale.update({k: v for k, v in campi.items() if k in CAMPI_STATO})
        self.path.write_text(json.dumps(attuale, ensure_ascii=False), encoding="utf-8")


class _NonCollegato:
    attivo = False
    motivo = "Integrazione non ancora implementata."

    def stato(self) -> dict:
        return {}


class ClaudeCodeHookAdapter(_NonCollegato):
    nome = "Claude Code (hook)"
    motivo = "Da collegare: hook Claude Code che chiama StatusFileAdapter.scrivi()."


class CodexAdapter(_NonCollegato):
    nome = "Codex"
    motivo = "Nessuna API di eventi locale: usare registro/scrivi.py + comandi del bridge."


class GatewayAdapter(_NonCollegato):
    nome = "Gateway modelli (FreeLLMAPI ecc.)"
    motivo = "Richiede chiavi API autorizzate: non attivo."


ADAPTERS_PREVISTI = (ClaudeCodeHookAdapter(), CodexAdapter(), GatewayAdapter())
