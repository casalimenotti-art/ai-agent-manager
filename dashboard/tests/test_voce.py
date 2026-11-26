import io, sys, pathlib, types, wave
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import chat, config, voce


def wav(secondi=1.0, rate=16000):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(b"\x00\x00" * int(rate * secondi))
    return b.getvalue()


def test_validazione_audio():
    assert voce.valida_wav(wav(1))[0]
    for cattivo in (b"", b"x" * 100, wav(0.05), wav(130, 8000), b"RIFF" + b"0" * 5000):
        assert not voce.valida_wav(cattivo)[0]
    assert not voce.valida_wav(b"a" * (voce.MAX_BYTES + 1))[0]


def test_trascrizione_con_motore_finto_e_normalizzazione():
    r = voce.trascrivi(wav(1), _motore=lambda d, l: "  trova   dieci clienti \n a Cagliari ")
    assert r == {"ok": True, "testo": "trova dieci clienti a Cagliari", "messaggio": ""}
    assert not voce.trascrivi(wav(1), _motore=lambda d, l: "   ")["ok"]                     # silenzio
    r = voce.trascrivi(wav(1), _motore=lambda d, l: (_ for _ in ()).throw(RuntimeError("boom")))
    assert not r["ok"] and "RuntimeError" in r["messaggio"]                                 # errori non fanno crashare la UI
    assert len(voce.trascrivi(wav(1), _motore=lambda d, l: "a" * 9000)["testo"]) == 4000


def test_senza_pacchetto_messaggio_chiaro(monkeypatch):
    monkeypatch.setattr(voce, "disponibile", lambda: False)
    r = voce.trascrivi(wav(1))
    assert not r["ok"] and "non installato" in r["messaggio"]


def test_installa_pinnato_solo_wheel():
    chiamate = []
    def finto(cmd):
        chiamate.append(cmd); return types.SimpleNamespace(returncode=0, stderr="")
    assert voce.installa(finto)["ok"]
    c = chiamate[0]
    assert "--only-binary=:all:" in c and "faster-whisper==1.2.1" in c and "--break-system-packages" not in c
    assert not voce.installa(lambda cmd: types.SimpleNamespace(returncode=1, stderr="boom"))["ok"]


def test_agente_manager_nel_comando(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CLAUDE_HOME", tmp_path)
    assert "--agent" not in chat.costruisci_comando(None, "guardian-manager")            # non installato: non lo passa
    (tmp_path / "agents").mkdir(); (tmp_path / "agents" / "guardian-manager.md").write_text("x")
    c = chat.costruisci_comando("sid", "guardian-manager")
    assert c[c.index("--agent") + 1] == "guardian-manager" and c[c.index("--resume") + 1] == "sid"
    assert "--agent" not in chat.costruisci_comando(None, "../../x; rm")                 # nome non sicuro: scartato
