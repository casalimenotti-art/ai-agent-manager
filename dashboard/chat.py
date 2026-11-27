"""Agente centrale: esegue `claude -p` in una cartella progetto, con streaming e --resume."""
from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from pathlib import Path
from typing import Iterator

import config


def agente_installato(nome: str | None) -> bool:
    """L'agente esiste in ~/.claude/agents (o è un nome sicuro)? Se no, non lo si passa a claude (darebbe errore)."""
    return bool(nome) and bool(re.fullmatch(r"[a-z0-9-]{1,64}", nome)) and (config.CLAUDE_HOME / "agents" / f"{nome}.md").is_file()


def costruisci_comando(resume: str | None = None, agente: str | None = None) -> list[str]:
    cmd = [config.CLAUDE_BIN, "-p", "--output-format", "stream-json", "--verbose",
           "--include-partial-messages", "--permission-mode", config.CHAT_PERMISSION_MODE]
    if agente and agente_installato(agente):
        cmd += ["--agent", agente]
    if resume:
        cmd += ["--resume", resume]
    return cmd


def esegui_locale(prompt: str, cwd: str, resume: str | None = None, agente: str | None = None) -> Iterator[dict]:
    """Lancia claude e produce gli eventi stream-json (dict).

    Il prompt va su stdin (equivale a `claude -p "<domanda>"` ma evita problemi con
    domande che iniziano per '-' o molto lunghe). Alla fine produce un evento
    {"type": "guardian_end", "returncode", "stderr"}.
    """
    cartella = Path(cwd).expanduser()
    if not cartella.is_dir():
        yield {"type": "guardian_end", "returncode": -1, "stderr": f"Cartella inesistente: {cwd}"}
        return
    try:
        proc = subprocess.Popen(
            costruisci_comando(resume, agente), cwd=cartella, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1,
        )
    except FileNotFoundError:
        yield {"type": "guardian_end", "returncode": -1,
               "stderr": f"Comando '{config.CLAUDE_BIN}' non trovato (imposta CLAUDE_BIN nel .env)"}
        return
    timer = threading.Timer(config.CHAT_TIMEOUT_S, proc.kill)
    timer.start()
    stderr_buf: list[str] = []
    t = threading.Thread(target=lambda: stderr_buf.append(proc.stderr.read()), daemon=True)
    t.start()
    try:
        try:
            proc.stdin.write(prompt)
            proc.stdin.close()
        except BrokenPipeError:
            pass
        for riga in proc.stdout:
            riga = riga.strip()
            if not riga:
                continue
            try:
                yield json.loads(riga)
            except ValueError:
                yield {"type": "guardian_raw", "text": riga}
        rc = proc.wait()
        t.join(timeout=2)
        yield {"type": "guardian_end", "returncode": rc, "stderr": "".join(stderr_buf).strip()}
    finally:  # chiusura anticipata del generatore (es. utente cambia pagina)
        timer.cancel()
        if proc.poll() is None:
            proc.kill()
            proc.wait()


class Risposta:
    """Accumula gli eventi di una richiesta e ne espone testo, strumenti, session_id, costo."""

    def __init__(self):
        self.testo = ""
        self.strumenti: list[str] = []
        self.session_id: str | None = None
        self.costo: float | None = None
        self.errore: str | None = None
        self._streaming = False  # True se abbiamo ricevuto delta di testo

    def aggiungi(self, ev: dict) -> bool:
        """Ritorna True se la vista va aggiornata."""
        tipo = ev.get("type")
        if ev.get("session_id"):
            self.session_id = ev["session_id"]
        if tipo == "stream_event":
            e = ev.get("event", {})
            d = e.get("delta", {})
            if e.get("type") == "content_block_delta" and d.get("type") == "text_delta":
                self._streaming = True
                self.testo += d.get("text", "")
                return True
        elif tipo == "assistant":
            for b in (ev.get("message", {}).get("content") or []):
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    self.strumenti.append(b.get("name", "?"))
                    return True
            if not self._streaming:  # fallback senza partial messages
                for b in (ev.get("message", {}).get("content") or []):
                    if isinstance(b, dict) and b.get("type") == "text":
                        self.testo += b.get("text", "")
                        return True
        elif tipo == "result":
            self.costo = ev.get("total_cost_usd")
            if ev.get("is_error"):
                self.errore = ev.get("result") or "errore"
            elif ev.get("result") and not self.testo.strip():
                self.testo = ev["result"]
            return True
        elif tipo == "guardian_end":
            if ev.get("returncode") not in (0, None) and not self.errore:
                self.errore = ev.get("stderr") or f"claude è terminato con codice {ev.get('returncode')}"
            return True
        return False


