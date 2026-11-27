"""Piano strutturato prodotto dal planner, validato prima di diventare task."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

from guardian.core.models import ACTION_TYPES, ValidazioneError, pulisci

ALIAS_PRIORITA = {"bassa": "bassa", "basso": "bassa", "low": "bassa", "media": "media", "medio": "media",
                  "medium": "media", "alta": "alta", "alto": "alta", "high": "alta", "urgente": "urgente",
                  "urgent": "urgente", "critical": "urgente"}
MAX_TASK = 12


@dataclass
class PlanTask:
    title: str
    description: str = ""
    priority: str = "media"
    depends_on: list[int] = field(default_factory=list)  # indici di altri task del piano
    agent: str | None = None                             # id agente suggerito (solo tra quelli esistenti)
    capabilities: list[str] = field(default_factory=list)
    expected_result: str = ""
    completion_criteria: str = ""
    requires_approval: bool = False
    action_type: str = "altro"
    approval_reason: str = ""


@dataclass
class Plan:
    goal: str
    summary: str
    tasks: list[PlanTask]
    assumptions: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _lista(v, n=10, lun=300) -> list[str]:
    return [pulisci(str(x), lun) for x in (v if isinstance(v, list) else []) if str(x).strip()][:n]


def _aciclico(deps: list[list[int]]) -> bool:
    stato = [0] * len(deps)  # 0 nuovo, 1 in visita, 2 fatto

    def visita(i):
        if stato[i] == 1:
            return False
        if stato[i] == 2:
            return True
        stato[i] = 1
        ok = all(visita(j) for j in deps[i])
        stato[i] = 2
        return ok
    return all(visita(i) for i in range(len(deps)))


def da_dict(d: dict, goal: str, agent_ids=()) -> Plan:
    """Valida l'output del modello (o un piano salvato). Corregge ciò che è sicuro correggere, rifiuta il resto."""
    if not isinstance(d, dict) or not isinstance(d.get("tasks"), list) or not d["tasks"]:
        raise ValidazioneError("Il piano non contiene task.")
    grezzi = d["tasks"][:MAX_TASK]
    n, agenti = len(grezzi), {a.lower() for a in agent_ids}
    tasks = []
    for i, t in enumerate(grezzi):
        if not isinstance(t, dict):
            raise ValidazioneError(f"Task {i + 1} non valido.")
        deps = []
        for x in t.get("depends_on") or []:
            try:
                j = int(x)
            except (TypeError, ValueError):
                continue
            if 0 <= j < n and j != i and j not in deps:
                deps.append(j)
        agente = str(t.get("agent") or "").lower() or None
        tipo = str(t.get("action_type") or "altro")
        tasks.append(PlanTask(
            title=pulisci(t.get("title"), 200, True, f"titolo del task {i + 1}"),
            description=pulisci(t.get("description"), 2000),
            priority=ALIAS_PRIORITA.get(str(t.get("priority") or t.get("risk") or "media").lower(), "media"),
            depends_on=deps, agent=agente if agente in agenti else None,
            capabilities=_lista(t.get("capabilities"), 8, 40),
            expected_result=pulisci(t.get("expected_result"), 1000),
            completion_criteria=pulisci(t.get("completion_criteria") or t.get("success_criteria"), 1000),
            requires_approval=bool(t.get("requires_approval")) or tipo in ACTION_TYPES[:-1],
            action_type=tipo if tipo in ACTION_TYPES else "altro",
            approval_reason=pulisci(t.get("approval_reason"), 500)))
    if not _aciclico([t.depends_on for t in tasks]):
        raise ValidazioneError("Le dipendenze del piano formano un ciclo.")
    titoli = [t.title.lower() for t in tasks]
    if len(set(titoli)) != len(titoli):
        raise ValidazioneError("Il piano contiene task con lo stesso titolo.")
    return Plan(goal=pulisci(goal, 1000, True, "obiettivo"), summary=pulisci(d.get("summary"), 1000),
                tasks=tasks, assumptions=_lista(d.get("assumptions")), missing=_lista(d.get("missing_integrations")
                                                                                   or d.get("missing")))
