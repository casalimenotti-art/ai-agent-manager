from datetime import datetime, timedelta, timezone

import pytest

from guardian.core.models import ValidazioneError
from guardian.core.store import conferma_piano, seed_users_da_registro
from guardian.core.store_sqlite import SqliteStore
from guardian.planner.assign import suggerisci
from guardian.planner.planner import PlannerNonDisponibile, make_plan
from guardian.planner.report import report
from guardian.planner.report import testo_report as rendi_testo
from guardian.planner.schema import da_dict
from guardian.providers.router import Router
from tests.test_providers import FintoLLM, prov

PIANO = {"summary": "Offerta ai clienti", "tasks": [
    {"title": "Elenco clienti", "priority": "alta", "capabilities": ["dati"], "agent": "amico1-codex"},
    {"title": "Bozza offerta", "depends_on": [0], "priority": "medio", "capabilities": ["testi"]},
    {"title": "Invio email", "depends_on": [1, 1, 7, "x"], "action_type": "email", "agent": "inventato"}],
    "assumptions": ["lista già verificata"], "missing_integrations": ["Gmail non collegato"]}


@pytest.fixture
def s():
    st = SqliteStore(":memory:")
    seed_users_da_registro(st)
    st.upsert_agent("amico1-codex", "amico1", "Codex", "codex", capabilities=["dati", "vendite"])
    st.upsert_agent("menotti-claude", "menotti", "Claude Code", "claude-code", capabilities=["testi", "siti"])
    return st


def test_schema_valida_e_corregge():
    p = da_dict(PIANO, "Offerta", ["amico1-codex", "menotti-claude"])
    assert [t.priority for t in p.tasks] == ["alta", "media", "media"]
    assert p.tasks[2].depends_on == [1] and p.tasks[2].agent is None and p.tasks[2].requires_approval
    assert p.tasks[0].agent == "amico1-codex" and p.missing == ["Gmail non collegato"]
    with pytest.raises(ValidazioneError, match="ciclo"):
        da_dict({"tasks": [{"title": "A", "depends_on": [1]}, {"title": "B", "depends_on": [0]}]}, "x")
    with pytest.raises(ValidazioneError, match="stesso titolo"):
        da_dict({"tasks": [{"title": "A"}, {"title": "a"}]}, "x")
    with pytest.raises(ValidazioneError):
        da_dict({"tasks": []}, "x")
    with pytest.raises(ValidazioneError, match="password"):
        da_dict({"tasks": [{"title": "usa password=abc123"}]}, "x")


def test_assegnazione_deterministica(s):
    agenti = s.agents()
    assert suggerisci(["testi"], agenti, []) == "menotti-claude"
    assert suggerisci(["cucina"], agenti, []) is None
    tasks = [{"assigned_agent_id": "amico1-codex", "stato": "running"}]
    assert suggerisci([], agenti, tasks) == "menotti-claude"  # meno carico
    s.set_agent_state("menotti-claude", "error", error="x")
    s._x("UPDATE agents SET last_heartbeat=? WHERE id='menotti-claude'", (datetime.now(timezone.utc).isoformat(),))
    assert suggerisci(["testi"], s.agents(), []) is None


def test_make_plan_con_server_finto_e_senza_provider(s, server):
    import json
    FintoLLM.risposte = {"llm": (200, json.dumps(PIANO))}
    piano, prov_nome, model = make_plan("Offerta", "", s.agents(), [], Router([prov(server, "llm")]))
    assert prov_nome == "llm" and piano.tasks[1].agent == "menotti-claude"  # completato da assign (capacità testi)
    corpo = FintoLLM.ricevuti[0]["body"]["messages"][1]["content"]
    assert "amico1-codex" in corpo and "Offerta" in corpo
    with pytest.raises(PlannerNonDisponibile):
        make_plan("x", "", [], [], Router([]))


def test_conferma_piano_crea_task_dipendenze_e_approvazioni(s):
    pr = s.create_project("Vendite")
    piano = da_dict(PIANO, "Offerta", ["amico1-codex", "menotti-claude"]).to_dict()
    pid = s.create_plan("Offerta", piano, pr["id"], "llm", "m", "menotti")
    ids = conferma_piano(s, pid, "menotti")
    t = [s.task(i) for i in ids]
    assert [x["stato"] for x in t] == ["ready", "planned", "needs_approval"]
    assert t[1]["depends_on"] == [ids[0]] and t[2]["depends_on"] == [ids[1]]
    assert t[0]["assigned_agent_id"] == "amico1-codex" and all(x["plan_id"] == pid for x in t)
    assert s.approvals("richiesta")[0]["action_type"] == "email" and s.plan(pid)["stato"] == "confermato"
    with pytest.raises(ValidazioneError, match="già deciso"):
        conferma_piano(s, pid)
    pid2 = s.create_plan("Di nuovo", piano, pr["id"])
    with pytest.raises(ValidazioneError, match="già task aperti"):
        conferma_piano(s, pid2)
    assert len(s.tasks(project_id=pr["id"])) == 3  # niente piani a metà


def test_report_prossime_azioni(s):
    a = s.create_task("Bloccato", stato="blocked")
    s.create_task("Pronto senza agente", stato="ready")
    f = s.create_task("Fallito", stato="running")
    s.update_task(f["id"], stato="failed", error="timeout")
    vecchio = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    r0 = s.create_task("Fermo", stato="running")
    s._x("UPDATE tasks SET updated_at=? WHERE id=?", (vecchio, r0["id"]))
    s.request_approval("Pagare il dominio", requested_by="menotti", action_type="pagamento")
    r = report(s)
    testi = [x["testo"] for x in r["prossime_azioni"]]
    assert testi[0].startswith("Decidi l'approvazione") and r["approvazioni"] == 1
    assert any(f"#{a['id']}" in x and "Sblocca" in x for x in testi)
    assert any("fallito" in x and "timeout" in x for x in testi)
    assert any("fermo da 30 h" in x for x in testi)
    assert any("Assegna il task" in x and "suggerito" in x for x in testi)
    assert "Prossime azioni:" in rendi_testo(r)
