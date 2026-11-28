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
