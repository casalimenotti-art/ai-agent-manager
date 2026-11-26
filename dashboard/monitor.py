"""Statistiche di sistema: processi Claude Code, CPU totale con storico, token/costo."""
from __future__ import annotations

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
        self._storico: deque[tuple[float, float]] = deque()
        self._lock = threading.Lock()
        self._mio_pid = os.getpid()
        psutil.cpu_percent(None)  # primo campione a vuoto

    def processi(self) -> dict:
        trovati: dict[int, psutil.Process] = {}
        for p in psutil.process_iter(["pid", "name", "cmdline", "exe"]):
            info = p.info
            if info["pid"] == self._mio_pid:
                continue
            if e_processo_claude(info["name"], info["cmdline"] or [], info["exe"] or ""):
                trovati[info["pid"]] = self._procs.get(info["pid"]) or p
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
        return {
            "n": len(lista),
            "cpu": round(sum(x["cpu"] for x in lista), 1),
            "ram_mb": round(sum(x["ram_mb"] for x in lista), 1),
            "lista": sorted(lista, key=lambda x: -x["cpu"]),
        }

    def cpu_totale(self) -> dict:
        ora = time.time()
        with self._lock:
            self._storico.append((ora, psutil.cpu_percent(None)))
            while self._storico and ora - self._storico[0][0] > self.storico_s:
                self._storico.popleft()
            storico = [[round(t - ora, 1), v] for t, v in self._storico]  # secondi relativi a "ora"
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
