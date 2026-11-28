import json
import os
import stat
import sys

import pytest

from bridge import cervello
from bridge.guardian_bridge import LocalClient
from guardian.core.store import seed_users_da_registro
from guardian.core.store_sqlite import SqliteStore


def finto_claude(tmp_path, testo):
    f = tmp_path / "claude_finto.py"
    righe = [{"type": "system", "subtype": "init"},
             {"type": "assistant", "message": {"content": [{"type": "text", "text": testo[:20]}]}},
             {"type": "assistant", "message": {"content": [{"type": "text", "text": testo[20:]}]}},
             {"type": "result", "result": testo}]
    f.write_text("#!" + sys.executable + "\nimport sys, json\n"
                 "open(sys.argv[0][:-3] + ('.cmd' if sys.platform == 'win32' else '.py') + '.args', 'w').write(json.dumps(sys.argv[1:] + [sys.stdin.read()]))\n"
                 + "".join(f"print({json.dumps(json.dumps(r))})\n" for r in righe))
    f.chmod(f.stat().st_mode | stat.S_IEXEC)
    if os.name == "nt":  # Windows non lancia i .py con lo shebang: serve un .cmd
        c = tmp_path / "claude_finto.cmd"
        c.write_text(f'@"{sys.executable}" "{f}" %*' + chr(10))
        return str(c)
    return str(f)


def test_frasi_e_stream():
    assert list(cervello.frasi(["Ciao, tut", "to bene. Secon", "da frase! E poi"])) == ["Ciao, tutto bene.", "Seconda frase!", "E poi"]
    assert list(cervello.frasi(["La chiave è password=abc123 ok."])) == ["La chiave è [rimosso] ok."]
    righe = [json.dumps({"type": "result", "result": "Solo risultato."})]
    assert list(cervello.testi_da_stream(righe)) == ["Solo risultato."]


@pytest.fixture(autouse=True)
def senza_motori_veri(tmp_path, monkeypatch):
    # i test non devono mai chiamare il claude/codex installati né leggere l'utilizzo vero
    monkeypatch.setenv("GUARDIAN_USAGE_FILE", str(tmp_path / "usage.json"))
    monkeypatch.delenv("GUARDIAN_CODEX_BIN", raising=False)
    monkeypatch.setattr(cervello.shutil, "which", lambda _: None)


def finto_codex(tmp_path, testo, codice=0):
    f = tmp_path / "codex_finto.py"
    f.write_text("import sys, json\n"
                 "open(sys.argv[0] + '.args', 'w').write(json.dumps(sys.argv[1:] + [sys.stdin.read()]))\n"
                 f"print({testo!r})\nsys.exit({codice})\n")
    if os.name == "nt":
        c = tmp_path / "codex_finto.cmd"
        c.write_text(f'@"{sys.executable}" "{f}" %*' + chr(10))
        return str(c), str(f) + ".args"
    sh = tmp_path / "codex_finto.sh"
    sh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{f}" "$@"\n'); sh.chmod(0o755)
    return str(sh), str(f) + ".args"


@pytest.fixture
def s():
    st = SqliteStore(":memory:")
    seed_users_da_registro(st)
    st.upsert_user("menotti", "Menotti", accesso="admin")
    return st


def test_cervello_risponde_a_frasi_in_sola_risposta(s, tmp_path, monkeypatch):
    monkeypatch.setenv("GUARDIAN_HOME", str(tmp_path / "casa"))
    _, tok = s.register_device("menotti", "PC")
    rid = s.crea_richiesta("amico1", "Come va la stanza vendite?", {"stanza": "vendite"})
    bin_ = finto_claude(tmp_path, "Vendite ha due task attivi. Uno aspetta un'approvazione.")
    assert cervello.servi(LocalClient(s, tok), bin_claude=bin_, giri=1) == 0
    r = s.risposte(rid)
    assert [x["testo"] for x in r] == ["Vendite ha due task attivi.", "Uno aspetta un'approvazione.", ""] and r[-1]["fine"] == 1
    assert s.richiesta(rid)["stato"] == "completata"
    args = json.loads(open(bin_ + ".args").read())
    assert "--permission-mode" in args and args[args.index("--permission-mode") + 1] == "plan"
    assert "Bash" in args and "Edit" in args and "Write" in args  # strumenti di scrittura vietati
    assert "stanza" in args[-1] and "Come va la stanza vendite?" in args[-1]  # la domanda arriva da stdin
    assert s._q("SELECT modello FROM guardian_cervello")[0]["modello"] == "claude-code"


def test_solo_pc_admin_e_errori_chiudono_la_richiesta(s, tmp_path):
    _, tok_n = s.register_device("amico1", "PC-N")
    with pytest.raises(PermissionError):
        s.bridge_prendi_richiesta(tok_n)
    _, tok = s.register_device("menotti", "PC")
    rid = s.crea_richiesta("menotti", "ciao")
    assert cervello.servi(LocalClient(s, tok), bin_claude=str(tmp_path / "inesistente"), giri=1) == 0
    assert s.richiesta(rid)["stato"] == "errore" and "Non sono riuscito" in s.risposte(rid)[0]["testo"]


