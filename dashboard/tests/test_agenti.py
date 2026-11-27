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


def test_costi_per_giorno_progetto_modello_e_output(tmp_path):
    now = time.time()
    p = tmp_path / "projects" / "x" / "s1.jsonl"
    scrivi(p, [asst(now - 10, "m1", tool="Edit", out=1000), asst(now - 9, "m2", tool="Bash", out=500, cwd="/p/miaapp")])
    ix = indice(tmp_path)
    k = ix.costi(7)
    oggi = k["giorni"][-1]
    assert len(k["giorni"]) == 7 and oggi["msgs"] == 2 and oggi["tools"] == 2 and oggi["edits"] == 1
    assert oggi["token_out"] == 1500 and k["oggi"] > 0 and k["ultimi7"] == k["oggi"]
    assert k["progetti"][0]["progetto"] == "miaapp" and k["modelli"][0]["modello"] == "claude-sonnet-5-5"
    assert k["proiezione_mese"] >= k["mese"]
    ix.costi(7)  # seconda lettura: nessun doppio conteggio
    assert ix.costi(7)["giorni"][-1]["msgs"] == 2


def test_costi_ignora_giorni_fuori_finestra(tmp_path):
    scrivi(tmp_path / "projects" / "x" / "s1.jsonl", [asst(time.time() - 40 * 86400, "m1", testo="vecchio")])
    assert indice(tmp_path).costi(30)["ultimi30"] == 0


import pytest
@pytest.mark.parametrize("modello,inp,out,cr,cw,atteso", [
    ("claude-sonnet-5-5", 1_000_000, 0, 0, 0, 2.0),
    ("claude-sonnet-5-5", 0, 1_000_000, 0, 0, 10.0),
    ("claude-sonnet-5-5", 0, 0, 1_000_000, 0, 0.10),   # cache read 0.05x
    ("claude-opus-5-5", 0, 0, 0, 1_000_000, 5.0),       # cache write 1.25x
    ("claude-opus-5-5", 0, 1_000_000, 0, 0, 20.0),
    ("claude-opus-4-1-20250805", 1_000_000, 0, 0, 0, 15.0),
    ("claude-opus-4-6", 1_000_000, 0, 0, 0, 5.0),
    ("claude-haiku-4-5-20251001", 0, 1_000_000, 0, 0, 5.0),
    ("claude-haiku-5-5", 50_000, 0, 0, 0, 0.005),
    ("claude-haiku-5-5", 200_000, 0, 0, 0, 0.10),       # prompt > 100k: tariffa lunga
    ("claude-fable-5-2", 0, 0, 1_000_000, 0, 0.20),
    ("modello-sconosciuto", 1_000_000, 0, 0, 0, 2.0),
])
def test_prezzi_ufficiali(modello, inp, out, cr, cw, atteso):
    assert agenti.costo(modello, inp, out, cr, cw) == pytest.approx(atteso)


def test_burn_rate_ultime_5_ore(tmp_path):
    now = time.time()
    scrivi(tmp_path / "projects" / "x" / "s1.jsonl", [asst(now - 5, "m1", out=1_000_000), asst(now - 6 * 3600, "m2", out=1_000_000)])
    k = indice(tmp_path).costi(7)
    un_msg = agenti.costo("claude-sonnet-5-5", 10, 1_000_000, 1000, 500)
    assert k["ultime_5h"] == pytest.approx(un_msg, abs=1e-3)       # il messaggio di 6 ore fa è escluso
    assert k["burn_orario"] == pytest.approx(un_msg / 5, abs=1e-3)


def _tool_use(t, tid, nome, inp, mid="mu"):
    return {"type": "assistant", "timestamp": iso(t), "cwd": "/p/app", "uuid": mid + tid,
            "message": {"id": mid + tid, "model": "claude-sonnet-5-5",
                        "content": [{"type": "tool_use", "id": tid, "name": nome, "input": inp}], "usage": {}}}


def _tool_result(t, tid, testo):
    return {"type": "user", "timestamp": iso(t), "cwd": "/p/app",
            "message": {"content": [{"type": "tool_result", "tool_use_id": tid, "content": testo}]}}


