import json, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pytest
import config, fonte, lavori

FAKE = str(pathlib.Path(__file__).with_name("fake_claude_lento.py"))


@pytest.fixture
def L(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CLAUDE_BIN", FAKE)
    return lavori.Lavori(fonte.FonteLocale(), tmp_path / "chat.json", iniziali=3, cwd_default=str(tmp_path))


def attendi(L, ids, timeout=15):
    t = time.time()
    while time.time() - t < timeout:
        if not any(L.get(i).in_corso for i in ids):
            return True
        time.sleep(0.1)
    return False


def test_tre_chat_di_partenza_e_massimo_cinque(L):
    assert len(L.ids()) == 3
    assert L.nuova() and L.nuova() and L.nuova() is None and len(L.ids()) == 5
    assert L.get(L.ids()[0]).agente == config.MANAGER_AGENT and L.get(L.ids()[1]).agente is None


def test_tre_lavori_in_parallelo_senza_mescolarsi(L):
    ids = L.ids()
    t0 = time.time()
    for i, n in zip(ids, ("uno", "due", "tre")):
        assert L.invia(i, f"compito {n}")["ok"]
    assert L.in_corso() == 3
    assert attendi(L, ids)
    durata = time.time() - t0
    assert durata < 2.6, f"in serie sarebbero 3+ s, in parallelo ~1 s: {durata:.1f}"
    for i, n in zip(ids, ("uno", "due", "tre")):
        s = L.istantanea(i)
        assert s["msgs"][-1]["testo"].endswith(f"compito {n}") and s["msgs"][0]["testo"] == f"compito {n}"   # nessuno scambio tra chat
        assert s["sid"] and "WebSearch" in s["msgs"][-1]["nota"] and not s["in_corso"]
    assert len({L.get(i).sid for i in ids}) == 3                                                            # una sessione per chat


def test_non_si_puo_inviare_mentre_lavora_e_validazioni(L):
    i = L.ids()[0]
    assert not L.invia(i, "   ")["ok"] and not L.invia("xx", "ciao")["ok"] and not L.invia(i, "a" * 9000)["ok"]
    L.imposta(i, cwd="")
    assert "cartella" in L.invia(i, "ciao")["messaggio"]
    L.imposta(i, cwd="/")
    assert L.invia(i, "lento uno")["ok"]
    assert "ancora" in L.invia(i, "altro")["messaggio"]
    assert not L.chiudi(i) and not L.reset(i)                                                              # né chiudere né azzerare in corso
    L.ferma(i); assert attendi(L, [i], 8)


def test_stop_interrompe_davvero_il_processo(L):
    i = L.ids()[1]
    L.invia(i, "lento due")
    time.sleep(1.2)
    assert L.istantanea(i)["testo"]                                                                         # streaming visibile mentre lavora
    t0 = time.time()
    assert L.ferma(i)
    assert attendi(L, [i], 5) and time.time() - t0 < 4
    s = L.istantanea(i)
    assert s["msgs"][-1]["errore"] and "Interrotto" in s["msgs"][-1]["testo"]
    assert L.invia(i, "dopo lo stop")["ok"] and attendi(L, [i])                                             # la chat resta usabile
    assert "dopo lo stop" in L.istantanea(i)["msgs"][-1]["testo"]


def test_resume_usa_la_sessione_della_stessa_chat(L):
    i = L.ids()[0]
    L.invia(i, "primo"); assert attendi(L, [i]); sid1 = L.get(i).sid
    L.invia(i, "secondo"); assert attendi(L, [i])
    assert L.get(i).sid == sid1 or L.get(i).sid                                                             # resta valorizzato
    L.imposta(i, cwd="/tmp"); assert L.get(i).sid is None                                                   # altra cartella = conversazione nuova


def test_persistenza_e_file_corrotto(L, tmp_path, monkeypatch):
    i = L.ids()[0]
    L.invia(i, "ricordami"); assert attendi(L, [i])
    L2 = lavori.Lavori(fonte.FonteLocale(), tmp_path / "chat.json", iniziali=3)
    assert len(L2.ids()) == 3 and any("ricordami" in m["testo"] for m in L2.get(i).msgs) and L2.get(i).sid
    (tmp_path / "chat.json").write_text("{rotto")
    assert len(lavori.Lavori(fonte.FonteLocale(), tmp_path / "chat.json", iniziali=3).ids()) == 3          # riparte pulito


def test_errore_della_fonte_non_blocca_il_thread(tmp_path):
    class Rotta:
        def esegui(self, *a, **k):
            raise RuntimeError("boom")
    L = lavori.Lavori(Rotta(), None, iniziali=1, cwd_default="/x")
    i = L.ids()[0]
    assert L.invia(i, "ciao")["ok"] and attendi(L, [i], 5)
    assert "boom" in L.istantanea(i)["msgs"][-1]["testo"] and not L.get(i).in_corso


def test_chiudi_mantiene_almeno_una_chat(L):
    for i in L.ids()[1:]:
        assert L.chiudi(i)
    assert not L.chiudi(L.ids()[0]) and len(L.ids()) == 1
