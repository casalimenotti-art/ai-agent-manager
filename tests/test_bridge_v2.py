import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from bridge import install_hooks
from bridge.collectors.base import CodaJsonl, redigi
from bridge.collectors.claude_code import ClaudeCodeCollector, leggi_usage, stato_da_eventi
from bridge.collectors.codex import CodexCollector
from guardian.core.models import ValidazioneError, stato_agente
from guardian.core.store import seed_users_da_registro
from guardian.core.store_sqlite import SqliteStore

BRIDGE = Path(__file__).resolve().parent.parent / "bridge" / "guardian_bridge.py"


def scrivi(path: Path, righe):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in righe:
            f.write(json.dumps(r) + "\n")


def test_coda_jsonl_incrementale_e_riga_incompleta(tmp_path):
    f = tmp_path / "e.jsonl"
    scrivi(f, [{"a": 1}])
    with open(f, "a") as h:
        h.write('{"a": 2')  # riga ancora in scrittura
    c = CodaJsonl(f, tmp_path / "off")
    assert c.nuove() == [{"a": 1}]
    with open(f, "a") as h:
        h.write("}\n")
    assert c.nuove() == [{"a": 2}] and c.nuove() == []


def test_redigi_toglie_segreti_e_tronca():
    assert "sk-" not in redigi("usa la chiave sk-abcdefghijklmnopqrstuv per favore")
    assert len(redigi("x" * 500)) == 201


def test_stato_da_eventi():
    assert stato_da_eventi([{"event": "UserPromptSubmit"}, {"event": "PreToolUse"}]) == "working"
    assert stato_da_eventi([{"event": "PreToolUse"}, {"event": "Stop"}]) == "idle"
    assert stato_da_eventi([{"event": "Notification", "message": "Claude needs your permission to use Bash"}]) == "needs_approval"
    assert stato_da_eventi([{"event": "Notification", "message": "Claude is waiting for your input"}]) == "waiting"
    assert stato_da_eventi([]) is None


def test_collector_claude(tmp_path):
    ev, us = tmp_path / "events.jsonl", tmp_path / "usage.json"
    ora = time.time()
    scrivi(ev, [{"ts": ora - 5, "event": "UserPromptSubmit", "prompt": "rifai il sito, password=segreta123"},
                {"ts": ora - 4, "event": "PreToolUse", "tool": "Bash"},
                {"ts": ora - 3, "event": "PostToolUse", "tool": "Bash"}])
    us.write_text(json.dumps({"five_hour": {"pct": 42.4, "resets_at": 1}, "seven_day": {"pct": 18}, "ts": ora}))
    c = ClaudeCodeCollector(tmp_path, ev, us, condividi_prompt=True)
    r = c.leggi(ora)
    assert r.stato == "working" and r.usage["five_hour"]["pct"] == 42.4
    msgs = [x["message"] for x in r.logs]
    assert msgs[1] == "Strumento: Bash" and "segreta123" not in msgs[0] and len(r.logs) == 2
    assert c.leggi(ora + 60).stato is None  # nessun evento nuovo, ancora recente
    assert c.leggi(ora + 3600).stato == "unknown"  # troppo tempo senza eventi
    senza = ClaudeCodeCollector(tmp_path / "b", ev, us, condividi_prompt=False).leggi(ora)
    assert senza.logs[0]["message"] == "Richiesta all'agente"
    us.write_text(json.dumps({"five_hour": {"pct": 100}, "ts": ora}))
    assert ClaudeCodeCollector(tmp_path / "c", ev, us).leggi(ora).error == "Limite di utilizzo raggiunto"
    us.write_text(json.dumps({"five_hour": {"pct": 10}, "ts": ora - 3600}))
    assert leggi_usage(us, ora) is None  # dati vecchi: non inviati


def test_collector_codex(tmp_path):
    ev = tmp_path / "codex.jsonl"
    c = CodexCollector(tmp_path, ev)
    assert c.leggi().stato == "unknown"
    scrivi(ev, [{"ts": time.time(), "type": "agent-turn-complete", "prompt": "prepara bozze"}])
    r = c.leggi()
    assert r.stato == "idle" and "prepara bozze" in r.logs[0]["message"]


