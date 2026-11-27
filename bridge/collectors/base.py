"""Lettura incrementale di file JSONL locali (scritti dagli hook) con offset persistente."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from guardian.core.models import SEGRETO  # noqa: E402

PROMPT_MAX = 200


def redigi(testo: str, massimo: int = PROMPT_MAX) -> str:
    """Testo condivisibile: una riga, troncato, e mai con segreti (sostituiti da [rimosso])."""
    t = " ".join(str(testo or "").split())
    t = SEGRETO.sub("[rimosso]", t)
    return t[:massimo] + ("…" if len(t) > massimo else "")


def iso(ts) -> str:
    """ts epoch (float) o ISO -> ISO UTC."""
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")
    return str(ts or datetime.now(timezone.utc).isoformat(timespec="seconds"))


@dataclass
class Lettura:
    """Risultato di un giro di un collector."""
    stato: str | None = None          # None = nessuna informazione nuova
    error: str | None = None
    usage: dict | None = None
    logs: list[dict] = field(default_factory=list)


class CodaJsonl:
    """Legge solo le righe nuove di un file JSONL, ricordando la posizione in un file di offset."""

    def __init__(self, path: str | Path, offset_path: str | Path):
        self.path, self.offset_path = Path(path).expanduser(), Path(offset_path).expanduser()

    def _offset(self) -> int:
        try:
            return int(self.offset_path.read_text().strip() or 0)
        except (OSError, ValueError):
            return 0

    def nuove(self, massimo: int = 2000) -> list[dict]:
        if not self.path.exists():
            return []
        off = self._offset()
        if off > self.path.stat().st_size:  # file ruotato o ricreato
            off = 0
        righe = []
        with open(self.path, "rb") as f:
            f.seek(off)
            for raw in f:
                if not raw.endswith(b"\n"):
                    break  # riga ancora in scrittura: la riprendo al prossimo giro
                off += len(raw)
                try:
                    righe.append(json.loads(raw))
                except ValueError:
                    continue
                if len(righe) >= massimo:
                    break
        self.offset_path.parent.mkdir(parents=True, exist_ok=True)
        self.offset_path.write_text(str(off))
        return righe
