import os
import subprocess
import sys
from pathlib import Path

import pytest

from guardian.core.models import Handoff, ValidazioneError
from guardian.core.store import seed_users_da_registro
from guardian.core.store_sqlite import SqliteStore
from guardian.export_md import FINE, INIZIO, aggiorna_file, sezione_task

BRIDGE = Path(__file__).resolve().parent.parent / "bridge" / "guardian_bridge.py"


@pytest.fixture
def s():
    st = SqliteStore(":memory:")
    seed_users_da_registro(st)
    return st


def test_memoria_fonte_ricerca_e_sostituzione(s):
    p = s.create_project("Nexo")
    a = s.add_memory("decisione", "Usiamo Supabase come backend condiviso", "GUARDIAN_DECISIONS.md", p["id"], None, "menotti")
    with pytest.raises(ValidazioneError, match="fonte"):
        s.add_memory("decisione", "senza fonte", "")
    with pytest.raises(ValidazioneError, match="password"):
        s.add_memory("procedura", "login con password=abc123", "chat")
    with pytest.raises(ValidazioneError):
        s.add_memory("pettegolezzo", "x", "y")
    assert [m["id"] for m in s.memories(q="supabase BACKEND")] == [a]
    assert s.memories(q="firebase") == []
    b = s.add_memory("decisione", "Backend: Supabase + RPC, niente server separato", "piano v2", p["id"])
    s.supersede_memory(a, b)
    assert [m["id"] for m in s.memories(project_id=p["id"])] == [b]
    assert len(s.memories(project_id=p["id"], includi_superate=True)) == 2
    with pytest.raises(ValidazioneError):
        s.supersede_memory(b, b)


def test_handoff_v2_notifica_ripresa_presa_chiusura(s):
    s.upsert_agent("menotti-claude", "menotti", "Claude Code", "claude-code")
    s.upsert_agent("amico1-codex", "amico1", "Codex", "codex")
    p = s.create_project("Siti")
    t = s.create_task("Sito Bellini", project_id=p["id"], stato="running", assigned_agent_id="menotti-claude")
    h = Handoff(agent_name="Claude Code", summary="Sito al 70%", next_step="Rifinire il footer", task_id=t["id"],
                tests_pending="controllo su telefono", dependencies="foto dal cliente", important_notes="non usare font esterni",
                from_agent_id="menotti-claude", to_agent_id="amico1-codex", files_changed=["siti-demo/bellini.html"])
    hid = s.add_handoff(h, user_id="menotti")
    r = s.handoff(hid)
    assert r["stato"] == "aperto" and r["tests_pending"] == "controllo su telefono" and r["to_agent_id"] == "amico1-codex"
    assert s.notifications("amico1", True)[0]["kind"] == "handoff_to_you"
    rip = s.memories(task_id=t["id"], kind="ripresa")[0]
    assert "Rifinire il footer" in rip["content"] and "non usare font esterni" in rip["content"]
    assert rip["source"] == f"handoff #{hid}" and rip["project_id"] == p["id"]
    assert s.events()[0]["event_type"] == "handoff"
    md = Handoff.da_riga(r).markdown()
    for sez in ("Test ancora necessari", "Dipendenze", "Da non perdere", "per: amico1-codex"):
        assert sez in md
    assert s.take_handoff(hid, "amico1-codex", "amico1")["stato"] == "preso"
    with pytest.raises(ValidazioneError, match="già preso"):
        s.take_handoff(hid)
    assert s.close_handoff(hid, "amico1")["stato"] == "chiuso"
    with pytest.raises(ValidazioneError):
        s.add_handoff(Handoff(agent_name="x", summary="s", next_step="n", to_agent_id="nessuno"))


def test_bridge_cli_checkpoint_v2_take_e_memoria(tmp_path):
    db, casa = tmp_path / "hub.db", tmp_path / "casa"
    s = SqliteStore(db)
    seed_users_da_registro(s)
    _, tok_m = s.register_device("menotti", "PC-M")
    _, tok_n = s.register_device("amico1", "PC-N")
    s.bridge_agent_register(tok_m, "menotti-claude", "Claude Code", "claude-code")
    s.bridge_agent_register(tok_n, "amico1-codex", "Codex", "codex")
    t = s.create_task("Preventivo", stato="running")
    env = {**os.environ, "GUARDIAN_HOME": str(casa)}

    def run(tok, *argv):
        return subprocess.run([sys.executable, str(BRIDGE), "--local", str(db), "--token", tok, *argv],
                              capture_output=True, text=True, env=env, timeout=60)

    r = run(tok_m, "checkpoint", "--task", str(t["id"]), "--summary", "bozza pronta", "--next", "inviare per revisione",
            "--tests-pending", "rilettura", "--notes", "prezzi da confermare", "--from-agent", "menotti-claude",
            "--to-agent", "amico1-codex")
    assert r.returncode == 0, r.stderr
    hid = SqliteStore(db).handoffs()[0]["id"]
    assert run(tok_n, "handoff-take", str(hid), "--agent", "menotti-claude").returncode == 2  # agente altrui
    r = run(tok_n, "handoff-take", str(hid), "--agent", "amico1-codex")
    assert r.returncode == 0 and "prezzi da confermare" in r.stdout
    assert run(tok_n, "memory", "add", "Il cliente preferisce WhatsApp", "--tipo", "preferenza", "--fonte", "visita 27/11").returncode == 0
    assert run(tok_n, "memory", "add", "senza fonte").returncode == 2
    r = run(tok_m, "memory", "search", "whatsapp")
    assert "preferisce WhatsApp" in r.stdout and "visita 27/11" in r.stdout


def test_export_md_preserva_il_testo_a_mano(s, tmp_path):
    s.create_task("Aperto | con barra", stato="ready", responsabile="menotti")
    s.update_task(s.create_task("Chiuso")["id"], stato="cancelled")
    f = tmp_path / "TASKS.md"
    f.write_text("# Milestone\n\ntesto scritto a mano\n")
    aggiorna_file(f, sezione_task(s))
    aggiorna_file(f, sezione_task(s))  # idempotente: un solo blocco
    testo = f.read_text()
    assert testo.startswith("# Milestone\n\ntesto scritto a mano") and testo.count(INIZIO) == 1 and testo.count(FINE) == 1
    assert "Aperto / con barra" in testo and "Chiuso" not in testo
