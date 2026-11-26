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
DEFAULT_PROJECTS = [p.strip() for p in (os.environ.get("DEFAULT_PROJECTS") or "").split(",") if p.strip()]

REFRESH_S = int(_num("REFRESH_S", 3))
IDLE_THRESHOLD_S = _num("IDLE_THRESHOLD_S", 120)
HISTORY_S = _num("HISTORY_S", 120)
AGENT_MAX_AGE_H = _num("AGENT_MAX_AGE_H", 24)
CHAT_TIMEOUT_S = _num("CHAT_TIMEOUT_S", 900)
CHAT_PERMISSION_MODE = os.environ.get("CHAT_PERMISSION_MODE") or "default"

# Stima prezzi USD / milione di token: (input, output). Cache read = 0.1x input, cache write = 1.25x input.
PRICES = {"opus": (15.0, 75.0), "sonnet": (3.0, 15.0), "haiku": (1.0, 5.0)}
DEFAULT_PRICE = PRICES["sonnet"]
try:
    if os.environ.get("PRICES_JSON"):
        PRICES.update({k: tuple(v) for k, v in json.loads(os.environ["PRICES_JSON"]).items()})
except (ValueError, TypeError):
    pass
