"""Componente Streamlit «microfono a mani libere»: registra, rileva le pause e consegna a Python un WAV a 16 kHz per frase."""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit.components.v1 as components

_componente = components.declare_component("mic_continuo", path=str(Path(__file__).resolve().parent / "componenti" / "mic_continuo"))


def mic_continuo(key: str = "mic_cont") -> dict | None:
    """Ultimo enunciato: {"id", "wav" (base64), "ms"} oppure None. Ogni frase nuova ha un `id` diverso."""
    v = _componente(key=key, default=None)
    return v if isinstance(v, dict) and v.get("wav") and v.get("id") else None


def decodifica(v: dict, max_byte: int = 12 * 1024 * 1024) -> bytes:
    """WAV dal valore del componente, con tetto di dimensione (il componente arriva dal browser: non fidarsi)."""
    s = v.get("wav", "")
    if not isinstance(s, str) or len(s) > max_byte * 4 // 3 + 8:
        return b""
    try:
        return base64.b64decode(s, validate=True)
    except Exception:
        return b""
