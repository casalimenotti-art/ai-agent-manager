#!/usr/bin/env python3
"""Installa (con conferma) gli hook che danno a Guardian lo stato reale degli agenti.

  python bridge/install_hooks.py claude            # mostra cosa cambierebbe in ~/.claude/settings.json
  python bridge/install_hooks.py claude --apply    # applica (prima crea una copia di sicurezza)
  python bridge/install_hooks.py codex             # stampa la riga da aggiungere a ~/.codex/config.toml

Non tocca nulla senza --apply e una conferma esplicita. Se è già presente l'hook della plancia locale
(dashboard/hooks/guardian_hook.py, stesso formato), per quell'evento non ne aggiunge un altro.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import time
from pathlib import Path

QUI = Path(__file__).resolve().parent
EVENTI_CLAUDE = ("UserPromptSubmit", "PreToolUse", "PostToolUse", "Notification", "Stop", "SubagentStop")
CON_MATCHER = ("PreToolUse", "PostToolUse")
GIA_NOSTRI = ("claude_hook.py", "guardian_hook.py")


def comando_python(script: Path) -> str:
    py = "python" if sys.platform.startswith("win") else "python3"
    return f'{py} "{script}"'


def unisci_hook_claude(settings: dict, comando: str) -> tuple[dict, list[str]]:
    """Restituisce (nuove impostazioni, eventi aggiunti). Non modifica l'originale."""
    nuovo = copy.deepcopy(settings or {})
    hooks = nuovo.setdefault("hooks", {})
    aggiunti = []
    for ev in EVENTI_CLAUDE:
        voci = hooks.setdefault(ev, [])
        presenti = [h.get("command", "") for v in voci for h in v.get("hooks", [])]
        if any(n in c for c in presenti for n in GIA_NOSTRI):
            continue
        voce = {"hooks": [{"type": "command", "command": comando}]}
        if ev in CON_MATCHER:
            voce = {"matcher": "*", **voce}
        voci.append(voce)
        aggiunti.append(ev)
    return nuovo, aggiunti


def claude(apply: bool, settings_path: Path, si: bool = False) -> int:
    try:
        attuali = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    except ValueError:
        print(f"{settings_path} non è JSON valido: non lo tocco.", file=sys.stderr)
        return 2
    nuovi, aggiunti = unisci_hook_claude(attuali, comando_python(QUI / "hooks" / "claude_hook.py"))
    if not aggiunti:
        print("Hook di Guardian già presenti per tutti gli eventi: niente da fare.")
        return 0
    print(f"Eventi da aggiungere in {settings_path}: {', '.join(aggiunti)}")
    print(json.dumps({"hooks": {e: nuovi["hooks"][e] for e in aggiunti}}, indent=2, ensure_ascii=False))
    if not apply:
        print("\nNessuna modifica fatta. Per applicare: python bridge/install_hooks.py claude --apply")
        return 0
    if not si and input("Applico? Scrivi 'si' per confermare: ").strip().lower() not in ("si", "sì"):
        print("Annullato.")
        return 1
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        copia = settings_path.with_name(f"{settings_path.name}.bak-{time.strftime('%Y%m%d%H%M%S')}")
        shutil.copy2(settings_path, copia)
        print(f"Copia di sicurezza: {copia}")
    settings_path.write_text(json.dumps(nuovi, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Fatto. Riavvia Claude Code; poi nel bridge/.env imposta GUARDIAN_CLAUDE_AGENT_ID (es. menotti-claude).")
    return 0


def codex() -> int:
    script = QUI / "hooks" / "codex_notify.py"
    py = "python" if sys.platform.startswith("win") else "python3"
    print("Aggiungi in ~/.codex/config.toml (in cima al file, fuori da ogni sezione [..]):\n")
    print(f'notify = ["{py}", "{script.as_posix()}"]\n')
    print("Poi nel bridge/.env imposta GUARDIAN_CODEX_AGENT_ID (es. amico1-codex).")
    print("Da verificare: dopo un turno di Codex deve comparire una riga in ~/.guardian/codex-events.jsonl.")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("agente", choices=("claude", "codex"))
    p.add_argument("--apply", action="store_true")
    p.add_argument("--yes", action="store_true", help=argparse.SUPPRESS)
    p.add_argument("--settings", default=str(Path.home() / ".claude" / "settings.json"))
    a = p.parse_args(argv)
    return claude(a.apply, Path(a.settings), a.yes) if a.agente == "claude" else codex()


if __name__ == "__main__":
    raise SystemExit(main())
