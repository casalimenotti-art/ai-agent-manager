import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from guardian.providers.base import ProviderErrore, ProviderNonDisponibile
from guardian.providers.config import carica_provider, pagamento_consentito
from guardian.providers.openai_compat import OpenAICompatProvider, estrai_json
from guardian.providers.router import Router


class FintoLLM(BaseHTTPRequestHandler):
    risposte: dict = {}
    ricevuti: list = []

    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FintoLLM.ricevuti.append({"path": self.path, "auth": self.headers.get("Authorization"), "body": corpo})
        codice, contenuto = FintoLLM.risposte[self.path.split("/")[1]]
        self.send_response(codice)
        self.end_headers()
        if codice == 200:
            self.wfile.write(json.dumps({"choices": [{"message": {"content": contenuto}}]}).encode())

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    srv = HTTPServer(("127.0.0.1", 0), FintoLLM)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    FintoLLM.ricevuti.clear()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def prov(base, nome, costo="local"):
    return OpenAICompatProvider(nome, f"{base}/{nome}", "m-" + nome, api_key="k-" + nome, costo=costo)


def test_estrai_json():
    assert estrai_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert estrai_json('Ecco: {"a": {"b": 2}} fine') == {"a": {"b": 2}}
    with pytest.raises(ValueError):
        estrai_json("nessun json")


def test_ok_e_richiesta_corretta(server):
    FintoLLM.risposte = {"uno": (200, '{"summary": "ok"}')}
    r = Router([prov(server, "uno")])
    risposta, p = r.complete_json("sistema", "utente")
    assert risposta == {"summary": "ok"} and p.nome == "uno"
    req = FintoLLM.ricevuti[0]
    assert req["path"] == "/uno/chat/completions" and req["auth"] == "Bearer k-uno"
    assert req["body"]["response_format"] == {"type": "json_object"} and req["body"]["model"] == "m-uno"
    assert r.chiamate[0].esito == "ok" and "utente" not in repr(r.chiamate[0])


def test_fallback_su_429_e_json_non_valido(server):
    FintoLLM.risposte = {"a": (429, ""), "b": (200, "non è json"), "c": (200, '{"x": 1}')}
    tracce = []
    r = Router([prov(server, "a"), prov(server, "b"), prov(server, "c")], on_call=tracce.append)
    risposta, p = r.complete_json("s", "u")
    assert p.nome == "c" and [c.esito for c in tracce] == ["errore", "errore", "ok"]


def test_errore_non_ritentabile_si_ferma(server):
    FintoLLM.risposte = {"a": (401, ""), "b": (200, '{"x": 1}')}
    with pytest.raises(ProviderErrore):
        Router([prov(server, "a"), prov(server, "b")]).complete_json("s", "u")


def test_paid_escluso_e_nessun_provider(server):
    FintoLLM.risposte = {"p": (200, '{"x": 1}')}
    r = Router([prov(server, "p", "paid")], allow_paid=False)
    with pytest.raises(ProviderNonDisponibile):
        r.complete_json("s", "u")
    assert "pagamento" in r.stato()[0]["motivo"] and FintoLLM.ricevuti == []
    assert Router([prov(server, "p", "paid")], allow_paid=True).complete_json("s", "u")[0] == {"x": 1}
    with pytest.raises(ProviderNonDisponibile):
        Router([]).complete_json("s", "u")


def test_config_da_env_e_chiave_mai_mostrata():
    env = {"GUARDIAN_PROVIDERS": "freellm, rotto", "GUARDIAN_PROVIDER_FREELLM_URL": "https://gw.example/v1",
           "GUARDIAN_PROVIDER_FREELLM_MODEL": "llama", "GUARDIAN_PROVIDER_FREELLM_KEY": "segreta-123",
           "GUARDIAN_PROVIDER_ROTTO_URL": "https://x"}
    ps = carica_provider(lambda k: env.get(k, ""))
    assert [p.nome for p in ps] == ["freellm"] and ps[0].available() and "segreta" not in repr(ps[0])
    assert not pagamento_consentito(lambda k: env.get(k, ""))
    assert not OpenAICompatProvider("x", "http://esterno.example/v1", "m", "k").available()  # http non locale
    assert carica_provider(lambda k: "") == []