def test_hook_scripts_scrivono_eventi(tmp_path):
    env = {**os.environ, "GUARDIAN_EVENTS_FILE": str(tmp_path / "c.jsonl"),
           "GUARDIAN_CODEX_EVENTS_FILE": str(tmp_path / "x.jsonl")}
    hooks = BRIDGE.parent / "hooks"
    subprocess.run([sys.executable, str(hooks / "claude_hook.py")], input=json.dumps(
        {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": "segreto"}}), text=True,
        env=env, check=True)
    subprocess.run([sys.executable, str(hooks / "codex_notify.py"), json.dumps(
        {"type": "agent-turn-complete", "input-messages": ["ciao"], "last-assistant-message": "risposta privata"})],
        env=env, check=True)
    c = json.loads((tmp_path / "c.jsonl").read_text())
    assert c["event"] == "PreToolUse" and c["tool"] == "Edit" and "segreto" not in json.dumps(c)
    x = json.loads((tmp_path / "x.jsonl").read_text())
    assert x["type"] == "agent-turn-complete" and "risposta privata" not in json.dumps(x)


def test_install_hooks_merge_non_duplica(tmp_path):
    base = {"model": "x", "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "python guardian_hook.py"}]}]}}
    nuovo, aggiunti = install_hooks.unisci_hook_claude(base, "python3 claude_hook.py")
    assert "Stop" not in aggiunti and "Notification" in aggiunti and nuovo["model"] == "x"
    assert nuovo["hooks"]["PreToolUse"][0]["matcher"] == "*" and base["hooks"].get("PreToolUse") is None
    assert install_hooks.unisci_hook_claude(nuovo, "python3 claude_hook.py")[1] == []
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps(base))
    assert install_hooks.claude(False, settings) == 0 and json.loads(settings.read_text()) == base  # dry-run
    assert install_hooks.claude(True, settings, si=True) == 0
    assert "Notification" in json.loads(settings.read_text())["hooks"]
    assert list(tmp_path.glob("settings.json.bak-*"))


@pytest.fixture
def s():
    st = SqliteStore(":memory:")
    seed_users_da_registro(st)
    return st


def test_rpc_agenti_sqlite(s):
    _, tok = s.register_device("menotti", "PC-M")
    _, tok2 = s.register_device("amico1", "PC-N")
    a = s.bridge_agent_register(tok, "Menotti-Claude", "Claude Code", "claude-code", ["python"])
    assert a["id"] == "menotti-claude" and a["stato"] == "unknown" and a["capabilities"] == ["python"]
    with pytest.raises(PermissionError):
        s.bridge_agent_register(tok2, "menotti-claude", "x", "codex")
    with pytest.raises(PermissionError):
        s.bridge_agent_state(tok2, "menotti-claude", "working")
    a = s.bridge_agent_state(tok, "menotti-claude", "working", usage={"five_hour": {"pct": 10}})
    assert stato_agente(a) == "working" and a["usage"]["five_hour"]["pct"] == 10
    assert s.events()[0]["event_type"] == "agent_connected"
    vecchio = dict(a, last_heartbeat=(datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat())
    assert stato_agente(vecchio) == "unknown"
    assert s.bridge_agent_logs(tok, "menotti-claude", [{"message": "Strumento: Bash", "source": "hook"},
                                                       {"message": ""}]) == 1
    assert s.agent_logs(agent_id="menotti-claude")[0]["message"] == "Strumento: Bash"
    assert s.agent_logs(level="error") == []
    t = s.create_task("Sito", responsabile="menotti", stato="ready")
    altro = s.create_task("Altro", responsabile="amico1", stato="ready")
    with pytest.raises(ValidazioneError, match="collaboratore"):
        s.bridge_claim_task(tok, "menotti-claude", altro["id"])
    t = s.bridge_claim_task(tok, "menotti-claude", t["id"])
    assert t["stato"] == "running" and t["assigned_agent_id"] == "menotti-claude"
    assert s.agent("menotti-claude")["current_task_id"] == t["id"]
    with pytest.raises(ValidazioneError, match="ready"):
        s.bridge_claim_task(tok, "menotti-claude", t["id"])
    s.bridge_agent_state(tok, "menotti-claude", "error", error="crash")
    assert s.notifications("menotti", True)[0]["kind"] == "agent_error"


def test_bridge_run_end_to_end(tmp_path):
    db, casa = tmp_path / "hub.db", tmp_path / "casa"
    ev = tmp_path / "events.jsonl"
    env = {**os.environ, "GUARDIAN_HOME": str(casa), "GUARDIAN_CLAUDE_AGENT_ID": "menotti-claude",
           "GUARDIAN_EVENTS_FILE": str(ev), "GUARDIAN_USAGE_FILE": str(tmp_path / "nessuno.json"),
           "GUARDIAN_CAPABILITIES": "python, siti"}
    r = subprocess.run([sys.executable, str(BRIDGE), "--local", str(db), "init-local", "--user", "menotti", "--nome", "PC"],
                       capture_output=True, text=True, env=env)
    token = r.stdout.strip().split()[-1]
    env["GUARDIAN_DEVICE_TOKEN"] = token
    scrivi(ev, [{"ts": time.time(), "event": "UserPromptSubmit", "prompt": "ciao"}, {"ts": time.time(), "event": "Stop"}])
    r = subprocess.run([sys.executable, str(BRIDGE), "--local", str(db), "run", "--giri", "1"], capture_output=True,
                       text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    s = SqliteStore(db)
    a = s.agent("menotti-claude")
    assert a["stato"] == "idle" and a["capabilities"] == ["python", "siti"] and a["device_id"]
    assert [x["message"] for x in s.agent_logs()] == ["Turno completato", "Richiesta all'agente: ciao"]
    assert s.devices()[0]["last_seen"]
