import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import chat, config

FAKE = str(pathlib.Path(__file__).with_name("fake_claude.py"))


def _run(prompt, resume=None, cwd="."):
    config.CLAUDE_BIN = FAKE
    r = chat.Risposta()
    for ev in chat.esegui_locale(prompt, cwd, resume):
        r.aggiungi(ev)
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
