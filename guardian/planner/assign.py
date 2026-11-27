"""Suggerimento deterministico dell'agente per un task: capacità, disponibilità, carico. Decide sempre una persona."""
from __future__ import annotations

from guardian.core.models import TASK_TERMINALI, stato_agente

STATI_ESCLUSI = ("error", "offline")


def carico(agent_id: str, tasks: list[dict]) -> int:
    return sum(1 for t in tasks if t.get("assigned_agent_id") == agent_id and t["stato"] not in TASK_TERMINALI)


def suggerisci(capacita: list[str], agenti: list[dict], tasks: list[dict]) -> str | None:
    richieste = {c.lower() for c in capacita or []}
    candidati = []
    for a in agenti:
        if not a.get("disponibile", True) or stato_agente(a) in STATI_ESCLUSI:
            continue
        comuni = len(richieste & {c.lower() for c in a.get("capabilities") or []})
        if richieste and not comuni:
            continue
        candidati.append((-comuni, carico(a["id"], tasks), a["id"]))
    return min(candidati)[2] if candidati else None
