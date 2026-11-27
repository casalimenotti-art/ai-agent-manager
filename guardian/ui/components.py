"""Componenti condivisi della UI di Guardian (nessuna logica di dominio)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import streamlit as st

from guardian.core.models import ValidazioneError, eta_secondi

CSS = """<style>
.block-container{padding-top:1.2rem;max-width:1300px}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.25);border-radius:12px;padding:.6rem .8rem}
.g-pill{display:inline-block;padding:.05rem .55rem;border-radius:999px;font-size:.8rem;font-weight:600}
.g-online,.g-idle,.g-ok{background:#1f9d5533;color:#1f9d55}.g-offline,.g-unknown{background:#8884;color:inherit;opacity:.8}
.g-occupato,.g-working{background:#2b7de933;color:#2b7de9}
.g-limite,.g-errore,.g-error,.g-critical{background:#d9480f33;color:#d9480f}
.g-waiting,.g-needs_approval,.g-warning{background:#e6a10033;color:#b07800}
</style>"""

ICONE_STATO = {"in attesa": "⏳", "in corso": "🔄", "bloccato": "⛔", "completato": "✅"}


@dataclass
class Ctx:
    """Contesto passato a ogni pagina: archivio, utente collegato, nomi dei collaboratori."""
    store: object
    io: dict
    nomi: dict = field(default_factory=dict)

    def nome(self, uid) -> str:
        return self.nomi.get(uid, uid or "—")


def segreto(nome: str) -> str:
    try:
        v = st.secrets.get(nome)
        if v:
            return str(v)
    except Exception:
        pass
    return os.environ.get(nome, "")


def fa(ts) -> str:
    sec = eta_secondi(ts)
    if sec is None:
        return "mai"
    if sec < 90:
        return "ora"
    if sec < 3600:
        return f"{int(sec // 60)} min fa"
    if sec < 86400:
        return f"{int(sec // 3600)} h fa"
    return str(ts)[:10]


def pill(stato: str) -> str:
    return f'<span class="g-pill g-{stato}">{stato.replace("_", " ")}</span>'


def esegui(fn, *a, ok: str | None = None, **kw):
    """Esegue un'operazione sull'archivio mostrando errori leggibili, mai dettagli interni o segreti."""
    try:
        r = fn(*a, **kw)
        if ok:
            st.toast(ok)
        return r
    except (ValidazioneError, PermissionError) as e:
        st.error(str(e))
    except Exception as e:  # errori di rete/DB
        st.error(f"Operazione non riuscita ({type(e).__name__}). Riprova o controlla la connessione.")
    return None


def riga_evento(ctx: Ctx, e: dict) -> None:
    chi = " · ".join(x for x in (ctx.nome(e.get("user_id")) if e.get("user_id") else "", e.get("agent_name") or "") if x)
    task = f" · task #{e['task_id']}" if e.get("task_id") else ""
    files = " · " + ", ".join(e["files"][:5]) if e.get("files") else ""
    st.markdown(f"**{e['event_type']}** — {e['message']}  \n"
                f"<small>{fa(e['timestamp'])} · {chi or 'sistema'}{task}{files}</small>", unsafe_allow_html=True)
