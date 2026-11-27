"""Statistiche di sistema: processi Claude Code, CPU totale con storico, token/costo."""
from __future__ import annotations

import json
import math
import os
import threading
import time
from collections import deque

import psutil

import config

_MARCATORI_PERCORSO = ("@anthropic-ai/claude-code", "@anthropic-ai\\claude-code")


def e_processo_claude(nome: str, cmdline: list[str], exe: str = "") -> bool:
    """Vero se nome == claude* oppure il percorso contiene @anthropic-ai/claude-code."""
    n = (nome or "").lower()
    if n == "claude" or n == "claude.exe" or n.startswith("claude-"):
        return True
    # solo eseguibile e primi due argomenti (es. "node /.../@anthropic-ai/claude-code/cli.js"):
    # il resto della riga di comando può contenere la stringa per caso (es. una shell)
    blob = " ".join((cmdline or [])[:2]) + " " + (exe or "")
    return any(m in blob for m in _MARCATORI_PERCORSO)


class Campionatore:
    """Mantiene gli oggetti psutil.Process (necessari per cpu_percent) e lo storico CPU."""

    def __init__(self, storico_s: float | None = None):
        self.storico_s = config.HISTORY_S if storico_s is None else storico_s
        self._procs: dict[int, psutil.Process] = {}
        self._esclusi: dict[int, float] = {}   # pid -> create_time dei processi già scartati
        self._storico: deque[tuple[float, float, float]] = deque()
        self._lock = threading.Lock()
        self._lock_proc = threading.Lock()
        self._mio_pid = os.getpid()
        self._claude_pct = 0.0  # CPU Claude in % dell'intera macchina (cpu / n_core)
        psutil.cpu_percent(None)  # primo campione a vuoto

    def processi(self) -> dict:
        with self._lock_proc:   # cpu_percent(None) confronta con l'ultima chiamata: due thread insieme falsano la lettura
            return self._processi()

    def _processi(self) -> dict:
        trovati: dict[int, psutil.Process] = {}
        escl = self._esclusi
        nuovi_escl: dict[int, float] = {}
        for p in psutil.process_iter(["pid", "name", "create_time"]):
            info = p.info
            pid = info["pid"]
            if pid == self._mio_pid:
                continue
            if escl.get(pid) == info["create_time"]:   # già valutato e non Claude: niente cmdline/exe (costosi)
                nuovi_escl[pid] = info["create_time"]
                continue
            try:
                cmd, exe = p.cmdline(), p.exe()
            except (psutil.Error, OSError):
                cmd, exe = [], ""
            if e_processo_claude(info["name"], cmd or [], exe or ""):
                trovati[pid] = self._procs.get(pid) or p
            else:
                nuovi_escl[pid] = info["create_time"]
        self._esclusi = nuovi_escl
        self._procs = trovati
        lista = []
        for pid, p in trovati.items():
            try:
                lista.append({
                    "pid": pid,
                    "nome": p.name(),
                    "cpu": p.cpu_percent(None),  # % di un core; la prima lettura è 0
                    "ram_mb": round(p.memory_info().rss / 1048576, 1),
                    "cmd": " ".join(p.cmdline())[:120],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        somma = round(sum(x["cpu"] for x in lista), 1)
        self._claude_pct = min(100.0, somma / (psutil.cpu_count() or 1))
        return {
            "n": len(lista),
            "cpu": somma,
            "ram_mb": round(sum(x["ram_mb"] for x in lista), 1),
            "lista": sorted(lista, key=lambda x: -x["cpu"]),
        }

    def cpu_totale(self) -> dict:
        ora = time.time()
        with self._lock:
            self._storico.append((ora, psutil.cpu_percent(None), self._claude_pct))
            while self._storico and ora - self._storico[0][0] > self.storico_s:
                self._storico.popleft()
            storico = [[round(t - ora, 1), v, c] for t, v, c in self._storico]  # [sec relativi a ora, totale %, Claude %]
        vm = psutil.virtual_memory()
        return {
            "cpu": storico[-1][1],
            "n_core": psutil.cpu_count() or 1,
            "ram_pct": vm.percent,
            "ram_tot_mb": round(vm.total / 1048576),
            "storico": storico,
        }


def riepilogo_token(sessioni: list[dict], ore: float = 24) -> dict:
    """Token/costo: sessione più recente + totale delle sessioni attive nelle ultime `ore`."""
    principali = [s for s in sessioni if s["tipo"] == "sessione"]
    limite = time.time() - ore * 3600

    def somma(rows):
        return {
            "token_in": sum(r["token_in"] for r in rows),
            "token_out": sum(r["token_out"] for r in rows),
            "cache": sum(r["cache_read"] + r["cache_write"] for r in rows),
            "costo": round(sum(r["costo"] for r in rows), 2),
        }

    ultima = principali[0] if principali else None
    # i subagenti contano nel totale: hanno costi propri
    recenti = [s for s in sessioni if s["ultimo_agg"] >= limite]
    return {
        "ultima": ({"progetto": ultima["progetto"], "modello": ultima["modello"],
                    **somma([ultima] + [s for s in sessioni if s["padre"] == ultima["sessione"]])}
                   if ultima else None),
        "totale": somma(recenti),
        "ore": ore,
    }


# ---- ricavi inseriti a mano (per margine/ROI): {"YYYY-MM": importo_usd}
def _file_ricavi():
    return config.EVENTS_FILE.parent / "ricavi.json"


def leggi_ricavi() -> dict[str, float]:
    try:
        d = json.loads(_file_ricavi().read_text(encoding="utf-8"))
        return {str(k): float(v) for k, v in d.items() if isinstance(v, (int, float))}
    except (OSError, ValueError, AttributeError):
        return {}


def scrivi_ricavo(mese: str, importo: float) -> dict[str, float]:
    import re
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", mese or ""):
        raise ValueError("mese non valido (atteso YYYY-MM)")
    if not isinstance(importo, (int, float)) or not math.isfinite(importo) or importo < 0 or importo > 1e9:
        raise ValueError("importo non valido")
    dati = leggi_ricavi()
    dati[mese] = round(float(importo), 2)
    path = _file_ricavi()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(dati, indent=1), encoding="utf-8")
    tmp.replace(path)
    return dati
