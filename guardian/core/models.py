"""Costanti, validazioni e formato handoff di Guardian Hub (solo libreria standard)."""
from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

TASK_STATI = ("backlog", "planned", "ready", "running", "waiting", "blocked", "needs_approval", "completed", "failed",
              "cancelled")
TASK_TERMINALI = ("completed", "failed", "cancelled")
TASK_APERTI = tuple(s for s in TASK_STATI if s not in TASK_TERMINALI)
TASK_STATI_V1 = {"in attesa": "ready", "in corso": "running", "bloccato": "blocked", "completato": "completed"}
PRIORITA = ("bassa", "media", "alta", "urgente")
APPROVAL_STATI = ("richiesta", "approvata", "rifiutata")
ACTION_TYPES = ("email", "pubblicazione", "contatto_cliente", "spesa", "pagamento", "irreversibile", "account_esterno",
                "comando_pericoloso", "altro")
DEVICE_STATI = ("online", "occupato", "limite", "errore", "offline")
AGENT_STATI = ("online", "offline", "idle", "working", "waiting", "needs_approval", "error", "unknown")
AGENT_TIPI = ("claude-code", "codex", "api", "manuale")
SEVERITA = ("info", "warning", "error", "critical")
MEMORY_KINDS = ("obiettivo", "decisione", "info_progetto", "preferenza", "risultato", "errore", "procedura", "ripresa")
HANDOFF_STATI = ("aperto", "preso", "chiuso")
ONLINE_SECONDI = 120  # un dispositivo è online se l'ultimo heartbeat è più recente di così


def _carica_regex_segreti() -> re.Pattern:
    """Riusa il filtro segreti del registro condiviso (registro/scrivi.py)."""
    try:
        spec = importlib.util.spec_from_file_location("_registro_scrivi", REPO / "registro" / "scrivi.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod._SEGRETO
    except Exception:  # file assente: filtro minimo equivalente
        return re.compile(r"(sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|eyJ[A-Za-z0-9_-]{20,}\.|"
                          r"(password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*\S+)", re.IGNORECASE)


SEGRETO = _carica_regex_segreti()
_JWT = re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.")


class ValidazioneError(ValueError):
    pass


def adesso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def pulisci(testo, massimo: int = 2000, obbligatorio: bool = False, nome: str = "testo") -> str:
    """Normalizza un testo libero e rifiuta segreti evidenti."""
    t = (testo or "").strip()
    if obbligatorio and not t:
        raise ValidazioneError(f"Il campo «{nome}» è obbligatorio.")
    if SEGRETO.search(t) or _JWT.search(t):
        raise ValidazioneError(f"Il campo «{nome}» sembra contenere una password o una chiave: non va salvato.")
    return t[:massimo]


def pulisci_file(files) -> list[str]:
    if isinstance(files, str):
        files = [f for f in re.split(r"[\n,]", files)]
    out = [pulisci(f, 300, nome="file") for f in (files or [])]
    return [f for f in out if f][:50]


def scegli(valore, ammessi, nome: str) -> str:
    v = (valore or "").strip().lower()
    if v not in ammessi:
        raise ValidazioneError(f"{nome} non valido: usa uno tra {', '.join(ammessi)}.")
    return v


def eta_secondi(ts: str | None, ora: datetime | None = None) -> float | None:
    if not ts:
        return None
    try:
        t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return ((ora or datetime.now(timezone.utc)) - t).total_seconds()


def stato_dispositivo(device: dict, ora: datetime | None = None) -> str:
    """Stato reale: offline se nessun heartbeat recente, qualunque cosa dichiari il record."""
    eta = eta_secondi(device.get("last_seen"), ora)
    if eta is None or eta > ONLINE_SECONDI:
        return "offline"
    if device.get("limit_reached"):
        return "limite"
    if device.get("error"):
        return "errore"
    s = device.get("stato") or "online"
    return s if s in DEVICE_STATI else "online"


@dataclass
class Handoff:
    """Passaggio di lavoro leggibile da agenti (Markdown) e da Guardian (campi)."""
    agent_name: str
    summary: str  # obiettivo + stato attuale
    next_step: str
    task_id: int | None = None
    completed_steps: str = ""
    files_changed: list[str] = field(default_factory=list)
    decisions: str = ""
    errors: str = ""
    tests: str = ""
    timestamp: str = ""

    def valida(self) -> "Handoff":
        self.agent_name = pulisci(self.agent_name, 80, True, "agente")
        self.summary = pulisci(self.summary, 4000, True, "obiettivo e stato")
        self.next_step = pulisci(self.next_step, 1000, True, "prossimo passo")
        for campo in ("completed_steps", "decisions", "errors", "tests"):
            setattr(self, campo, pulisci(getattr(self, campo), 4000, nome=campo))
        self.files_changed = pulisci_file(self.files_changed)
        self.timestamp = self.timestamp or adesso()
        return self

    def markdown(self) -> str:
        files = "\n".join(f"- {f}" for f in self.files_changed) or "- (nessuno)"
        sez = [("Obiettivo e stato attuale", self.summary), ("Lavoro completato", self.completed_steps),
               ("Decisioni prese", self.decisions), ("Problemi incontrati", self.errors),
               ("Test eseguiti", self.tests)]
        corpo = "\n\n".join(f"## {t}\n{v or '(niente)'}" for t, v in sez)
        return (f"# Handoff{f' task #{self.task_id}' if self.task_id else ''} — {self.agent_name}\n\n"
                f"- creato: {self.timestamp}\n\n{corpo}\n\n## File modificati\n{files}\n\n"
                f"## Prossimo passo\n{self.next_step}\n")


AGENTE_HEARTBEAT_SECONDI = 180  # oltre: il bridge non sta riferendo, lo stato dell'agente non è noto


def stato_agente(agent: dict, ora: datetime | None = None) -> str:
    """Stato mostrato: quello riferito dal bridge, ma 'unknown' se il bridge non lo aggiorna da troppo tempo.
    La presenza del PC non rende 'online' un agente."""
    eta = eta_secondi(agent.get("last_heartbeat"), ora)
    if eta is None or eta > AGENTE_HEARTBEAT_SECONDI:
        return "unknown" if agent.get("stato") != "offline" else "offline"
    s = agent.get("stato") or "unknown"
    return s if s in AGENT_STATI else "unknown"
