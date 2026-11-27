"""Router dei provider: ordine di preferenza, esclusione dei provider a pagamento, fallback su errori ritentabili.

Il fallback riguarda solo la singola richiesta al modello: non è un handoff di un task tra agenti.
"""
from __future__ import annotations

import time

from .base import Chiamata, Provider, ProviderErrore, ProviderNonDisponibile


class Router:
    def __init__(self, providers: list[Provider], allow_paid: bool = False, on_call=None):
        self.providers, self.allow_paid, self.on_call = list(providers), allow_paid, on_call
        self.chiamate: list[Chiamata] = []

    def utilizzabili(self) -> list[Provider]:
        return [p for p in self.providers if p.available() and (self.allow_paid or p.costo != "paid")]

    def stato(self) -> list[dict]:
        out = []
        for p in self.providers:
            motivo = ("a pagamento: disattivato (GUARDIAN_ALLOW_PAID=0)" if p.costo == "paid" and not self.allow_paid
                      else "" if p.available() else "configurazione incompleta (URL https, modello o chiave)")
            out.append({"nome": p.nome, "model": p.model, "costo": p.costo, "utilizzabile": not motivo, "motivo": motivo})
        return out

    def _traccia(self, c: Chiamata) -> None:
        self.chiamate.append(c)
        if self.on_call:
            try:
                self.on_call(c)
            except Exception:
                pass  # la traccia non deve mai far fallire la richiesta

    def complete_json(self, system: str, user: str) -> tuple[dict, Provider]:
        candidati = self.utilizzabili()
        if not candidati:
            raise ProviderNonDisponibile("Nessun provider AI configurato e consentito.")
        ultimo = None
        for p in candidati:
            t0 = time.perf_counter()
            try:
                risposta = p.complete_json(system, user)
            except ProviderErrore as e:
                self._traccia(Chiamata(p.nome, p.model, "errore", int((time.perf_counter() - t0) * 1000), str(e)))
                ultimo = e
                if not e.ritentabile:
                    break
                continue
            self._traccia(Chiamata(p.nome, p.model, "ok", int((time.perf_counter() - t0) * 1000)))
            return risposta, p
        raise ProviderErrore(f"Tutti i provider hanno fallito: {ultimo}", ritentabile=False)


def router_da_config(on_call=None) -> Router:
    from .config import carica_provider, pagamento_consentito
    return Router(carica_provider(), pagamento_consentito(), on_call)
