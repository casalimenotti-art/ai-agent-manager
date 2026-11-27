import json
import subprocess
import sys
from pathlib import Path

import pytest

from bridge import guardian_bridge as gb
from guardian_hub.store import SqliteStore

BRIDGE = Path(gb.__file__)


def run(db, *argv, token=None, env=None):
    import os
    e = {**os.environ, "GUARDIAN_DEVICE_TOKEN": token or "", **(env or {})}
    return subprocess.run([sys.executable, str(BRIDGE), "--local", str(db), *argv], capture_output=True, text=True,
                          env=e, timeout=60)


def test_end_to_end_locale(tmp_path):
    db = tmp_path / "hub.db"
    env = {"GUARDIAN_HOME": str(tmp_path / "home"), "GUARDIAN_AGENT": "Claude Code"}
    r = run(db, "init-local", "--user", "menotti", "--nome", "PC-Test", env=env)
    assert r.returncode == 0, r.stderr
    token = r.stdout.strip().split()[-1]
    stato = tmp_path / "stato.json"
    stato.write_text(json.dumps({"stato": "occupato", "model": "opus", "limit_reached": True}))
    assert run(db, "heartbeat", "--status-file", str(stato), token=token, env=env).returncode == 0
    s = SqliteStore(db)
    t = s.create_task("Prova", responsabile="menotti")
    assert run(db, "event", "nota", "test fatto", "--task", str(t["id"]), "--file", "x.py", token=token, env=env).returncode == 0
    r = run(db, "task-update", str(t["id"]), "--stato", "in corso", "--next", "finire", token=token, env=env)
    assert r.returncode == 0, r.stderr
    r = run(db, "checkpoint", "--task", str(t["id"]), "--summary", "metà", "--next", "finire test", token=token, env=env)
    assert r.returncode == 0, r.stderr
    assert list((tmp_path / "home" / "handoffs").glob("*.md"))
    r = run(db, "pull", token=token, env=env)
    assert f"#{t['id']}" in r.stdout
    assert json.loads((tmp_path / "home" / "inbox.json").read_text())[0]["id"] == t["id"]
    s = SqliteStore(db)
    d = s.devices()[0]
    assert d["stato"] == "occupato" and d["limit_reached"] and d["agent_name"] == "Claude Code"
    tipi = {e["event_type"] for e in s.events()}
    assert {"stato_dispositivo", "nota", "task_aggiornato", "checkpoint"} <= tipi
    # segreti rifiutati, token sbagliato rifiutato
    assert run(db, "event", "nota", "password=abc123", token=token, env=env).returncode == 2
    assert run(db, "pull", token="sbagliato", env=env).returncode == 2


def test_sync_registro(tmp_path):
    repo = tmp_path / "repo"
    (repo / "registro").mkdir(parents=True)
    righe = [{"ts": "2026-11-27T02:00:00+00:00", "chi": "menotti", "agente": "claude-code", "azione": "A", "file": [], "esito": "fatto"},
             {"ts": "2026-11-27T03:00:00+00:00", "chi": "amico1", "agente": "codex", "azione": "token: abcdef", "file": []}]
    (repo / "registro" / "x.jsonl").write_text("\n".join(json.dumps(r) for r in righe) + "\nnon json\n")
    lette = gb.righe_registro(repo)
    assert [r["azione"] for r in lette] == ["A"]  # riga con segreto e riga rotta scartate
    s = SqliteStore(":memory:")
    from guardian_hub.store import seed_users_da_registro
    seed_users_da_registro(s)
    _, token = s.register_device("menotti", "PC")
    c = gb.LocalClient(s, token)
    assert c.call("bridge_import_registro", rows=lette) == 1
    assert c.call("bridge_import_registro", rows=lette) == 0


def test_rpc_client_rifiuta_http():
    with pytest.raises(SystemExit):
        gb.RpcClient("http://esempio.it", "k", "t")


def test_rpc_client_payload(monkeypatch):
    visto = {}

    class R:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b"true"

    def finto(req, timeout):
        visto["url"], visto["body"], visto["h"] = req.full_url, json.loads(req.data), dict(req.headers)
        return R()

    monkeypatch.setattr(gb.urllib.request, "urlopen", finto)
    c = gb.RpcClient("https://x.supabase.co/", "anon", "tok")
    assert c.call("bridge_event", event_type="nota", message="m") is True
    assert visto["url"] == "https://x.supabase.co/rest/v1/rpc/bridge_event"
    assert visto["body"] == {"p_token": "tok", "p_event_type": "nota", "p_message": "m"}
    assert visto["h"]["Apikey"] == "anon"
