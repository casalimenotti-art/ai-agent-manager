from __future__ import annotations

from dataclasses import dataclass

COSTI = ("free", "local", "paid")


class ProviderNonDisponibile(RuntimeError):
    """Nessun provider configurato o utilizzabile con le regole attuali (es. solo provider a pagamento)."""


class ProviderErrore(RuntimeError):
    def __init__(self, messaggio: str, ritentabile: bool = False):
        super().__init__(messaggio)
        self.ritentabile = ritentabile


@dataclass
class Chiamata:
    """Traccia di una chiamata: mai prompt né risposta."""
    provider: str
    model: str
    esito: str  # ok | errore | saltato
    ms: int
    dettaglio: str = ""


class Provider:
    nome: str
    model: str
    costo: str

    def available(self) -> bool:
        raise NotImplementedError

    def complete_json(self, system: str, user: str) -> dict:
        """Restituisce un oggetto JSON (dict) prodotto dal modello. Solleva ProviderErrore."""
        raise NotImplementedError
