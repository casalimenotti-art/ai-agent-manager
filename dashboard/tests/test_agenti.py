import json, subprocess, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import agenti

HOOK = pathlib.Path(__file__).resolve().parents[1] / "hooks" / "guardian_hook.py"


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + ".000Z"


def asst(t, mid="m1", tool=None, testo=None, out=100, cwd="/p/miaapp", side=False):
    c = []
    if testo: c.append({"type": "text", "text": testo})
    if tool: c.append({"type": "tool_use", "name": tool, "input": {"secret": "x"}})
    return {"type": "assistant", "timestamp": iso(t), "cwd": cwd, "isSidechain": side, "uuid": mid + "u",
            "message": {"id": mid, "model": "claude-sonnet-5-5", "content": c,
                        "usage": {"input_tokens": 10, "output_tokens": out, "cache_read_input_tokens": 1000, "cache_creation_input_tokens": 500}}}


def scrivi(path, righe, newline=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        for r in righe:
            f.write(json.dumps(r) + "\n")


def indice(tmp_path):
    return agenti.Indice(tmp_path / "projects", tmp_path / "events.jsonl")


def test_stato_soglia_due_minuti(tmp_path):
    p = tmp_path / "projects" / "-p-miaapp"
    now = time.time()
    scrivi(p / "s-recente.jsonl", [asst(now - 30, testo="lavoro")])
    scrivi(p / "s-vecchia.jsonl", [asst(now - 300, testo="finito")])
    r = {s["sessione"]: s for s in indice(tmp_path).sessioni(soglia_s=120)}
    assert r["s-recente"]["stato"] == "al lavoro" and r["s-vecchia"]["stato"] == "fermo"
    assert r["s-recente"]["progetto"] == "miaapp"


def test_ultimo_strumento_messaggio_e_dedupe_token(tmp_path):
    p = tmp_path / "projects" / "x" / "s1.jsonl"
    now = time.time()
    # stesso message id ripetuto (succede nei JSONL reali): i token si contano una volta
    scrivi(p, [asst(now - 5, "m1", testo="primo", out=100), asst(now - 4, "m1", tool="Bash", out=100),
               asst(now - 3, "m2", testo="ultimo msg", out=50)])
    s = indice(tmp_path).sessioni()[0]
    assert s["strumento"] == "Bash" and s["messaggio"] == "ultimo msg"
    assert s["token_out"] == 150 and s["token_in"] == 20 and s["costo"] > 0


def test_user_tool_result_non_e_un_messaggio(tmp_path):
    p = tmp_path / "projects" / "x" / "s1.jsonl"
    now = time.time()
    scrivi(p, [{"type": "user", "timestamp": iso(now), "cwd": "/a", "message": {"content": "domanda utente"}},
               {"type": "user", "timestamp": iso(now), "cwd": "/a", "message": {"content": [{"type": "tool_result", "content": "out"}]}}])
    assert indice(tmp_path).sessioni()[0]["messaggio"] == "domanda utente"


def test_subagente_riconosciuto(tmp_path):
    now = time.time()
    scrivi(tmp_path / "projects" / "x" / "s1.jsonl", [asst(now, testo="padre")])
    scrivi(tmp_path / "projects" / "x" / "s1" / "subagents" / "agent-abc1234.jsonl", [asst(now, "ms", tool="Grep", side=True)])
    r = {s["tipo"]: s for s in indice(tmp_path).sessioni()}
    assert r["subagente"]["agente"] == "abc1234" and r["subagente"]["padre"] == "s1" and r["subagente"]["strumento"] == "Grep"


def test_lettura_incrementale_e_riga_parziale(tmp_path):
    p = tmp_path / "projects" / "x" / "s1.jsonl"
    now = time.time()
    scrivi(p, [asst(now, "m1", testo="uno")])
    ix = indice(tmp_path)
    assert ix.sessioni()[0]["messaggio"] == "uno"
    with open(p, "a") as f:  # riga scritta a metà
        f.write(json.dumps(asst(now + 1, "m2", testo="due"))[:40])
    assert ix.sessioni()[0]["messaggio"] == "uno"
    with open(p, "a") as f:
        f.write(json.dumps(asst(now + 1, "m2", testo="due"))[40:] + "\n")
    assert ix.sessioni()[0]["messaggio"] == "due"


def test_righe_corrotte_ignorate(tmp_path):
    p = tmp_path / "projects" / "x" / "s1.jsonl"
    p.parent.mkdir(parents=True)
    p.write_text("non json\n" + json.dumps(asst(time.time(), testo="ok")) + "\n[1,2]\n")
    assert indice(tmp_path).sessioni()[0]["messaggio"] == "ok"


def test_hook_stop_rende_fermo_subito_e_aggiorna_strumento(tmp_path):
    now = time.time()
    scrivi(tmp_path / "projects" / "x" / "s1.jsonl", [asst(now - 10, testo="a", tool="Read")])
    ix = indice(tmp_path)
    assert ix.sessioni()[0]["stato"] == "al lavoro"
    scrivi(tmp_path / "events.jsonl", [{"ts": now - 5, "event": "PreToolUse", "session_id": "s1", "tool": "Edit"}])
    s = ix.sessioni()[0]
    assert s["strumento"] == "Edit" and s["fonte"] == "hook" and s["stato"] == "al lavoro"
    scrivi(tmp_path / "events.jsonl", [{"ts": now - 1, "event": "Stop", "session_id": "s1", "tool": ""}])
    assert ix.sessioni()[0]["stato"] == "fermo"


def test_script_hook_scrive_evento_senza_tool_input(tmp_path):
    ev = tmp_path / "ev.jsonl"
    entrata = {"hook_event_name": "PreToolUse", "session_id": "s9", "cwd": "/a", "tool_name": "Bash",
               "tool_input": {"command": "echo SEGRETO"}}
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(entrata), text=True,
                       env={"GUARDIAN_EVENTS_FILE": str(ev), "PATH": ""}, capture_output=True)
    assert r.returncode == 0 and r.stdout == ""
    riga = json.loads(ev.read_text())
    assert riga["tool"] == "Bash" and riga["session_id"] == "s9" and "SEGRETO" not in ev.read_text()
    # input non valido: esce comunque con 0
    assert subprocess.run([sys.executable, str(HOOK)], input="garbage", text=True, env={"GUARDIAN_EVENTS_FILE": str(ev)}).returncode == 0
