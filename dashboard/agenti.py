"""Monitor agenti: legge i JSONL di ~/.claude/projects (+ eventi hook opzionali)."""
from __future__ import annotations

import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import config


def parse_ts(s: str | None) -> float:
    if not s:
        return 0.0
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def prezzo_modello(modello: str) -> tuple[str, float, float, float]:
    m = (modello or "").lower()
    for voce in config.PRICES:
        if voce[0] in m:
            return voce
    return config.DEFAULT_PRICE


def costo(modello: str, inp: int, out: int, cache_read: int, cache_write: int) -> float:
    chiave, p_in, p_out, mult_read = prezzo_modello(modello)
    if chiave == "haiku-5-5" and inp + cache_read + cache_write > config.HAIKU_55_LUNGO["soglia"]:
        p_in, p_out = config.HAIKU_55_LUNGO["input"], config.HAIKU_55_LUNGO["output"]
    return (inp * p_in + out * p_out + cache_read * p_in * mult_read + cache_write * p_in * 1.25) / 1e6


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
        self.giorni: dict[str, dict] = {}   # "YYYY-MM-DD" (ora locale) -> contatori
        self.ore: dict[str, float] = {}  # "YYYY-MM-DD HH" (ora locale) -> costo
        self.modelli_g: dict[str, dict[str, float]] = {}  # giorno -> modello -> costo
        self._visti: set[str] = set()  # id messaggi già contati (il JSONL ripete gli usage)

    def _giorno(self, ts: float) -> dict:
        chiave = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else "?"
        return self.giorni.setdefault(chiave, {"costo": 0.0, "token_in": 0, "token_out": 0, "cache": 0,
                                               "msgs": 0, "tools": 0, "edits": 0})

    def feed(self, riga: dict):
        ts = parse_ts(riga.get("timestamp"))
        if ts:
            self.ultimo_ts = max(self.ultimo_ts, ts)
        self.cwd = self.cwd or riga.get("cwd") or ""  # cartella di avvio: stabile anche se la sessione fa cd
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
            g_chiave = datetime.fromtimestamp(ts or self.ultimo_ts).strftime("%Y-%m-%d") if (ts or self.ultimo_ts) else "?"
            g = self._giorno(ts or self.ultimo_ts)
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        self.ultimo_strumento = b.get("name", "")
                        g["tools"] += 1
                        if self.ultimo_strumento in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                            g["edits"] += 1
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
                c = costo(self.modello, i, o, cr, cw)
                self.costo += c
                mg = self.modelli_g.setdefault(g_chiave, {})
                mg[self.modello or "?"] = mg.get(self.modello or "?", 0.0) + c
                g["costo"] += c
                ora_k = datetime.fromtimestamp(ts or self.ultimo_ts).strftime("%Y-%m-%d %H") if (ts or self.ultimo_ts) else "?"
                self.ore[ora_k] = self.ore.get(ora_k, 0.0) + c
                g["token_in"] += i
                g["token_out"] += o
                g["cache"] += cr + cw
                g["msgs"] += 1
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


    def costi(self, giorni: int = 30) -> dict:
        """Spesa e produttività aggregate per giorno / progetto / modello (ultimi `giorni` giorni)."""
        oggi = date.today()
        inizio = oggi - timedelta(days=giorni - 1)
        elenco = [(inizio + timedelta(days=i)).isoformat() for i in range(giorni)]
        tot = {k: {"data": k, "costo": 0.0, "token_in": 0, "token_out": 0, "cache": 0, "msgs": 0, "tools": 0, "edits": 0}
               for k in elenco}
        progetti: dict[str, float] = {}
        modelli: dict[str, float] = {}
        ore: dict[str, float] = {}
        limite = time.time() - giorni * 86400
        for p in self._files():
            try:
                if p.stat().st_mtime < limite:
                    continue
            except OSError:
                continue
            st = self._stati.get(p) or self._stati.setdefault(p, _Stato(p))
            st.aggiorna()
            nome = Path(st.cwd).name if st.cwd else p.parent.name
            for chiave, g in st.giorni.items():
                if chiave not in tot:
                    continue
                for k, v in g.items():
                    tot[chiave][k] += v
                progetti[nome] = progetti.get(nome, 0.0) + g["costo"]
            for ok, v in st.ore.items():
                ore[ok] = ore.get(ok, 0.0) + v
            for chiave, per_modello in st.modelli_g.items():
                if chiave in tot:
                    for m, c in per_modello.items():
                        modelli[m] = modelli.get(m, 0.0) + c
        serie = [dict(v, costo=round(v["costo"], 4)) for v in tot.values()]
        costo_di = lambda n: sum(x["costo"] for x in serie[-n:])
        attivi7 = [x["costo"] for x in serie[-7:]]
        media7 = sum(attivi7) / 7
        giorni_mese = (date(oggi.year + (oggi.month == 12), oggi.month % 12 + 1, 1) - date(oggi.year, oggi.month, 1)).days
        mese = sum(x["costo"] for x in serie if x["data"].startswith(oggi.strftime("%Y-%m")))
        adesso = datetime.now()
        ultime5 = [(adesso - timedelta(hours=i)).strftime("%Y-%m-%d %H") for i in range(5)]
        costo_5h = sum(ore.get(k, 0.0) for k in ultime5)
        return {
            "giorni": serie,
            "ultime_5h": round(costo_5h, 4),
            "burn_orario": round(costo_5h / 5, 4),   # media oraria sulle ultime 5 ore di calendario
            "ore": {k: round(v, 4) for k, v in ore.items() if k in ultime5},
            "progetti": sorted(({"progetto": k, "costo": round(v, 4)} for k, v in progetti.items()), key=lambda x: -x["costo"]),
            "modelli": sorted(({"modello": k, "costo": round(v, 4)} for k, v in modelli.items()), key=lambda x: -x["costo"]),
            "oggi": round(serie[-1]["costo"], 4),
            "ultimi7": round(costo_di(7), 4),
            "ultimi30": round(costo_di(30), 4),
            "mese": round(mese, 4),
            "media7": round(media7, 4),
            "proiezione_mese": round(mese + media7 * (giorni_mese - oggi.day), 4),
            "mese_id": oggi.strftime("%Y-%m"),
        }
