import pytest
from streamlit.testing.v1 import AppTest

PAGINE = ["Overview", "Agenti", "Task", "Attività", "Handoff", "Approvazioni", "Dispositivi"]


@pytest.fixture
def at(tmp_path, monkeypatch):
    monkeypatch.setenv("GUARDIAN_DB", str(tmp_path / "hub.db"))
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    from guardian.core.store_sqlite import SqliteStore
    s = SqliteStore(tmp_path / "hub.db")
    from guardian.core.store import seed_users_da_registro
    seed_users_da_registro(s)
    t = s.create_task("Task di prova", responsabile="menotti")
    _, tok = s.register_device("menotti", "PC", "Claude Code")
    s.bridge_heartbeat(tok, "occupato", current_task=t["id"])
    s.bridge_checkpoint(tok, task_id=t["id"], summary="stato", next_step="passo")
    s.request_approval("Inviare email", requested_by="amico1")
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
    assert metriche["PC online"] == "1/1" and metriche["Task in esecuzione"] == "0"
    assert metriche["Approvazioni da decidere"] == "1"
