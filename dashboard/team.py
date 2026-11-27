"""Team: le tre persone (Claude Code + 2 Codex) e il registro condiviso in registro/*.jsonl.

Il registro si legge dalla cartella locale E da tutti i branch noti a git (locali e origin/*),
così le righe che gli amici hanno pushato sul proprio branch compaiono anche prima del merge.
"""
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CARTELLA = "registro"
_ENV_GIT = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}


def _git(repo: Path, *args, timeout: float = 10) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=_ENV_GIT)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def leggi_persone(repo: Path = REPO) -> list[dict]:
    try:
        dati = json.loads((repo / CARTELLA / "persone.json").read_text(encoding="utf-8"))
        return [p for p in dati if isinstance(p, dict) and p.get("id")]
    except (OSError, ValueError):
        return []


def analizza_righe(testo: str, fonte: str = "") -> list[dict]:
    """Righe JSONL -> voci valide (ignora righe rotte o senza i campi minimi)."""
    out = []
    for riga in (testo or "").splitlines():
        riga = riga.strip()
        if not riga:
            continue
        try:
            v = json.loads(riga)
        except ValueError:
            continue
        if not isinstance(v, dict) or not v.get("chi") or not v.get("azione") or not v.get("ts"):
            continue
        v = {k: v.get(k, "") for k in ("ts", "chi", "agente", "azione", "esito", "branch")} | {"file": v.get("file") or []}
        if not isinstance(v["file"], list):
            v["file"] = [str(v["file"])]
        v["fonte"] = fonte
        out.append(v)
    return out


def _rami(repo: Path) -> list[str]:
    out = _git(repo, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")
    return [r for r in (out or "").splitlines() if r and not r.endswith("/HEAD")]


def leggi_registro(repo: Path = REPO, da_git: bool = True) -> list[dict]:
    """Tutte le voci, senza doppioni, dalla più recente."""
    voci = []
    cart = repo / CARTELLA
    for f in sorted(cart.glob("*.jsonl")) if cart.is_dir() else []:
        try:
            voci += analizza_righe(f.read_text(encoding="utf-8"), "locale")
        except OSError:
            pass
    if da_git:
        for ref in _rami(repo):
            nomi = _git(repo, "ls-tree", "--name-only", f"{ref}:{CARTELLA}")
            for nome in (nomi or "").splitlines():
                if nome.endswith(".jsonl"):
                    voci += analizza_righe(_git(repo, "show", f"{ref}:{CARTELLA}/{nome}") or "",
                                           ref.removeprefix("refs/heads/").removeprefix("refs/remotes/"))
    visti, uniche = set(), []
    for v in voci:
        k = (v["ts"], v["chi"], v["azione"])
        if k not in visti:
            visti.add(k)
            uniche.append(v)
    return sorted(uniche, key=lambda v: v["ts"], reverse=True)


def commit_recenti(repo: Path = REPO, giorni: int = 7, limite: int = 40) -> list[dict]:
    """Ultimi commit di TUTTI i branch: chi, quando, messaggio, branch."""
    out = _git(repo, "log", "--all", f"--since={giorni}.days", f"-n{limite}", "--date=iso-strict",
               "--format=%h%x1f%an%x1f%ad%x1f%s%x1f%D")
    voci = []
    for riga in (out or "").splitlines():
        parti = riga.split("\x1f")
        if len(parti) == 5:
            voci.append({"hash": parti[0], "autore": parti[1], "ts": parti[2], "messaggio": parti[3], "rami": parti[4]})
    return voci


def aggiorna_da_github(repo: Path = REPO) -> tuple[bool, str]:
    """git fetch (solo lettura: non tocca i file di lavoro né i branch locali)."""
    out = _git(repo, "fetch", "--all", "--prune", "--quiet", timeout=30)
    return (True, "Aggiornato da GitHub.") if out is not None else (False, "Fetch non riuscito: controlla la rete o l'accesso a GitHub.")


def riepilogo(persone: list[dict], voci: list[dict], ora: datetime | None = None) -> list[dict]:
    """Per ogni persona: ultima voce, quante oggi (UTC), quante bloccate."""
    ora = ora or datetime.now(timezone.utc)
    oggi = ora.astimezone(timezone.utc).date().isoformat()
    out = []
    for p in persone:
        sue = [v for v in voci if v["chi"] == p["id"]]
        out.append({**p, "ultima": sue[0] if sue else None,
                    "oggi": sum(1 for v in sue if str(v["ts"])[:10] == oggi),
                    "bloccate": sum(1 for v in sue[:5] if v.get("esito") in ("bloccato", "fallito"))})
    return out


def quando(ts: str, ora: datetime | None = None) -> str:
    """'3 min fa', 'ieri 14:05', '26/11 09:30' (ora locale del PC)."""
    try:
        t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
    except ValueError:
        return str(ts)
    ora = ora or datetime.now(timezone.utc)
    sec = (ora - t).total_seconds()
    if sec < 60:
        return "adesso"
    if sec < 3600:
        return f"{int(sec // 60)} min fa"
    loc = t.astimezone()
    if sec < 86400 and loc.date() == ora.astimezone().date():
        return f"oggi {loc:%H:%M}"
    return f"{loc:%d/%m %H:%M}"


def passaggi_aperti(repo: Path = REPO) -> list[dict]:
    """Passaggi aperti o presi, letti dalla cartella locale e da tutti i branch.
    Lo stato va solo avanti (aperto -> preso -> chiuso): per ogni file vale la versione più avanzata."""
    import re
    ordine = {"aperto": 1, "preso": 2, "chiuso": 3}
    migliori: dict[str, tuple[int, str, str]] = {}

    def _vedi(nome: str, testo: str, fonte: str):
        m = re.search(r"^- stato: *(\w+)", testo or "", re.M)
        rango = ordine.get(m.group(1) if m else "", 0)
        if rango and rango > migliori.get(nome, (0,))[0]:
            migliori[nome] = (rango, testo, fonte)

    cart = repo / "passaggi"
    for f in sorted(cart.glob("*.md")) if cart.is_dir() else []:
        try:
            _vedi(f.name, f.read_text(encoding="utf-8"), "locale")
        except OSError:
            pass
    for ref in _rami(repo):
        for nome in (_git(repo, "ls-tree", "--name-only", f"{ref}:passaggi") or "").splitlines():
            if nome.endswith(".md"):
                _vedi(nome, _git(repo, "show", f"{ref}:passaggi/{nome}") or "", ref.split("/", 2)[-1])
    out = []
    for nome, (rango, testo, fonte) in migliori.items():
        if rango == 3:
            continue
        campo = lambda k: (re.search(rf"^- {k}: *(.+)$", testo, re.M) or [None, ""])[1].strip()
        titolo = (re.search(r"^# Passaggio di lavoro: *(.+)$", testo, re.M) or [None, nome])[1].strip()
        out.append({"nome": nome, "titolo": titolo, "stato": "aperto" if rango == 1 else "preso", "da": campo("da"),
                    "per": campo("per"), "branch": campo("branch"), "creato": campo("creato"), "fonte": fonte})
    return sorted(out, key=lambda v: v["creato"], reverse=True)
