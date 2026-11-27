import pytest
from streamlit.testing.v1 import AppTest

PAGINE = ["Overview", "Agenti", "Task", "Progetti", "Attività", "Log", "Handoff", "Memoria", "Approvazioni", "Notifiche",
          "Dispositivi"]


@pytest.fixture
def at(tmp_path, monkeypatch):
    monkeypatch.setenv("GUARDIAN_DB", str(tmp_path / "hub.db"))
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    from guardian.core.store_sqlite import SqliteStore
    s = SqliteStore(tmp_path / "hub.db")
    from guardian.core.store import seed_users_da_registro
    seed_users_da_registro(s)
    p = s.create_project("Nexo", "progetto di prova", "menotti")
    t = s.create_task("Task di prova", responsabile="menotti", stato="ready", project_id=p["id"])
    s.create_task("Dipendente", stato="planned", depends_on=[t["id"]], project_id=p["id"])
    a = s.bridge_agent_register(tok := s.register_device("menotti", "PC2")[1], "menotti-claude", "Claude Code", "claude-code")
    s.bridge_agent_state(tok, a["id"], "working")
    s.bridge_agent_logs(tok, a["id"], [{"message": "Strumento: Bash", "source": "hook"}])
    _, tok = s.register_device("menotti", "PC", "Claude Code")
    s.bridge_heartbeat(tok, "occupato", current_task=t["id"])
    s.bridge_checkpoint(tok, task_id=t["id"], summary="stato", next_step="passo", tests_pending="e2e")
    s.add_memory("decisione", "Backend Supabase", "piano v2", p["id"])
    s.request_approval("Inviare email", requested_by="amico1", action_type="email", reason="preventivo",
                       impact="1 email", data_involved="indirizzo del cliente", task_id=t["id"])
    a = AppTest.from_file("../guardian/app.py", default_timeout=30)
    return a


@pytest.mark.parametrize("pagina", PAGINE)
def test_pagine_senza_eccezioni(at, pagina):
    at.session_state["pagina"] = pagina
    at.run()
    assert not at.exception, at.exception


def test_overview_dati_reali(at):
    at.run()
    metriche = {m.label: m.value for m in at.metric}
    assert metriche["Task in esecuzione"] == "0" and metriche["Agenti al lavoro"] == "1"
    assert metriche["Approvazioni da decidere"] == "1"


def test_pagina_log_e_approvazioni(at):
    at.session_state["pagina"] = "Log"
    at.run()
    assert not at.exception and at.dataframe
    at.session_state["pagina"] = "Approvazioni"
    at.run()
    testo = " ".join(m.value for m in at.markdown)
    assert "Impatto previsto" in testo and "Dati coinvolti" in testo
