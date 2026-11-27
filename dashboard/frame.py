"""Adattatore per incorporare HTML: `components.html` è in dismissione, `st.iframe` è il sostituto.

Si usa `components.html` finché esiste (comportamento testato) e `st.iframe` quando verrà rimosso. Entrambi eseguono JavaScript con accesso
same-origin: passare SOLO HTML scritto da noi (testi di modelli o di pagine web vanno sempre serializzati e neutralizzati, vedi voce_out.js_parla).
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as _c


def html_frame(html: str, height: int = 0, scrolling: bool = False):
    if hasattr(_c, "html"):
        return _c.html(html, height=height, scrolling=scrolling)
    return st.iframe(html, height=max(1, height))