# ---------------------------------------------------------------- "Lancia un agente" (sempre dopo conferma)
MAX_COMPITO = 4000
LANCI: list[dict] = []   # registro dei lanci in background (letto dall'interfaccia, scritto dai thread)
_LANCI_LOCK = threading.Lock()
DOPPIO_CLIC_S = 3.0


def agenti_installati() -> list[str]:
    """Nomi degli agenti presenti in ~/.claude/agents (gli unici lanciabili)."""
    cartella = config.CLAUDE_HOME / "agents"
    if not cartella.is_dir():
        return []
    return sorted(p.stem for p in cartella.glob("*.md") if re.fullmatch(r"[a-z0-9-]{1,64}", p.stem))


def pulisci_compito(testo: str) -> str:
    """Testo libero: via i caratteri di controllo (tranne a capo/tab), spazi ai bordi, tetto di lunghezza."""
    t = "".join(c for c in (testo or "") if c in "\n\t" or ord(c) >= 32)
    return t.strip()[:MAX_COMPITO]


def prepara_lancio(agente: str, compito: str, cwd: str, installati: list[str] | None = None) -> dict:
    """Costruisce (senza eseguire nulla) il lancio di un agente.

    Ritorna {ok, errore, argv, prompt, cwd, modo}. `argv` è una lista (mai una stringa di shell);
    il compito viaggia su stdin come nel resto della chat, quindi non viene mai interpolato in una shell.
    Mai bypassPermissions: si usa config.CHAT_PERMISSION_MODE.
    """
    ammessi = agenti_installati() if installati is None else installati
    compito = pulisci_compito(compito)
    modo = config.CHAT_PERMISSION_MODE
    res = {"ok": False, "errore": "", "argv": [], "prompt": compito, "cwd": (cwd or "").strip(), "modo": modo}
    if agente not in ammessi or not agente_installato(agente):
        res["errore"] = f"L'agente «{agente}» non è installato in ~/.claude/agents."
    elif not compito:
        res["errore"] = "Scrivi il compito da assegnare."
    elif modo == "bypassPermissions":
        res["errore"] = "I lanci dalla dashboard non usano bypassPermissions: cambia CHAT_PERMISSION_MODE."
    elif not res["cwd"] or not Path(res["cwd"]).expanduser().is_dir():
        res["errore"] = f"Cartella inesistente: {res['cwd'] or '(vuota)'}"
    else:
        res["argv"] = costruisci_comando(None, agente)
        res["ok"] = True
    return res


def anteprima_lancio(lancio: dict) -> str:
    """Testo semplice (da passare a theme.esc se finisce in HTML) che spiega cosa verrà eseguito."""
    return (f"Cartella: {lancio['cwd']}\nComando: {' '.join(lancio['argv'])}\n"
            f"Permessi: {lancio['modo']}\nCompito (passato come input, non come comando di shell):\n{lancio['prompt']}")


def lancia_in_background(esegui, lancio: dict, agente: str) -> dict:
    """Avvia `esegui(prompt, cwd, None, agente)` (es. fonte.esegui) in un thread e ne registra lo stato."""
    voce_reg = {"agente": agente, "compito": lancio["prompt"][:120], "cwd": lancio["cwd"],
                "stato": "in corso", "errore": None, "session_id": None, "_ts": time.time(), "_chiave": (agente, lancio["prompt"], lancio["cwd"])}
    with _LANCI_LOCK:
        # doppio clic: stesso compito già partito da meno di DOPPIO_CLIC_S secondi e ancora in corso -> non rilanciare
        for v in LANCI:
            if v.get("_chiave") == voce_reg["_chiave"] and v["stato"] == "in corso" and voce_reg["_ts"] - v["_ts"] < DOPPIO_CLIC_S:
                return v
        LANCI.append(voce_reg)

    def _corpo():
        r = Risposta()
        try:
            for ev in esegui(lancio["prompt"], lancio["cwd"], None, agente):
                r.aggiungi(ev)
        except Exception as e:  # il thread non deve morire in silenzio
            r.errore = str(e)
        voce_reg.update(stato="errore" if r.errore else "finito", errore=r.errore, session_id=r.session_id)

    threading.Thread(target=_corpo, daemon=True).start()
    return voce_reg
