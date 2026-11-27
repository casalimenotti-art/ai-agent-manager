"""Planner: trasforma un obiettivo in un piano strutturato usando un provider AI tramite il router.

Senza provider utilizzabile solleva PlannerNonDisponibile: Guardian non inventa piani.
Il piano è solo una proposta: diventa task solo quando una persona lo conferma.
"""
from __future__ import annotations

import json

from guardian.core.models import ACTION_TYPES
from guardian.planner.assign import suggerisci
from guardian.planner.schema import Plan, da_dict
from guardian.providers.base import ProviderNonDisponibile

SYSTEM_PROMPT = f"""Sei il planner di Guardian, il centro di coordinamento degli agenti AI di NEXO (3 collaboratori).
Trasforma l'obiettivo in un piano concreto. Non affermare di aver eseguito azioni: produci solo un piano.
Non inventare accessi, risultati o integrazioni. Rendi espliciti prerequisiti, rischi e approvazioni necessarie.
Ogni invio di email, pubblicazione, contatto con clienti, spesa, pagamento, modifica irreversibile, operazione su account
esterni o comando pericoloso richiede approvazione umana (requires_approval true e action_type appropriato).
Assegna un agente solo scegliendo tra quelli elencati, in base alle capacità; altrimenti lascia agent null.
Restituisci SOLO JSON valido:
{{"summary": "...", "tasks": [{{"title": "...", "description": "...", "priority": "bassa|media|alta|urgente",
  "depends_on": [0], "agent": "id-agente o null", "capabilities": ["..."], "expected_result": "...",
  "completion_criteria": "...", "requires_approval": false, "action_type": "{'|'.join(ACTION_TYPES)}",
  "approval_reason": "..."}}],
 "assumptions": ["..."], "missing_integrations": ["..."]}}
Da 2 a 10 task. depends_on usa gli indici (da 0) di altri task del piano, senza cicli."""


class PlannerNonDisponibile(RuntimeError):
    pass


def prompt_utente(goal: str, context: str, agents: list[dict], projects: list[dict]) -> str:
    agenti = [{"id": a["id"], "tipo": a["tipo"], "collaboratore": a["user_id"], "capacita": a.get("capabilities") or [],
               "disponibile": a.get("disponibile", True)} for a in agents]
    return (f"Obiettivo:\n{goal}\n\nContesto e vincoli:\n{context or 'nessuno'}\n\n"
            f"Agenti disponibili:\n{json.dumps(agenti, ensure_ascii=False)}\n\n"
            f"Progetti attivi: {', '.join(p['nome'] for p in projects) or 'nessuno'}")


def make_plan(goal: str, context: str, agents: list[dict], projects: list[dict], router,
              tasks: list[dict] | None = None) -> tuple[Plan, str, str]:
    """(piano validato, provider, modello). Completa l'agente suggerito con l'assegnazione deterministica."""
    try:
        risposta, provider = router.complete_json(SYSTEM_PROMPT, prompt_utente(goal, context, agents, projects))
    except ProviderNonDisponibile as e:
        raise PlannerNonDisponibile(str(e)) from None
    piano = da_dict(risposta, goal, [a["id"] for a in agents])
    for t in piano.tasks:
        if not t.agent and t.capabilities:
            t.agent = suggerisci(t.capabilities, agents, tasks or [])
    return piano, provider.nome, provider.model
