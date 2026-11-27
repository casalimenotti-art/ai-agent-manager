"""Storico delle conversazioni con Guardian: JSON Lines, un file al giorno, FUORI dal repo (può contenere dati dei clienti)."""
import json
import os
import re
import threading
import time
from datetime import date
from pathlib import Path

import agenti

_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_TESTO = 20000
_LOCK_SCRITTURA = threading.Lock()


def cartella_default() -> Path:
    env = os.environ.get("GUARDIAN_CONV_DIR")
    return Path(env) if env else Path.home() / ".claude" / "guardian" / "conversazioni"


def _dir(cartella) -> Path:
    return Path(cartella) if cartella else cartella_default()


def _file(data: str, cartella) -> Path:
    return _dir(cartella) / f"{data}.jsonl"


def aggiungi(msg: dict, cartella=None) -> bool:
    """Aggiunge un messaggio (ruolo, testo, ts) al file di oggi. Testo mascherato. Ritorna False se non salva."""
    try:
        testo = agenti.maschera(msg.get("testo"), MAX_TESTO)
        ruolo = str(msg.get("ruolo") or "")
        if not testo or ruolo not in ("user", "assistant"):
            return False
        riga = {"ruolo": ruolo, "testo": testo, "ts": msg.get("ts") or time.time()}
        d = _dir(cartella)
        d.mkdir(parents=True, exist_ok=True)
        dati = (json.dumps(riga, ensure_ascii=False) + "\n").encode("utf-8")
        with _LOCK_SCRITTURA:
            with open(_file(date.today().isoformat(), cartella), "ab", buffering=0) as f:
                f.write(dati)   # una sola write per riga: righe mai intrecciate
        return True
    except (OSError, ValueError, TypeError, AttributeError):
        return False


def _leggi(path: Path) -> list[dict]:
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for riga in f:
                try:
                    m = json.loads(riga)
                except ValueError:
                    continue
                if isinstance(m, dict) and m.get("ruolo") in ("user", "assistant") and isinstance(m.get("testo"), str):
                    out.append({"ruolo": m["ruolo"], "testo": m["testo"], "ts": m.get("ts", 0)})
    except OSError:
        pass
    return out


def carica_oggi(cartella=None, limite: int = 50) -> list[dict]:
    return carica_giorno(date.today().isoformat(), cartella)[-limite:] if limite > 0 else []


def elenco_giorni(cartella=None) -> list[str]:
    """Giorni con storico, dal più recente."""
    try:
        nomi = [p.stem for p in _dir(cartella).glob("*.jsonl") if _DATA.match(p.stem)]
    except OSError:
        return []
    return sorted(nomi, reverse=True)


def carica_giorno(data: str, cartella=None) -> list[dict]:
    data = str(data)
    if not _DATA.match(data):   # evita percorsi arbitrari
        return []
    return _leggi(_file(data, cartella))
