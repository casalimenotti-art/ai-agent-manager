"""Skill: elenco da ~/.claude/skills/*/SKILL.md, prompt di esecuzione, installazione da GitHub."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

import config

# solo https://github.com/<owner>/<repo>[.git][/]  (niente query, fragment, userinfo, sottopercorsi)
URL_GITHUB = re.compile(r"^https://github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/([A-Za-z0-9._-]+?)(?:\.git)?/?$")


def _meta(f: Path) -> dict:
    try:
        m = re.match(r"^---\s*\n(.*?)\n---", f.read_text(encoding="utf-8", errors="replace"), re.S)
        meta = yaml.safe_load(m.group(1)) if m else {}
    except (OSError, yaml.YAMLError):
        meta = {}
    return meta if isinstance(meta, dict) else {}


def _radici(skills_dir: Path | None) -> list[tuple[str, list[Path]]]:
    """(origine, file SKILL.md) in ordine di priorità. Con skills_dir esplicito guarda solo lì (test)."""
    if skills_dir is not None:
        return [("installata", sorted(skills_dir.glob("*/SKILL.md")))]
    home = config.CLAUDE_HOME
    return [
        ("installata", sorted(f for f in (home / "skills").glob("*/SKILL.md"))),
        ("account", sorted((home / "skills" / "synced").glob("*/*/SKILL.md"))),   # skill sincronizzate dal tuo account
        ("plugin", sorted(home.glob("plugins/*/*/*/skills/*/SKILL.md"))),          # skill dei plugin
    ]


def elenca_skill(skills_dir: Path = None) -> list[dict]:
    """Tutte le skill visibili a Claude Code su questa macchina, senza duplicati per nome (vince la prima origine)."""
    out, visti = [], set()
    for origine, files in _radici(skills_dir):
        for f in files:
            meta = _meta(f)
            nome = str(meta.get("name") or f.parent.name)
            if nome in visti:
                continue
            visti.add(nome)
            out.append({
                "nome": nome,
                "descrizione": " ".join(str(meta.get("description") or "(nessuna descrizione)").split()),
                "cartella": f.parent.name,
                "origine": origine,
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
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
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


# ----------------------------------------------------------------- catalogo verificato
# Elenco FISSO (nessun URL arbitrario): repo e percorsi sono stati letti e scansionati prima dell'inserimento
# (solo testo/asset, nessuno script eseguibile). Per aggiungere una voce serve rivedere il codice della skill.
CATALOGO = [
    {"id": "frontend-design", "repo": "anthropics/skills", "path": "skills/frontend-design", "rischio": "basso",
     "titolo": "Frontend Design", "descrizione": "Interfacce web distintive e curate: token di design, tipografia, layout, motion."},
    {"id": "theme-factory", "repo": "anthropics/skills", "path": "skills/theme-factory", "rischio": "basso",
     "titolo": "Theme Factory", "descrizione": "10 temi pronti (colori + font) da applicare a slide, pagine e documenti."},
    {"id": "brand-guidelines", "repo": "anthropics/skills", "path": "skills/brand-guidelines", "rischio": "basso",
     "titolo": "Brand Guidelines", "descrizione": "Applica palette e tipografia di marca in modo coerente."},
    {"id": "canvas-design", "repo": "anthropics/skills", "path": "skills/canvas-design", "rischio": "basso-medio",
     "titolo": "Canvas Design", "descrizione": "Poster e arte visiva (PNG/PDF) con filosofia di design; include ~50 font. Può scaricare font."},
    {"id": "algorithmic-art", "repo": "anthropics/skills", "path": "skills/algorithmic-art", "rischio": "basso-medio",
     "titolo": "Algorithmic Art", "descrizione": "Arte generativa con p5.js. L'HTML generato carica p5.js da cdnjs e font da Google Fonts."},
    {"id": "web-design-guidelines", "repo": "vercel-labs/agent-skills", "path": "skills/web-design-guidelines", "rischio": "basso",
     "titolo": "Web Design Guidelines", "descrizione": "Audit di UI, accessibilità e UX contro le Web Interface Guidelines di Vercel."},
]
_ID_CATALOGO = {c["id"]: c for c in CATALOGO}


def catalogo_locale(skills_dir: Path = None) -> list[dict]:
    base = skills_dir or config.SKILLS_DIR
    return [{**c, "installata": (base / Path(c["path"]).name / "SKILL.md").is_file()} for c in CATALOGO]


def _git(args: list[str], cwd: Path | None = None, timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})


def installa_catalogo_locale(id_skill: str, skills_dir: Path = None) -> dict:
    voce = _ID_CATALOGO.get(id_skill)
    if not voce:
        return {"ok": False, "messaggio": "Skill non presente nel catalogo."}
    base = skills_dir or config.SKILLS_DIR
    nome = Path(voce["path"]).name
    dest = base / nome
    if dest.exists():
        return {"ok": False, "messaggio": f"'{nome}' è già installata: non la sovrascrivo."}
    tmp = Path(tempfile.mkdtemp(prefix="guardian-"))
    try:
        repo = tmp / "r"
        try:
            r = _git(["clone", "-q", "--depth", "1", "--filter=blob:none", "--sparse", "--",
                      f"https://github.com/{voce['repo']}.git", str(repo)])
            if r.returncode == 0:
                r = _git(["sparse-checkout", "set", "--", voce["path"]], cwd=repo)
            if r.returncode != 0:
                return {"ok": False, "messaggio": "git non riuscito: " + (r.stderr.strip()[-300:] or "errore")}
            sha = _git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"ok": False, "messaggio": f"git non riuscito: {e}"}
        src = repo / voce["path"]
        if not (src / "SKILL.md").is_file():
            return {"ok": False, "messaggio": "SKILL.md non trovato nel percorso atteso."}
        if any(p.is_symlink() for p in src.rglob("*")):
            return {"ok": False, "messaggio": "La skill contiene link simbolici: rifiutata per sicurezza."}
        base.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest, symlinks=False)
        (dest / ".guardian-source.json").write_text(
            json.dumps({"repo": f"https://github.com/{voce['repo']}", "path": voce["path"], "commit": sha}, indent=1))
        return {"ok": True, "messaggio": f"'{nome}' installata (commit {sha[:7]}) in {dest}"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
