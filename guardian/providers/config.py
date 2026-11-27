"""Provider configurati da variabili d'ambiente o st.secrets (le chiavi non vengono mai mostrate né salvate).

  GUARDIAN_PROVIDERS=freellm,ollama           ordine di preferenza
  GUARDIAN_PROVIDER_FREELLM_URL=https://…/v1  base URL OpenAI-compatibile
  GUARDIAN_PROVIDER_FREELLM_KEY=…             chiave (facoltativa per i provider locali)
  GUARDIAN_PROVIDER_FREELLM_MODEL=…           modello
  GUARDIAN_PROVIDER_FREELLM_COSTO=free        free | local | paid
  GUARDIAN_ALLOW_PAID=0                       1 = consenti i provider a pagamento
"""
from __future__ import annotations

import os
from typing import Callable

from .openai_compat import OpenAICompatProvider


def _lettore_default(nome: str) -> str:
    try:
        import streamlit as st
        v = st.secrets.get(nome)
        if v:
            return str(v)
    except Exception:
        pass
    return os.environ.get(nome, "")


def carica_provider(leggi: Callable[[str], str] = _lettore_default) -> list[OpenAICompatProvider]:
    out = []
    for nome in [n.strip().lower() for n in (leggi("GUARDIAN_PROVIDERS") or "").split(",") if n.strip()]:
        pre = f"GUARDIAN_PROVIDER_{nome.upper()}_"
        url, model = leggi(pre + "URL"), leggi(pre + "MODEL")
        if not (url and model):
            continue
        costo = (leggi(pre + "COSTO") or "free").lower()
        try:
            out.append(OpenAICompatProvider(nome, url, model, leggi(pre + "KEY"), costo))
        except ValueError:
            continue
    return out


def pagamento_consentito(leggi: Callable[[str], str] = _lettore_default) -> bool:
    return (leggi("GUARDIAN_ALLOW_PAID") or "0").strip() in ("1", "true", "si", "sì")
