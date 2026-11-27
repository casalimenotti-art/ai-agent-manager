"""Provider OpenAI-compatibile (POST {base_url}/chat/completions), solo libreria standard."""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request

from .base import COSTI, Provider, ProviderErrore


def estrai_json(testo: str) -> dict:
    """JSON dalla risposta del modello, anche se racchiuso in ``` o con testo attorno (dallo starter app.py)."""
    t = (testo or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        t = t[:-3] if t.endswith("```") else t
    inizio, fine = t.find("{"), t.rfind("}")
    if inizio < 0 or fine <= inizio:
        raise ValueError("nessun oggetto JSON nella risposta")
    d = json.loads(t[inizio:fine + 1])
    if not isinstance(d, dict):
        raise ValueError("la risposta non è un oggetto JSON")
    return d


class OpenAICompatProvider(Provider):
    def __init__(self, nome: str, base_url: str, model: str, api_key: str = "", costo: str = "free",
                 timeout: float = 60, json_mode: bool = True):
        if costo not in COSTI:
            raise ValueError(f"costo non valido per {nome}: {costo}")
        self.nome, self.base_url, self.model, self._key = nome, base_url.rstrip("/"), model, api_key
        self.costo, self.timeout, self.json_mode = costo, timeout, json_mode

    def __repr__(self) -> str:  # mai la chiave
        return f"OpenAICompatProvider({self.nome}, {self.model}, {self.costo})"

    def available(self) -> bool:
        locale = self.base_url.startswith(("http://localhost", "http://127.0.0.1"))
        return bool(self.base_url and self.model) and (locale or self.base_url.startswith("https://")) \
            and (bool(self._key) or self.costo == "local" or locale)

    def complete_json(self, system: str, user: str) -> dict:
        corpo = {"model": self.model, "temperature": 0.2,
                 "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if self.json_mode:
            corpo["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json"}
        if self._key:
            headers["Authorization"] = f"Bearer {self._key}"
        req = urllib.request.Request(f"{self.base_url}/chat/completions", data=json.dumps(corpo).encode(),
                                     headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                dati = json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            raise ProviderErrore(f"HTTP {e.code}", ritentabile=e.code == 429 or e.code >= 500) from None
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            raise ProviderErrore(f"rete: {type(e).__name__}", ritentabile=True) from None
        except ValueError:
            raise ProviderErrore("risposta del server non è JSON", ritentabile=True) from None
        try:
            testo = dati["choices"][0]["message"]["content"]
            return estrai_json(testo)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise ProviderErrore(f"risposta del modello non valida ({e.__class__.__name__})", ritentabile=True) from None
