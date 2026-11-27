import io
import json
import threading
import urllib.error
import urllib.request
import wave

import pytest

from bridge import voce_locale

ORIGINE = "http://localhost:4173"


def wav(campioni=1600, sr=16000):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(b"\x00\x10" * campioni)
    return b.getvalue()


@pytest.fixture
def server():
    visti = []
    srv = voce_locale.crea_server(lambda c, sr: visti.append((len(c), sr)) or "ciao guardian", "finto", porta=0, origini={ORIGINE})
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", visti
    srv.shutdown()


def chiama(url, metodo="GET", dati=None, origine=ORIGINE, extra=None):
    h = {"Origin": origine, **(extra or {})}
    if dati is not None:
        h["Content-Type"] = "audio/wav"
    req = urllib.request.Request(url, data=dati, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, dict(r.headers), (json.loads(r.read() or b"{}") if metodo != "OPTIONS" else {})
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), {}


def test_stato_trascrizione_e_cors(server):
    url, visti = server
    st, h, d = chiama(url + "/stato")
    assert st == 200 and d["pronto"] and d["privato"] and h["Access-Control-Allow-Origin"] == ORIGINE
    st, _, d = chiama(url + "/trascrivi", "POST", wav())
    assert st == 200 and d["testo"] == "ciao guardian" and visti == [(1600, 16000)]


def test_origini_estranee_rifiutate(server):
    url, visti = server
    assert chiama(url + "/stato", origine="https://sito-cattivo.example")[0] == 403
    assert chiama(url + "/trascrivi", "POST", wav(), origine="https://sito-cattivo.example")[0] == 403
    assert chiama(url + "/stato", origine="")[0] == 403
    assert visti == []


def test_preflight_private_network(server):
    url, _ = server
    st, h, _ = chiama(url + "/trascrivi", "OPTIONS", extra={"Access-Control-Request-Private-Network": "true",
                                                              "Access-Control-Request-Method": "POST"})
    assert st == 204 and h.get("Access-Control-Allow-Private-Network") == "true"


def test_audio_non_valido_e_motore_assente():
    srv = voce_locale.crea_server(None, "sherpa-onnx non installato", porta=0, origini={ORIGINE})
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}"
    try:
        st, _, d = chiama(url + "/stato")
        assert st == 200 and d["pronto"] is False and "non installato" in d["motore"]
        assert chiama(url + "/trascrivi", "POST", wav())[0] == 503
    finally:
        srv.shutdown()
    with pytest.raises(ValueError):
        b = io.BytesIO()
        with wave.open(b, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(16000); w.writeframes(b"\x00" * 400)
        voce_locale.leggi_wav(b.getvalue())


def test_solo_loopback():
    srv = voce_locale.crea_server(None, "x", porta=0, origini={ORIGINE})
    try:
        assert srv.server_address[0] == "127.0.0.1"
    finally:
        srv.server_close()
