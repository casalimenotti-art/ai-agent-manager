"""Skill: elenco da ~/.claude/skills/*/SKILL.md, prompt di esecuzione, installazione da GitHub."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

import config

# solo https://github.com/<owner>/<repo>[.git][/]  (niente query, fragment, userinfo, sottopercorsi)
URL_GITHUB = re.compile(r"^https://github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/([A-Za-z0-9._-]+?)(?:\.git)?/?$")


def elenca_skill(skills_dir: Path = None) -> list[dict]:
    base = skills_dir or config.SKILLS_DIR
    out = []
    for f in sorted(base.glob("*/SKILL.md")):
        meta: dict = {}
        try:
            m = re.match(r"^---\s*\n(.*?)\n---", f.read_text(encoding="utf-8", errors="replace"), re.S)
            if m:
                meta = yaml.safe_load(m.group(1)) or {}
        except (OSError, yaml.YAMLError):
            pass
        if not isinstance(meta, dict):
            meta = {}
        out.append({
            "nome": str(meta.get("name") or f.parent.name),
            "descrizione": " ".join(str(meta.get("description") or "(nessuna descrizione)").split()),
            "cartella": f.parent.name,
        })
    return out


def prompt_skill(nome: str, richiesta: str) -> str:
    return f"Usa la skill {nome} per: {richiesta.strip()}"


def valida_url(url: str) -> tuple[str, str] | None:
    """Ritorna (owner, repo) se l'URL è https://github.com/owner/repo, altrimenti None."""
    m = URL_GITHUB.match((url or "").strip())
    if not m:
        return None
    owner, repo = m.groups()
    if repo in (".", "..") or repo.startswith(".") or ".." in repo:
        return None
    return owner, repo


def installa_locale(url: str, skills_dir: Path = None) -> dict:
    base = skills_dir or config.SKILLS_DIR
    url = (url or "").strip()
    v = valida_url(url)
    if not v:
        return {"ok": False, "messaggio": "URL non valido: accetto solo https://github.com/<utente>/<repo>"}
    repo = v[1]
    dest = base / repo
    if dest.exists():
        return {"ok": False, "messaggio": f"Esiste già una skill '{repo}' in {base}: non la sovrascrivo."}
    base.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".guardian-", dir=base))  # cartella nostra: la possiamo cancellare
    try:
        clone = tmp / repo
        try:
            r = subprocess.run(
                ["git", "clone", "--depth", "1", "--", f"https://github.com/{v[0]}/{repo}.git", str(clone)],
                capture_output=True, text=True, timeout=180,
                env={**__import__("os").environ, "GIT_TERMINAL_PROMPT": "0"},
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"ok": False, "messaggio": f"git clone non riuscito: {e}"}
        if r.returncode != 0:
            return {"ok": False, "messaggio": "git clone non riuscito: " + (r.stderr.strip()[-300:] or "errore")}
        if not (clone / "SKILL.md").is_file():
            return {"ok": False, "messaggio": "Il repository non ha un SKILL.md nella radice: non è una skill installabile qui."}
        shutil.rmtree(clone / ".git", ignore_errors=True)
        clone.rename(dest)
        return {"ok": True, "messaggio": f"Skill '{repo}' installata in {dest}"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
