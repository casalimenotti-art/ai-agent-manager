"""Configurazione letta da dashboard/.env e dalle variabili d'ambiente."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _path(name: str, default: str) -> Path:
    return Path(os.environ.get(name) or default).expanduser()


def _num(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name) or default)
    except ValueError:
        return default


SOURCE = (os.environ.get("GUARDIAN_SOURCE") or "local").lower()
AGENT_URL = os.environ.get("GUARDIAN_AGENT_URL", "")
TOKEN = os.environ.get("GUARDIAN_TOKEN", "")

CLAUDE_HOME = _path("CLAUDE_HOME", "~/.claude")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN") or "claude"
EVENTS_FILE = _path("GUARDIAN_EVENTS_FILE", "~/.claude/guardian/events.jsonl")
PROJECTS_DIR = CLAUDE_HOME / "projects"
SKILLS_DIR = CLAUDE_HOME / "skills"
LEADS_DIR = _path("LEADS_DIR", str(BASE_DIR.parent / "leads"))     # CSV scritti da cacciatore-clienti
VISITE_DIR = EVENTS_FILE.parent                                     # stati visite e foto (fuori dal repo)
DEFAULT_PROJECTS = [p.strip() for p in (os.environ.get("DEFAULT_PROJECTS") or "").split(",") if p.strip()]

REFRESH_S = int(_num("REFRESH_S", 3))
IDLE_THRESHOLD_S = _num("IDLE_THRESHOLD_S", 120)
HISTORY_S = _num("HISTORY_S", 120)
AGENT_MAX_AGE_H = _num("AGENT_MAX_AGE_H", 24)
CHAT_TIMEOUT_S = _num("CHAT_TIMEOUT_S", 900)
CHAT_PERMISSION_MODE = os.environ.get("CHAT_PERMISSION_MODE") or "default"

# Prezzi USD / milione di token, da https://platform.claude.com/docs/en/about-claude/pricing (verificati 2026-11-26).
# Voci (sottostringa dell'ID modello, input, output, moltiplicatore cache-read): la PRIMA che combacia vince,
# quindi le più specifiche stanno in alto. Cache write = 1.25x input (5 min).
PRICES = [
    ("fable-5-2", 8.0, 40.0, 0.025), ("mythos-5-2", 8.0, 40.0, 0.025),
    ("fable-5-1", 10.0, 50.0, 0.025), ("mythos-5-1", 10.0, 50.0, 0.025),
    ("fable-5", 10.0, 50.0, 0.1), ("mythos-5", 10.0, 50.0, 0.1),
    ("opus-5-5", 4.0, 20.0, 0.05),
    ("opus-4-1", 15.0, 75.0, 0.1), ("opus-4-2025", 15.0, 75.0, 0.1),
    ("opus", 5.0, 25.0, 0.1),
    ("sonnet-5-5", 2.0, 10.0, 0.05), ("sonnet-5", 2.0, 10.0, 0.1), ("sonnet", 3.0, 15.0, 0.1),
    ("haiku-5-5", 0.10, 0.50, 0.1), ("haiku", 1.0, 5.0, 0.1),
]
DEFAULT_PRICE = ("?", 2.0, 10.0, 0.05)
# Haiku 5.5: oltre 100k token di prompt (input + cache) si applica una tariffa 5x
HAIKU_55_LUNGO = {"soglia": 100_000, "input": 0.50, "output": 2.50}
# Override opzionale: PRICES_JSON={"sonnet-5-5":[2,10]}  (cache read 0.1x se non diversamente noto)
try:
    if os.environ.get("PRICES_JSON"):
        PRICES = [(k, float(v[0]), float(v[1]), 0.1) for k, v in json.loads(os.environ["PRICES_JSON"]).items()] + PRICES
except (ValueError, TypeError, IndexError):
    pass
