import glob
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

from guardian.core.models import ValidazioneError
from guardian.core.store import seed_users_da_registro
from guardian.core.store_sqlite import SCHEMA_V1, SqliteStore


@pytest.fixture
def s():
    st = SqliteStore(":memory:")
    seed_users_da_registro(st)
    return st


def test_duplicati_solo_tra_aperti(s):
    p = s.create_project("Nexo")
    s.create_task("Sito Bellini", project_id=p["id"])
    with pytest.raises(ValidazioneError, match="Esiste già"):
        s.create_task("sito bellini", project_id=p["id"])
    s.create_task("Sito Bellini")  # altro progetto (nessuno): ammesso
    t = s.tasks(project_id=p["id"])[0]
    s.update_task(t["id"], stato="cancelled")
    s.create_task("Sito Bellini", project_id=p["id"])  # il vecchio è chiuso: ammesso
    with pytest.raises(ValidazioneError, match="progetto"):
        s.create_project("NEXO")


def test_dipendenze(s):
    a = s.create_task("A", stato="ready")
    with pytest.raises(ValidazioneError, match="dipendenze"):
        s.create_task("B", stato="ready", depends_on=[a["id"]])
    b = s.create_task("B", stato="planned", depends_on=[a["id"]])
    with pytest.raises(ValidazioneError, match="dipendenze"):
        s.update_task(b["id"], stato="running")
    with pytest.raises(ValidazioneError, match="inesistenti"):
        s.create_task("C", depends_on=[999])
    with pytest.raises(ValidazioneError, match="sé stesso"):
        s.update_task(b["id"], depends_on=[b["id"]])
    s.update_task(a["id"], stato="completed")
    assert s.update_task(b["id"], stato="ready")["stato"] == "ready"


def test_un_running_per_agente(s):
    s.upsert_agent("menotti-claude", "menotti", "Claude Code", "claude-code", capabilities=["python", "siti"])
    t1 = s.create_task("T1", stato="ready", assigned_agent_id="menotti-claude")
    t2 = s.create_task("T2", stato="ready", assigned_agent_id="menotti-claude")
    s.update_task(t1["id"], stato="running")
    with pytest.raises(ValidazioneError, match="già un task in esecuzione"):
        s.update_task(t2["id"], stato="running")
    tipi = [e["event_type"] for e in s.events()]
    assert "task_assigned" in tipi and "task_started" in tipi


def test_approvazioni_cambiano_stato_e_notificano(s):
    t = s.create_task("Email preventivo", stato="ready", responsabile="amico1")
    aid = s.request_approval("Inviare email", "preventivo", t["id"], "amico1", action_type="email",
                             reason="cliente interessato", impact="1 email", data_involved="email del cliente")
    assert s.task(t["id"])["stato"] == "needs_approval"
    assert all(len(s.notifications(u, True)) == 1 for u in ("menotti", "amico1", "amico2"))
    s.decide_approval(aid, "approvata", "menotti")
    assert s.task(t["id"])["stato"] == "ready"
    assert s.notifications("amico1", True)[0]["kind"] == "approval_decided"
    a2 = s.request_approval("Pagare", task_id=t["id"], requested_by="amico1", action_type="pagamento")
    s.decide_approval(a2, "rifiutata", "menotti")
    assert s.task(t["id"])["stato"] == "blocked"
    with pytest.raises(ValidazioneError):
        s.request_approval("x", action_type="boh")
    s.mark_read("amico1")
    assert s.notifications("amico1", True) == []


def test_task_fallito_e_agente_in_errore_notificano(s):
    s.upsert_agent("amico1-codex", "amico1", "Codex", "codex")
    t = s.create_task("Bozze", stato="running", responsabile="amico1")
    s.update_task(t["id"], stato="failed", error="timeout")
    s.set_agent_state("amico1-codex", "error", error="crash")
    kinds = {n["kind"] for n in s.notifications("amico1")}
    assert {"task_failed", "agent_error"} <= kinds
    ev = s.events()[0]
    assert ev["severity"] == "error" and "(manuale)" in ev["message"]
    with pytest.raises(ValidazioneError):
        s.set_agent_state("amico1-codex", "felice")


def test_migrazione_da_db_v1(tmp_path):
    db = tmp_path / "v1.db"
    c = sqlite3.connect(db)
    c.executescript(SCHEMA_V1.replace("DEFAULT 'backlog'", "DEFAULT 'in attesa'"))
    c.execute("INSERT INTO users (id, nome) VALUES ('menotti', 'M')")
    for titolo, stato in (("Sito", "in attesa"), ("Sito", "in corso"), ("Fatto", "completato")):
        c.execute("INSERT INTO tasks (titolo, stato, created_at, updated_at) VALUES (?,?,'2026-11-27','2026-11-27')",
                  (titolo, stato))
    c.commit()
    c.close()
    s = SqliteStore(db)
    assert [(t["titolo"], t["stato"]) for t in sorted(s.tasks(), key=lambda t: t["id"])] == [
        ("Sito", "ready"), ("Sito (#2)", "running"), ("Fatto", "completed")]
    assert s.tasks()[0]["depends_on"] == []
    SqliteStore(db)  # seconda apertura: idempotente


@pytest.mark.skipif(not glob.glob("/usr/lib/postgresql/*/bin/initdb") or not shutil.which("psql"),
                    reason="PostgreSQL non installato")
def test_migrazioni_postgres():
    r = subprocess.run(["bash", str(Path(__file__).parent / "pg" / "run.sh")], capture_output=True, text=True,
                       timeout=300)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-2000:]
    assert "CHECK 002 OK" in r.stdout and "CHECK 003 OK" in r.stdout and "CHECK 004 OK" in r.stdout
