#!/usr/bin/env python3
"""Guardian Bridge: collega un PC (e il suo agente) a Guardian Hub.

Solo connessioni HTTPS in USCITA verso Supabase. Nessuna porta aperta, nessun comando remoto eseguito:
i task assegnati vengono solo scaricati e mostrati / salvati in ~/.guardian/inbox.json.

Configurazione (variabili d'ambiente o file bridge/.env, escluso da git):
  GUARDIAN_SUPABASE_URL, GUARDIAN_SUPABASE_ANON_KEY, GUARDIAN_DEVICE_TOKEN, GUARDIAN_AGENT, GUARDIAN_MODEL
Modalità locale (test/sviluppo, nessuna rete):  --local percorso.db

Esempi:
  python bridge/guardian_bridge.py heartbeat --loop 60 --status-file ~/.guardian/stato.json
  python bridge/guardian_bridge.py event nota "Finiti i test del sito" --task 4 --file siti-demo/x.html
  python bridge/guardian_bridge.py task-update 4 --stato completato --next "Revisione di amico1"
  python bridge/guardian_bridge.py checkpoint --task 4 --summary "..." --done "..." --next "..." --file a.py
  python bridge/guardian_bridge.py pull
  python bridge/guardian_bridge.py sync-registro --branches
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from guardian.core.models import Handoff, ValidazioneError, pulisci, pulisci_file  # noqa: E402

CASA = Path(os.environ.get("GUARDIAN_HOME", Path.home() / ".guardian"))


def carica_env(path: Path = Path(__file__).resolve().parent / ".env") -> None:
    """Legge KEY=VALUE da bridge/.env senza sovrascrivere l'ambiente."""
    if not path.exists():
        return
    for riga in path.read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if riga and not riga.startswith("#") and "=" in riga:
            k, v = riga.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class RpcClient:
    """Chiama le funzioni RPC di Supabase (PostgREST) con la chiave pubblica anon + token del dispositivo."""

    def __init__(self, url: str, anon_key: str, token: str, timeout: float = 15):
        if not url.startswith("https://") and not url.startswith("http://localhost"):
            raise SystemExit("GUARDIAN_SUPABASE_URL deve essere https://")
        self.url, self.key, self.token, self.timeout = url.rstrip("/"), anon_key, token, timeout

    def call(self, fn: str, **params):
        body = json.dumps({"p_token": self.token, **{f"p_{k}": v for k, v in params.items()}}).encode()
        req = urllib.request.Request(f"{self.url}/rest/v1/rpc/{fn}", data=body, method="POST", headers={
            "apikey": self.key, "Authorization": f"Bearer {self.key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                testo = r.read().decode() or "null"
                return json.loads(testo)
        except urllib.error.HTTPError as e:
            dettaglio = e.read().decode(errors="replace")[:300]
            raise RuntimeError(f"Guardian Hub ha rifiutato {fn} ({e.code}): {dettaglio}") from None


class LocalClient:
    """Stessa interfaccia di RpcClient ma su SqliteStore (per test e sviluppo)."""

    def __init__(self, store, token: str):
        self.store, self.token = store, token

    def call(self, fn: str, **params):
        return getattr(self.store, fn)(self.token, **params)


def crea_client(args):
    token = os.environ.get("GUARDIAN_DEVICE_TOKEN", "")
    if args.local:
        from guardian.core.store_sqlite import SqliteStore
        return LocalClient(SqliteStore(args.local), args.token or token)
    url, key = os.environ.get("GUARDIAN_SUPABASE_URL", ""), os.environ.get("GUARDIAN_SUPABASE_ANON_KEY", "")
    if not (url and key and (args.token or token)):
        raise SystemExit("Mancano GUARDIAN_SUPABASE_URL, GUARDIAN_SUPABASE_ANON_KEY o GUARDIAN_DEVICE_TOKEN "
                         "(vedi bridge/.env.example).")
    return RpcClient(url, key, args.token or token)


# ------------------------------------------------------------------ comandi
def leggi_stato_file(path: str | None) -> dict:
    """File di stato locale scritto a mano o da un hook dell'agente (JSON). Campi ammessi sotto."""
    if not path:
        return {}
    p = Path(path).expanduser()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    ammessi = ("stato", "agent_name", "model", "current_task", "error", "limit_reached")
    return {k: d[k] for k in ammessi if k in d}


def heartbeat_once(client, args) -> dict:
    dati = {"stato": args.stato, "agent_name": os.environ.get("GUARDIAN_AGENT") or None,
            "model": os.environ.get("GUARDIAN_MODEL") or None, "current_task": args.task,
            "error": args.error, "limit_reached": args.limit}
    dati.update({k: v for k, v in leggi_stato_file(args.status_file).items() if v is not None})
    dati["error"] = pulisci(dati.get("error"), 500, nome="errore") or None
    return client.call("bridge_heartbeat", **dati)


def cmd_heartbeat(client, args):
    if not args.loop:
        print(json.dumps(heartbeat_once(client, args), default=str))
        return 0
    print(f"Heartbeat ogni {args.loop}s. Ctrl+C per fermare (invia 'offline').")
    try:
        while True:
            try:
                heartbeat_once(client, args)
            except (RuntimeError, urllib.error.URLError, OSError) as e:
                print(f"[guardian] heartbeat non riuscito: {e}", file=sys.stderr)
            time.sleep(max(15, args.loop))
    except KeyboardInterrupt:
        args.stato, args.status_file = "offline", None
        heartbeat_once(client, args)
        print("Offline.")
    return 0


def cmd_event(client, args):
    ok = client.call("bridge_event", event_type=pulisci(args.tipo, 40, True, "tipo"),
                     message=pulisci(args.messaggio, 1000, True, "messaggio"), task_id=args.task,
                     files=pulisci_file(args.file), external_key=None)
    print("Evento registrato." if ok else "Evento già presente.")
    return 0


def cmd_task_update(client, args):
    r = client.call("bridge_task_update", task_id=args.id, stato=args.stato,
                    next_step=pulisci(args.next, 1000, nome="prossimo passo") or None, files=pulisci_file(args.file))
    print(f"Task #{r['id']} → {r['stato']}")
    return 0


def cmd_checkpoint(client, args):
    h = Handoff(agent_name=os.environ.get("GUARDIAN_AGENT") or args.agente or "agente", summary=args.summary,
                next_step=args.next, task_id=args.task, completed_steps=args.done or "",
                files_changed=args.file, decisions=args.decisions or "", errors=args.errors or "",
                tests=args.tests or "").valida()
    hid = client.call("bridge_checkpoint", task_id=h.task_id, agent_name=h.agent_name, summary=h.summary,
                      completed_steps=h.completed_steps, files_changed=h.files_changed, decisions=h.decisions,
                      errors=h.errors, tests=h.tests, next_step=h.next_step)
    cartella = CASA / "handoffs"
    cartella.mkdir(parents=True, exist_ok=True)
    copia = cartella / f"{time.strftime('%Y%m%dT%H%M%S')}-task{h.task_id or 0}.md"
    copia.write_text(h.markdown(), encoding="utf-8")
    print(f"Handoff #{hid} salvato su Guardian. Copia locale: {copia}")
    return 0


def cmd_pull(client, args):
    tasks = client.call("bridge_pull_tasks") or []
    CASA.mkdir(parents=True, exist_ok=True)
    (CASA / "inbox.json").write_text(json.dumps(tasks, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if not tasks:
        print("Nessun task assegnato.")
    for t in tasks:
        print(f"#{t['id']} [{t['priorita']}] {t['stato']}: {t['titolo']}" + (f" → {t['next_step']}" if t.get("next_step") else ""))
    print("I task NON vengono eseguiti automaticamente: passali tu al tuo agente.")
    return 0


def _git(repo: Path, *argv) -> str:
    r = subprocess.run(["git", *argv], cwd=repo, capture_output=True, text=True, timeout=30)
    return r.stdout if r.returncode == 0 else ""


def righe_registro(repo: Path, branches: bool = False) -> list[dict]:
    """Righe di registro/*.jsonl (cartella locale e, se richiesto, tutti i branch origin/*)."""
    testi: list[str] = [p.read_text(encoding="utf-8") for p in sorted((repo / "registro").glob("*.jsonl"))]
    if branches:
        for ref in _git(repo, "for-each-ref", "refs/remotes/origin", "--format=%(refname:short)").split():
            for nome in _git(repo, "ls-tree", "--name-only", ref, "registro/").split():
                if nome.endswith(".jsonl"):
                    testi.append(_git(repo, "show", f"{ref}:{nome}"))
    visti, out = set(), []
    for testo in testi:
        for riga in testo.splitlines():
            riga = riga.strip()
            if not riga:
                continue
            chiave = "registro:" + hashlib.sha256(riga.encode()).hexdigest()[:32]
            if chiave in visti:
                continue
            try:
                d = json.loads(riga)
                azione = pulisci(d.get("azione"), 1000, True, "azione")
            except (ValueError, ValidazioneError):
                continue  # righe rotte o con segreti: mai inviate
            visti.add(chiave)
            out.append({"chi": d.get("chi"), "agente": d.get("agente"), "azione": azione,
                        "file": pulisci_file(d.get("file") or []), "esito": d.get("esito"), "ts": d.get("ts"),
                        "external_key": chiave})
    return out


def cmd_sync_registro(client, args):
    righe = righe_registro(Path(args.repo), args.branches)
    nuove = 0
    for i in range(0, len(righe), 200):
        nuove += client.call("bridge_import_registro", rows=righe[i:i + 200]) or 0
    print(f"Registro: {len(righe)} righe lette, {nuove} nuove su Guardian.")
    return 0


def cmd_init_local(args):
    """Solo modalità locale: crea collaboratori da persone.json e un dispositivo, stampa il token."""
    from guardian.core.store import crea_store_locale
    s = crea_store_locale(args.local)
    d, token = s.register_device(args.user, args.nome, os.environ.get("GUARDIAN_AGENT", ""))
    print(f"Dispositivo #{d['id']} creato. Token (mostrato una volta): {token}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Guardian Bridge")
    p.add_argument("--local", help="Usa un database SQLite locale invece di Supabase")
    p.add_argument("--token", help="Token dispositivo (meglio GUARDIAN_DEVICE_TOKEN in bridge/.env)")
    sub = p.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("heartbeat")
    h.add_argument("--stato", default="online", choices=("online", "occupato", "limite", "errore", "offline"))
    h.add_argument("--task", type=int)
    h.add_argument("--error")
    h.add_argument("--limit", action="store_true", help="Limite di utilizzo dell'agente raggiunto")
    h.add_argument("--loop", type=int, default=0, help="Secondi tra un heartbeat e l'altro (min 15)")
    h.add_argument("--status-file", help="JSON locale con stato/agent_name/model/current_task/error/limit_reached")
    e = sub.add_parser("event")
    e.add_argument("tipo")
    e.add_argument("messaggio")
    e.add_argument("--task", type=int)
    e.add_argument("--file", action="append", default=[])
    t = sub.add_parser("task-update")
    t.add_argument("id", type=int)
    t.add_argument("--stato", choices=("in attesa", "in corso", "bloccato", "completato"))
    t.add_argument("--next")
    t.add_argument("--file", action="append", default=[])
    c = sub.add_parser("checkpoint")
    c.add_argument("--task", type=int)
    c.add_argument("--agente")
    c.add_argument("--summary", required=True, help="Obiettivo e stato attuale")
    c.add_argument("--done", help="Lavoro completato")
    c.add_argument("--decisions")
    c.add_argument("--errors")
    c.add_argument("--tests")
    c.add_argument("--next", required=True, help="Prossimo passo preciso")
    c.add_argument("--file", action="append", default=[])
    sub.add_parser("pull")
    s = sub.add_parser("sync-registro")
    s.add_argument("--repo", default=str(REPO))
    s.add_argument("--branches", action="store_true", help="Legge il registro anche da tutti i branch origin/*")
    i = sub.add_parser("init-local")
    i.add_argument("--user", required=True)
    i.add_argument("--nome", required=True)
    return p


COMANDI = {"heartbeat": cmd_heartbeat, "event": cmd_event, "task-update": cmd_task_update,
           "checkpoint": cmd_checkpoint, "pull": cmd_pull, "sync-registro": cmd_sync_registro}


def main(argv=None) -> int:
    carica_env()
    args = parser().parse_args(argv)
    try:
        if args.cmd == "init-local":
            if not args.local:
                raise SystemExit("init-local richiede --local")
            return cmd_init_local(args)
        return COMANDI[args.cmd](crea_client(args), args)
    except (ValidazioneError, PermissionError, RuntimeError, urllib.error.URLError) as e:
        print(f"Errore: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
