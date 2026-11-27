from datetime import datetime, timedelta, timezone

import pytest

from guardian.core.models import Handoff, ValidazioneError, stato_dispositivo
from guardian.core.store import seed_users_da_registro
from guardian.core.store_sqlite import SqliteStore


@pytest.fixture
def s():
    st = SqliteStore(":memory:")
    seed_users_da_registro(st)
    return st


def test_seed_users(s):
    assert {u["id"] for u in s.users()} >= {"menotti", "amico1", "amico2"}


def test_task_lifecycle_and_events(s):
    t = s.create_task("Sito ottica", "demo", "menotti", "Claude Code", "alta", "bozza", created_by="menotti")
    assert t["stato"] == "backlog" and t["files_changed"] == []
    t = s.update_task(t["id"], by="amico1", stato="running", files_changed="a.py\nb.html")
    assert t["stato"] == "running" and t["files_changed"] == ["a.py", "b.html"]
    tipi = [e["event_type"] for e in s.events()]
    assert tipi == ["task_started", "task_created"]
    s.update_task(t["id"], stato="in corso")  # alias v1 accettato
    assert s.task(t["id"])["stato"] == "running"


def test_validazioni(s):
    with pytest.raises(ValidazioneError):
        s.create_task("")
    with pytest.raises(ValidazioneError):
        s.create_task("x", priorita="altissima")
    with pytest.raises(ValidazioneError):
        s.create_task("x", descrizione="api_key = sk-abcdefghijklmnopqrstuvwxyz")
    t = s.create_task("x")
    with pytest.raises(ValidazioneError):
        s.update_task(t["id"], stato="boh")


def test_device_token_hidden_and_heartbeat(s):
    d, token = s.register_device("menotti", "PC-Menotti", "Claude Code")
    assert "token_hash" not in d and token.startswith("gdn_")
    assert stato_dispositivo(d) == "offline"
    d = s.bridge_heartbeat(token, "occupato", model="opus")
    assert stato_dispositivo(d) == "occupato" and d["model"] == "opus"
    with pytest.raises(PermissionError):
        s.bridge_heartbeat("sbagliato")
    s.revoke_device(d["id"])
    with pytest.raises(PermissionError):
        s.bridge_heartbeat(token)


def test_stato_offline_se_heartbeat_vecchio():
    vecchio = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    assert stato_dispositivo({"last_seen": vecchio, "stato": "online"}) == "offline"
    recente = datetime.now(timezone.utc).isoformat()
    assert stato_dispositivo({"last_seen": recente, "stato": "online", "limit_reached": True}) == "limite"


def test_handoff_and_pull(s):
    d, token = s.register_device("amico1", "PC-Niko", "Codex")
    t = s.create_task("Bozze contatto", responsabile="amico1", priorita="urgente", stato="ready")
    s.create_task("Altro", responsabile="menotti", stato="ready")
    s.create_task("Idea", responsabile="amico1")  # backlog: non viene scaricato
    assert [x["id"] for x in s.bridge_pull_tasks(token)] == [t["id"]]
    hid = s.bridge_checkpoint(token, task_id=t["id"], summary="Bozze 3/10", next_step="Bozza 4", files_changed=["x.md"])
    h = s.handoffs(t["id"])[0]
    assert h["id"] == hid and h["agent_name"] == "Codex" and h["files_changed"] == ["x.md"]
    assert s.task(t["id"])["next_step"] == "Bozza 4"
    assert [x for x in s.devices() if x["id"] == d["id"]][0]["last_checkpoint"]


def test_handoff_markdown():
    h = Handoff(agent_name="Claude", summary="obiettivo", next_step="fare X", task_id=3, files_changed=["a"]).valida()
    md = h.markdown()
    assert "## Prossimo passo\nfare X" in md and "- a" in md and "task #3" in md
    with pytest.raises(ValidazioneError):
        Handoff(agent_name="c", summary="s", next_step="").valida()


def test_approvals(s):
    aid = s.request_approval("Inviare email", "a cliente", requested_by="amico1")
    assert s.approvals("richiesta")[0]["id"] == aid
    s.decide_approval(aid, "approvata", "menotti")
    a = s.approvals()[0]
    assert a["status"] == "approvata" and a["decided_by"] == "menotti"
    s.decide_approval(aid, "rifiutata", "amico2")  # già decisa: non cambia
    assert s.approvals()[0]["status"] == "approvata"
    with pytest.raises(ValidazioneError):
        s.decide_approval(aid, "richiesta", "x")


def test_import_registro_idempotente(s):
    _, token = s.register_device("menotti", "PC", "")
    righe = [{"chi": "menotti", "agente": "claude-code", "azione": "fatto x", "file": ["a"], "esito": "fatto",
              "ts": "2026-11-27T02:12:53+00:00", "external_key": "registro:1"},
             {"chi": "sconosciuto", "azione": "y", "external_key": "registro:2"}]
    assert s.bridge_import_registro(token, righe) == 1
    assert s.bridge_import_registro(token, righe) == 0
    e = s.events()[0]
    assert e["message"] == "fatto x [fatto]" and e["timestamp"].startswith("2026-11-27")
