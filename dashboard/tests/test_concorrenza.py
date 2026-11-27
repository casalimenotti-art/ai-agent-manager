import sys, pathlib, threading, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import chat, storico, voce, monitor


def _insieme(fn, n=8):
    errori = []

    def w(i):
        try:
            fn(i)
        except Exception as e:  # noqa
            errori.append(e)
    ts = [threading.Thread(target=w, args=(i,)) for i in range(n)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errori, errori


def test_storico_righe_intere(tmp_path):
    _insieme(lambda i: [storico.aggiungi({"ruolo": "user", "testo": f"{i}-" + "x" * 15000}, tmp_path) for _ in range(5)])
    righe = [m for f in tmp_path.glob("*.jsonl") for m in storico._leggi(f)]
    assert len(righe) == 40
    assert len(list(tmp_path.glob("*.jsonl"))[0].read_text(encoding="utf-8").splitlines()) == 40


def test_doppio_clic_un_solo_lancio():
    chat.LANCI.clear()
    avvii = []

    def esegui(p, c, s, a):
        avvii.append(1)
        time.sleep(0.3)
        return iter(())
    lancio = {"prompt": "compito", "cwd": "/x"}
    _insieme(lambda i: chat.lancia_in_background(esegui, lancio, "ag"))
    time.sleep(0.6)
    assert len(chat.LANCI) == 1 and len(avvii) == 1


def test_voce_carica_una_volta(monkeypatch):
    voce._sherpa.clear()
    chiamate = []
    import types
    fake = types.SimpleNamespace(OfflineRecognizer=types.SimpleNamespace(
        from_transducer=lambda **k: (time.sleep(0.1), chiamate.append(1), object())[2]))
    monkeypatch.setitem(sys.modules, "sherpa_onnx", fake)
    _insieme(lambda i: voce._riconoscitore_sherpa())
    assert len(chiamate) == 1
    voce._sherpa.clear()


def test_monitor_processi_parallelo():
    c = monitor.Campionatore()
    _insieme(lambda i: (c.processi(), c.cpu_totale()))
