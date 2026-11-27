"""Catalogo per la barra laterale: frontmatter di agenti (~/.claude/agents/*.md) e skill, ricerca e gruppi. Funzioni pure."""
from __future__ import annotations

import json
import re
from pathlib import Path

import config

_FM = re.compile(r"\A﻿?---[ \t]*\r?\n(.*?)\r?\n---", re.S)
_CHIAVE = re.compile(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$")
MAX_DESC = 1200

# categorie degli agenti (le stesse tre dello spazio Squadra)
CAT_AGENTI = ["Sviluppo", "Squadra", "Sistema"]
_SVILUPPO = {"web-designer", "sviluppatore-dashboard"}
_SQUADRA = {"cacciatore-clienti", "verificatore-fonti", "redattore-outreach", "analista-risultati", "analista-presenza-online",
            "scopritore-problemi", "compilatore-schede-visita", "ricercatore-web", "scout-strumenti"}


def categoria_agente(nome: str) -> str:
    return "Sviluppo" if nome in _SVILUPPO else "Squadra" if nome in _SQUADRA else "Sistema"


def leggi_frontmatter(percorso) -> dict:
    """{name, description, tools} dal frontmatter di un .md. Mai eccezioni: file mancante/malformato -> dict vuoto o parziale."""
    try:
        testo = Path(percorso).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError, TypeError):
        return {}
    m = _FM.match(testo)
    if not m:
        return {}
    campi: dict[str, str] = {}
    chiave = None
    for riga in m.group(1).splitlines():
        k = _CHIAVE.match(riga) if not riga[:1].isspace() else None
        if k:
            chiave, val = k.group(1).lower(), k.group(2).strip()
            campi[chiave] = "" if val in (">", "|", ">-", "|-") else val.strip("\"'")
        elif chiave and riga.strip():
            campi[chiave] = (campi[chiave] + " " + riga.strip()).strip()
    desc = " ".join(campi.get("description", "").split())[:MAX_DESC]
    tools = [t.strip().strip("\"'") for t in re.split(r"[,\[\]]", campi.get("tools", "")) if t.strip().strip("\"'")]
    return {"name": campi.get("name", ""), "description": desc, "tools": tools}


def scheda_agente(nome: str, home: Path | None = None) -> dict:
    """Dettaglio di un agente: nome, descrizione, tools, percorso (esiste o no)."""
    f = (home or config.CLAUDE_HOME) / "agents" / f"{nome}.md"
    meta = leggi_frontmatter(f)
    return {"nome": nome, "descrizione": meta.get("description") or "(nessuna descrizione)", "tools": meta.get("tools", []),
            "percorso": str(f), "esiste": f.is_file()}


def percorso_skill(cartella: str, home: Path | None = None) -> Path | None:
    """SKILL.md di una skill per nome cartella (installate, sincronizzate, plugin); None se non c'è."""
    if not re.fullmatch(r"[\w.-]{1,100}", cartella or ""):
        return None
    h = home or config.CLAUDE_HOME
    cand = [h / "skills" / cartella / "SKILL.md", *sorted(h.glob(f"skills/synced/*/{cartella}/SKILL.md")),
            *sorted(h.glob(f"plugins/*/*/*/skills/{cartella}/SKILL.md"))]
    return next((p for p in cand if p.is_file()), None)


FILE_SKILL_IT = Path(__file__).parent / "dati" / "skill_it.json"


def carica_mappa_it(percorso: Path | None = None) -> dict:
    """Mappa nome skill -> riga italiana. File mancante o JSON rotto: mappa vuota."""
    try:
        d = json.loads(Path(percorso or FILE_SKILL_IT).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in d.items() if isinstance(k, str) and isinstance(v, str)} if isinstance(d, dict) else {}


def descrizione_it(nome: str, descrizione_originale: str, mappa: dict | None) -> str:
    """Riga italiana se presente, altrimenti la descrizione originale."""
    return (mappa or {}).get(nome) or descrizione_originale


def filtra(voci: list[dict], cerca: str) -> list[dict]:
    """Voci con 'nome' (e 'descrizione' / 'ruolo' facoltativi) che contengono tutte le parole cercate."""
    parole = (cerca or "").lower().split()
    if not parole:
        return list(voci)
    return [v for v in voci if all(p in " ".join(str(v.get(k, "")) for k in ("nome", "ruolo", "descrizione")).lower() for p in parole)]


def raggruppa(voci: list[dict], chiave_cat) -> dict[str, list[dict]]:
    """Raggruppa per categoria mantenendo l'ordine di prima comparsa."""
    out: dict[str, list[dict]] = {}
    for v in voci:
        out.setdefault(chiave_cat(v), []).append(v)
    return out
