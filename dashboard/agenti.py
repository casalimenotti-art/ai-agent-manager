"""Monitor agenti: legge i JSONL di ~/.claude/projects (+ eventi hook opzionali)."""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import config


def parse_ts(s: str | None) -> float:
    if not s:
        return 0.0
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def prezzo_modello(modello: str) -> tuple[float, float]:
    m = (modello or "").lower()
    for chiave, prezzo in config.PRICES.items():
        if chiave in m:
            return prezzo
    return config.DEFAULT_PRICE


def costo(modello: str, inp: int, out: int, cache_read: int, cache_write: int) -> float:
    p_in, p_out = prezzo_modello(modello)
    return (inp * p_in + out * p_out + cache_read * p_in * 0.1 + cache_write * p_in * 1.25) / 1e6


def _testo(content) -> str:
    """Testo leggibile da un campo content (stringa o lista di blocchi)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text").strip()
    return ""


class _Stato:
    """Riepilogo incrementale di un file JSONL."""

    def __init__(self, path: Path):
        self.path = path
        self.offset = 0
        self.session_id = path.stem
        self.cwd = ""
        self.sidechain = "subagents" in path.parts
        self.agent_id = path.stem.removeprefix("agent-") if self.sidechain else ""
        self.parent_session = path.parent.parent.name if self.sidechain else ""
        self.ultimo_ts = 0.0
        self.ultimo_strumento = ""
        self.ultimo_assistente = ""
        self.ultimo_utente = ""
        self.token_in = self.token_out = self.cache_r = self.cache_w = 0
        self.costo = 0.0
        self.modello = ""
        self._visti: set[str] = set()  # id messaggi già contati (il JSONL ripete gli usage)

    def feed(self, riga: dict):
        ts = parse_ts(riga.get("timestamp"))
        if ts:
            self.ultimo_ts = max(self.ultimo_ts, ts)
        self.cwd = riga.get("cwd") or self.cwd
        if riga.get("isSidechain"):
            self.sidechain = True
        tipo = riga.get("type")
        msg = riga.get("message")
        if not isinstance(msg, dict):
            return
        content = msg.get("content")
        if tipo == "assistant":
            testo = _testo(content)
            if testo:
                self.ultimo_assistente = testo
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        self.ultimo_strumento = b.get("name", "")
            usage = msg.get("usage") or {}
            mid = msg.get("id") or riga.get("uuid") or ""
            if usage and mid not in self._visti:
                self._visti.add(mid)
                i, o = usage.get("input_tokens", 0) or 0, usage.get("output_tokens", 0) or 0
                cr, cw = usage.get("cache_read_input_tokens", 0) or 0, usage.get("cache_creation_input_tokens", 0) or 0
                self.token_in += i
                self.token_out += o
                self.cache_r += cr
                self.cache_w += cw
                self.modello = msg.get("model") or self.modello
                self.costo += costo(self.modello, i, o, cr, cw)
        elif tipo == "user":
            testo = _testo(content)  # i tool_result non hanno testo: vengono ignorati
            if testo:
                self.ultimo_utente = testo

    def aggiorna(self):
        try:
            size = self.path.stat().st_size
            if size < self.offset:  # file riscritto
                self.__init__(self.path)
            with open(self.path, "rb") as f:
                f.seek(self.offset)
                dati = f.read()
        except OSError:
            return
        fine = dati.rfind(b"\n")
        if fine < 0:
            return  # riga ancora incompleta
        self.offset += fine + 1
        for r in dati[: fine + 1].splitlines():
            try:
                riga = json.loads(r)
            except ValueError:
                continue
            if isinstance(riga, dict):
                self.feed(riga)


class Indice:
    """Indice incrementale dei JSONL: ad ogni chiamata legge solo i byte nuovi."""

    def __init__(self, projects_dir: Path = None, events_file: Path = None):
        self.projects_dir = projects_dir or config.PROJECTS_DIR
        self.events_file = events_file or config.EVENTS_FILE
        self._stati: dict[Path, _Stato] = {}

    def _files(self):
        if not self.projects_dir.is_dir():
            return
        yield from self.projects_dir.glob("*/*.jsonl")
        yield from self.projects_dir.glob("*/*/subagents/*.jsonl")

    def eventi_hook(self, max_righe: int = 2000) -> dict[str, dict]:
        """Ultimo evento hook per session_id."""
        out: dict[str, dict] = {}
        try:
            with open(self.events_file, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - 400_000))
                righe = f.read().splitlines()[-max_righe:]
        except OSError:
            return out
        for r in righe:
            try:
                e = json.loads(r)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get("session_id"):
                out[e["session_id"]] = e
        return out

    def sessioni(self, soglia_s: float | None = None, eta_max_h: float | None = None) -> list[dict]:
        soglia = config.IDLE_THRESHOLD_S if soglia_s is None else soglia_s
        eta = (config.AGENT_MAX_AGE_H if eta_max_h is None else eta_max_h) * 3600
        ora = time.time()
        hook = self.eventi_hook()
        risultato = []
        for p in self._files():
            try:
                if ora - p.stat().st_mtime > eta:
                    self._stati.pop(p, None)
                    continue
            except OSError:
                continue
            st = self._stati.get(p) or self._stati.setdefault(p, _Stato(p))
            st.aggiorna()
            if not st.ultimo_ts:
                continue
            ultimo_ts, strumento, fonte = st.ultimo_ts, st.ultimo_strumento, "jsonl"
            ev = hook.get(st.session_id) if not st.sidechain else None
            fermo_da_hook = False
            if ev and ev.get("ts", 0) >= st.ultimo_ts - 1:
                ultimo_ts = max(ultimo_ts, ev["ts"])
                fonte = "hook"
                if ev.get("tool"):
                    strumento = ev["tool"]
                fermo_da_hook = ev.get("event") == "Stop"
            inattivo = ora - ultimo_ts
            al_lavoro = inattivo <= soglia and not fermo_da_hook
            progetto = Path(st.cwd).name if st.cwd else p.parent.name
            messaggio = st.ultimo_assistente or st.ultimo_utente
            risultato.append({
                "progetto": progetto,
                "cwd": st.cwd,
                "sessione": st.session_id,
                "tipo": "subagente" if st.sidechain else "sessione",
                "agente": st.agent_id,
                "padre": st.parent_session,
                "stato": "al lavoro" if al_lavoro else "fermo",
                "strumento": strumento,
                "messaggio": " ".join(messaggio.split())[:300],
                "ultimo_agg": ultimo_ts,
                "fonte": fonte,
                "token_in": st.token_in, "token_out": st.token_out,
                "cache_read": st.cache_r, "cache_write": st.cache_w,
                "costo": round(st.costo, 4),
                "modello": st.modello,
            })
        risultato.sort(key=lambda s: s["ultimo_agg"], reverse=True)
        return risultato

    def progetti(self) -> list[str]:
        visti = dict.fromkeys(config.DEFAULT_PROJECTS)
        for s in self.sessioni(eta_max_h=24 * 30):
            if s["cwd"]:
                visti.setdefault(s["cwd"])
        return list(visti)