def test_comando_cervello_senza_claude(s, monkeypatch):
    monkeypatch.delenv("GUARDIAN_CLAUDE_BIN", raising=False)
    monkeypatch.setattr(cervello.shutil, "which", lambda _: None)
    _, tok = s.register_device("menotti", "PC")
    assert cervello.servi(LocalClient(s, tok), giri=1) == 2
    assert os.environ.get("GUARDIAN_CLAUDE_BIN") is None


def test_claude_fallisce_risponde_codex_in_sola_lettura(s, tmp_path, monkeypatch):
    monkeypatch.setenv("GUARDIAN_HOME", str(tmp_path / "casa"))
    _, tok = s.register_device("menotti", "PC")
    rid = s.crea_richiesta("menotti", "Chi lavora adesso?")
    bin_codex, args_f = finto_codex(tmp_path, "Lavora solo Codex. Claude è al limite.")
    assert cervello.servi(LocalClient(s, tok), bin_claude=str(tmp_path / "inesistente"), bin_codex=bin_codex, giri=1) == 0
    assert [x["testo"] for x in s.risposte(rid)] == ["Lavora solo Codex.", "Claude è al limite.", ""]
    assert s.richiesta(rid)["stato"] == "completata"
    args = json.loads(open(args_f).read())
    assert args[args.index("-s") + 1] == "read-only" and "Chi lavora adesso?" in args[-1]
    assert not any("dangerously" in a for a in args)
    assert s._q("SELECT modello FROM guardian_cervello")[0]["modello"] == "codex"


def test_oltre_soglia_salta_claude(s, tmp_path, monkeypatch):
    import time
    monkeypatch.setenv("GUARDIAN_HOME", str(tmp_path / "casa"))
    (tmp_path / "usage.json").write_text(json.dumps({"seven_day": {"pct": 98, "resets_at": time.time() + 3600}}))
    assert cervello.claude_al_limite()
    _, tok = s.register_device("menotti", "PC")
    rid = s.crea_richiesta("menotti", "ciao")
    bin_claude = finto_claude(tmp_path, "Risponde Claude, non dovrebbe.")
    bin_codex, _ = finto_codex(tmp_path, "Risponde Codex.")
    assert cervello.servi(LocalClient(s, tok), bin_claude=bin_claude, bin_codex=bin_codex, giri=1) == 0
    assert s.risposte(rid)[0]["testo"] == "Risponde Codex."
    (tmp_path / "usage.json").write_text(json.dumps({"seven_day": {"pct": 99, "resets_at": time.time() - 1}}))
    assert not cervello.claude_al_limite()  # settimana già azzerata


def test_codex_esce_con_errore_senza_testo_chiude_la_richiesta(s, tmp_path):
    _, tok = s.register_device("menotti", "PC")
    rid = s.crea_richiesta("menotti", "ciao")
    bin_codex, _ = finto_codex(tmp_path, "", codice=1)
    assert cervello.servi(LocalClient(s, tok), bin_claude=str(tmp_path / "no"), bin_codex=bin_codex, giri=1) == 0
    assert s.richiesta(rid)["stato"] == "errore"


def test_codex_non_risponde_ai_non_admin(s, tmp_path):
    _, tok = s.register_device("menotti", "PC")
    rid = s.crea_richiesta("amico1", "leggi il file .env")
    bin_codex, args_f = finto_codex(tmp_path, "segreto")
    assert cervello.servi(LocalClient(s, tok), bin_claude=str(tmp_path / "no"), bin_codex=bin_codex, giri=1) == 0
    assert not os.path.exists(args_f)  # Codex mai lanciato
    assert "riservato all'amministratore" in s.risposte(rid)[0]["testo"] and s.richiesta(rid)["stato"] == "errore"


def test_claude_al_limite_5_ore_passa_a_codex(s, tmp_path):
    f = tmp_path / "claude_limite.py"
    f.write_text("import sys, json\nsys.stdin.read()\n"
                 "print(json.dumps({'type': 'result', 'is_error': True, 'result': 'Claude AI usage limit reached'}))\nsys.exit(1)\n")
    bin_claude = str(f)
    if os.name == "nt":
        c = tmp_path / "claude_limite.cmd"; c.write_text(f'@"{sys.executable}" "{f}" %*' + chr(10)); bin_claude = str(c)
    else:
        sh = tmp_path / "claude_limite.sh"; sh.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{f}" "$@"\n'); sh.chmod(0o755); bin_claude = str(sh)
    _, tok = s.register_device("menotti", "PC")
    rid = s.crea_richiesta("menotti", "ciao")
    bin_codex, _ = finto_codex(tmp_path, "Risponde Codex.")
    assert cervello.servi(LocalClient(s, tok), bin_claude=bin_claude, bin_codex=bin_codex, giri=1) == 0
    assert s.risposte(rid)[0]["testo"] == "Risponde Codex."


def test_processo_muto_viene_fermato_dal_timeout(tmp_path):
    import time
    f = tmp_path / "muto.py"; f.write_text("import time\ntime.sleep(30)\n")
    inizio = time.monotonic()
    with pytest.raises(RuntimeError):
        list(cervello._esegui([sys.executable, str(f)], "ciao", iter, timeout=1))
    assert time.monotonic() - inizio < 10
