import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import chat, config

FAKE = str(pathlib.Path(__file__).with_name("fake_claude.py"))


def _run(prompt, resume=None, cwd="."):
    # Portabile: il finto claude e' un .py lanciato con l'interprete (niente shebang su Windows).
    orig = chat.costruisci_comando
    chat.costruisci_comando = lambda *a, **k: [sys.executable, FAKE] + orig(*a, **k)[1:]
    try:
        r = chat.Risposta()
        for ev in chat.esegui_locale(prompt, cwd, resume):
            r.aggiungi(ev)
    finally:
        chat.costruisci_comando = orig
    return r


def test_streaming_e_session_id():
    r = _run("domanda")
    assert r.testo.startswith("Ciao da fake: domanda")
    assert r.session_id == "sess-nuova" and r.strumenti == ["Read"] and r.costo == 0.01 and not r.errore


def test_resume_passa_il_session_id():
    assert _run("x", resume="abc").session_id == "abc"


def test_prompt_che_inizia_con_trattino():
    assert "-rf" in _run("-rf").testo


def test_cartella_inesistente():
    assert "inesistente" in _run("x", cwd="/non/esiste").errore


def test_comando_mancante():
    config.CLAUDE_BIN = "/non/esiste/claude"
    r = chat.Risposta()
    for ev in chat.esegui_locale("x", "."):
        r.aggiungi(ev)
    assert "non trovato" in r.errore


# ---- Lancia un agente (funzioni pure, nessun agente viene davvero lanciato)
def test_prepara_lancio_argv_senza_compito(tmp_path, monkeypatch):
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "web-designer.md").write_text("x")
    monkeypatch.setattr(chat.config, "CLAUDE_HOME", tmp_path)
    t = 'a"; rm -rf / & $(evil)\x00'
    l = chat.prepara_lancio("web-designer", t, str(tmp_path))
    assert l["ok"] and l["argv"][l["argv"].index("--agent") + 1] == "web-designer"
    assert all("rm -rf" not in a for a in l["argv"])        # il compito non è mai un argomento/shell
    assert "\x00" not in l["prompt"] and "rm -rf" in l["prompt"]
    assert chat.config.CHAT_PERMISSION_MODE in l["argv"]
    assert "bypassPermissions" not in l["argv"]
    assert chat.agenti_installati() == ["web-designer"]


def test_prepara_lancio_rifiuta(tmp_path, monkeypatch):
    monkeypatch.setattr(chat.config, "CLAUDE_HOME", tmp_path)
    assert not chat.prepara_lancio("non-esiste", "x", str(tmp_path))["ok"]
    assert not chat.prepara_lancio("../../x", "x", str(tmp_path), installati=["../../x"])["ok"]
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "a.md").write_text("x")
    assert not chat.prepara_lancio("a", "   ", str(tmp_path))["ok"]
    assert not chat.prepara_lancio("a", "x", str(tmp_path / "nulla"))["ok"]
    monkeypatch.setattr(chat.config, "CHAT_PERMISSION_MODE", "bypassPermissions")
    assert not chat.prepara_lancio("a", "x", str(tmp_path))["ok"]


def test_lancia_in_background_usa_esegui_finto():
    import time
    visti = []

    def finto(prompt, cwd, resume, agente):
        visti.append((prompt, agente))
        yield {"type": "guardian_end", "returncode": 0, "stderr": ""}
    reg = chat.lancia_in_background(finto, {"prompt": "p", "cwd": "."}, "a")
    for _ in range(50):
        if reg["stato"] != "in corso":
            break
        time.sleep(0.02)
    assert reg["stato"] == "finito" and visti == [("p", "a")]