def test_attivita_delega_web_e_risultati_mascherati(tmp_path):
    now = time.time()
    scrivi(tmp_path / "projects" / "x" / "s1.jsonl", [
        _tool_use(now - 50, "t1", "Agent", {"subagent_type": "cacciatore-clienti", "description": "Cerca ristoranti", "prompt": "Trova 10 ristoranti a Cagliari"}),
        _tool_use(now - 40, "t2", "WebSearch", {"query": "ristoranti Cagliari senza sito"}),
        _tool_result(now - 39, "t2", "Risultati: A, B, C"),
        _tool_use(now - 30, "t3", "WebFetch", {"url": "https://example.com/a", "prompt": "c'è un sito?"}),
        _tool_result(now - 29, "t3", [{"type": "text", "text": "La pagina non esiste"}]),
        _tool_use(now - 20, "t4", "Bash", {"command": "curl -H 'Authorization: Bearer abcdefghijklmnop12345' x && export API_KEY=supersegreto"}),
        _tool_use(now - 10, "t5", "Write", {"file_path": "leads/2026-11-26-bar.csv", "content": "NON DEVE COMPARIRE"}),
        asst(now - 5, "m9", testo="Ho finito la ricerca"),
    ])
    ev = indice(tmp_path).attivita(limite=50)
    tipi = [e["tipo"] for e in ev]
    assert tipi[:2] == ["dice", "file"] and set(tipi) >= {"delega", "web-ricerca", "web-apri", "comando", "file"}   # più recenti prima
    per = {e["tipo"]: e for e in ev}
    assert per["delega"]["testo"].startswith("cacciatore-clienti") and "10 ristoranti" in per["delega"]["brief"]
    assert per["web-apri"]["url"] == "https://example.com/a" and per["web-apri"]["risultato"] == "La pagina non esiste"
    assert per["web-ricerca"]["risultato"] == "Risultati: A, B, C"
    tutto = json.dumps(ev)
    assert "abcdefghijklmnop12345" not in tutto and "supersegreto" not in tutto and "NON DEVE COMPARIRE" not in tutto
    assert per["file"]["testo"] == "leads/2026-11-26-bar.csv"


def test_attivita_filtri_e_limite(tmp_path):
    now = time.time()
    scrivi(tmp_path / "projects" / "x" / "s1.jsonl", [_tool_use(now - i, f"t{i}", "WebSearch", {"query": f"q{i}"}) for i in range(1, 8)])
    ix = indice(tmp_path)
    assert len(ix.attivita(limite=3)) == 3 and ix.attivita(limite=3)[0]["testo"] == "q1"
    assert ix.attivita(tipi={"delega"}) == []


def test_subagente_meta_nome_compito_e_finito(tmp_path):
    now = time.time()
    scrivi(tmp_path / "projects" / "x" / "s1.jsonl", [asst(now, testo="padre")])
    sub = tmp_path / "projects" / "x" / "s1" / "subagents" / "agent-abc1234.jsonl"
    scrivi(sub, [asst(now, "ms", tool="WebSearch", side=True)])
    meta = sub.with_name("agent-abc1234.meta.json")
    meta.write_text(json.dumps({"agentType": "cacciatore-clienti", "description": "Ristoranti Cagliari", "finished": False}))
    ix = indice(tmp_path)
    r = {s["tipo"]: s for s in ix.sessioni()}["subagente"]
    assert r["stato"] == "al lavoro" and r["nome_agente"] == "cacciatore-clienti" and r["compito"] == "Ristoranti Cagliari"
    meta.write_text(json.dumps({"agentType": "cacciatore-clienti", "description": "Ristoranti Cagliari", "finished": True}))
    r = {s["tipo"]: s for s in ix.sessioni()}["subagente"]
    assert r["stato"] == "finito"
    chi = {e["chi"] for e in ix.attivita()}
    assert "Cacciatore di clienti · Ristoranti Cagliari" in chi


def test_promemoria_interni_nascosti():
    t = agenti.maschera("prima <system-reminder>non mostrare</system-reminder> dopo <system-reminder>aperto senza fine")
    assert "non mostrare" not in t and "aperto" not in t and t.startswith("prima") and "dopo" in t


def test_nessun_link_apre_altre_schede():
    import theme
    righe = [{"ts": time.time(), "tipo": "web-apri", "url": "https://esempio.it/pagina", "testo": "cosa c'è",
              "chi": "cacciatore-clienti · test", "brief": "", "risultato": "ok", "strumento": "WebFetch", "sidechain": True}]
    html = theme.feed_attivita(righe, lambda t: "ora", time.time())
    assert "_blank" not in html and "esempio.it" in html
    cl = theme.tabella_clienti([{"adattamento": 4, "azienda": "A", "categoria": "c", "zona": "z", "stato": "da visitare",
                                 "fonte": "https://esempio.it/x", "prova": "p"}])
    assert "_blank" in cl and "noopener" in cl and ">esempio.it</a>" in cl


def test_dominio():
    import plancia
    assert plancia.dominio("https://www.italia.it/it/sardegna/x?a=1") == "italia.it"
    assert plancia.dominio("http://Bar.Sole.it:8080/a") == "bar.sole.it"
    assert plancia.dominio("javascript:alert(1)") == "" and plancia.dominio("") == ""


def test_nomi_di_ruolo_leggibili():
    import plancia
    assert plancia.nome_ruolo("general-purpose", "Siti B&B gruppo A") == "Web designer"
    assert plancia.nome_ruolo("general-purpose", "Plancia unica dashboard Guardian") == "Sviluppatore della dashboard"
    assert plancia.nome_ruolo("verificatore-fonti", "qualsiasi") == "Verificatore delle fonti"
    assert plancia.nome_ruolo("claude-code-guide", "") == "Esperto di Claude Code"
    assert plancia.nome_ruolo("general-purpose", "") == "Assistente"
