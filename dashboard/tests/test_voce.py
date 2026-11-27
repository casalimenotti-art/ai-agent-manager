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


# ---------------------------------------------------------------- sherpa + comandi vocali
import plancia


def test_normalizzazione_e_comandi():
    assert plancia.normalizza_voce("  Guardián,  Riassunto   AGENTI! ") == "guardian riassunto agenti"
    rc = plancia.riconosci_comando
    assert rc("Guardian, riassunto agenti.") == {"tipo": "riassunto", "valore": None}
    assert rc("gardian riassunto agenti")["tipo"] == "riassunto"           # variante di Guardian
    assert rc("Guardiano, apri clienti") == {"tipo": "apri", "valore": "clienti"}
    assert rc("apri scoperte")["valore"] == "scoperte" and rc("apri  Skill")["valore"] == "skill"
    assert rc("Nuova conversazione")["tipo"] == "nuova"
    assert rc("voce on")["valore"] is True and rc("Guardian voce off")["valore"] is False
    assert rc("riassunto agent")["tipo"] == "riassunto"                    # piccolo errore del riconoscitore
    assert rc("trova dieci clienti a Cagliari") is None and rc("") is None and rc(None) is None
    assert rc("apri la cartella dei clienti e leggi tutto il contenuto") is None


def wav_formato(rate, ch, n=4000, sw=2):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(ch); w.setsampwidth(sw); w.setframerate(rate)
        w.writeframes(b"\x00\x10" * (n * ch))
    return b.getvalue()


def test_wav_a_mono16k():
    x, sr = voce.wav_a_mono16k(wav_formato(48000, 2, 4800))
    assert sr == 16000 and x.dtype.name == "float32" and x.ndim == 1 and abs(len(x) - 1600) <= 1
    assert abs(float(x[0]) - 4096 / 32768) < 1e-4
    x, _ = voce.wav_a_mono16k(wav_formato(16000, 1, 800))
    assert len(x) == 800


def test_motore_sherpa_finto(monkeypatch):
    class Flusso:
        result = types.SimpleNamespace(text="  riassunto   agenti ")
        def accept_waveform(self, sr, c): self.sr = sr
    class Rec:
        def create_stream(self): return Flusso()
        def decode_stream(self, f): pass
    r = voce.trascrivi_sherpa(wav(1), _riconoscitore=Rec())
    assert r == {"ok": True, "testo": "riassunto agenti", "messaggio": ""}
    assert not voce.trascrivi_sherpa(b"x")["ok"]
    monkeypatch.setattr(voce, "sherpa_pacchetto", lambda: True)
    monkeypatch.setattr(voce, "sherpa_modello", lambda: True)
    assert voce.motore_riconoscimento()["motore"] == "sherpa"
    monkeypatch.setattr(voce, "sherpa_modello", lambda: False)
    monkeypatch.setattr(voce, "disponibile", lambda: False)
    m = voce.motore_riconoscimento(_riconoscitori=[])
    assert m["motore"] is None and "manca il modello" in m["mancante"]
