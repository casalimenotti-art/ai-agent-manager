"""Report e prossime azioni calcolati dal database (deterministici, sempre disponibili, nessun modello AI)."""
from __future__ import annotations

from guardian.core.models import TASK_STATI, TASK_TERMINALI, eta_secondi, stato_agente
from guardian.planner.assign import suggerisci

FERMO_ORE = 24
USO_ALTO = 90


def report(store) -> dict:
    tasks, agents, appr = store.tasks(), store.agents(), store.approvals("richiesta")
    per_id = {t["id"]: t for t in tasks}
    azioni: list[dict] = []

    def az(priorita: int, testo: str, ref: str = ""):
        azioni.append({"priorita": priorita, "testo": testo, "ref": ref})

    for a in appr:
        az(1, f"Decidi l'approvazione #{a['id']}: {a['action']}", f"approvals/{a['id']}")
    for a in agents:
        s = stato_agente(a)
        if s == "error":
            az(1, f"Controlla l'agente {a['nome']}: {a.get('error') or 'in errore'}", f"agents/{a['id']}")
        elif s == "needs_approval":
            az(1, f"{a['nome']} aspetta un permesso sul PC di {a['user_id']}", f"agents/{a['id']}")
        uso = max((w.get("pct", 0) for w in (a.get("usage") or {}).values() if isinstance(w, dict)), default=0)
        if uso >= USO_ALTO:
            az(2, f"{a['nome']} è al {uso:.0f}% di utilizzo: salva un handoff prima del limite", f"agents/{a['id']}")
    for t in tasks:
        ref = f"tasks/{t['id']}"
        if t["stato"] == "failed":
            az(2, f"Analizza il task fallito #{t['id']} {t['titolo']}" + (f": {t['error']}" if t.get("error") else ""), ref)
        elif t["stato"] == "blocked":
            az(2, f"Sblocca il task #{t['id']} {t['titolo']}", ref)
        elif t["stato"] == "running" and (eta_secondi(t["updated_at"]) or 0) > FERMO_ORE * 3600:
            ore = int((eta_secondi(t["updated_at"]) or 0) // 3600)
            az(2, f"Task #{t['id']} in esecuzione ma fermo da {ore} h: chiedi un checkpoint", ref)
        elif t["stato"] == "ready" and not t.get("assigned_agent_id"):
            sug = suggerisci([], agents, tasks)
            az(3, f"Assegna il task #{t['id']} {t['titolo']}" + (f" (suggerito: {sug})" if sug else " (nessun agente disponibile)"), ref)
        elif t["stato"] == "planned" and t.get("depends_on") and all(
                per_id.get(d, {}).get("stato") == "completed" for d in t["depends_on"]):
            az(3, f"Le dipendenze del task #{t['id']} sono completate: portalo a ready", ref)
    conteggi = {s: sum(t["stato"] == s for t in tasks) for s in TASK_STATI}
    aperti = sum(t["stato"] not in TASK_TERMINALI for t in tasks)
    return {"conteggi": conteggi, "aperti": aperti, "approvazioni": len(appr),
            "agenti": {a["id"]: stato_agente(a) for a in agents},
            "prossime_azioni": sorted(azioni, key=lambda x: x["priorita"])}


def testo_report(r: dict) -> str:
    c = r["conteggi"]
    righe = [f"Task aperti: {r['aperti']} (in esecuzione {c['running']}, pronti {c['ready']}, bloccati {c['blocked']}, "
             f"falliti {c['failed']}, in attesa di approvazione {c['needs_approval']}). Completati: {c['completed']}.",
             f"Approvazioni da decidere: {r['approvazioni']}."]
    if r["prossime_azioni"]:
        righe.append("Prossime azioni:")
        righe += [f"{i}. {a['testo']}" for i, a in enumerate(r["prossime_azioni"][:10], 1)]
    else:
        righe.append("Nessuna azione urgente.")
    return "\n".join(righe)
