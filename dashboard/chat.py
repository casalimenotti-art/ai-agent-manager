"""Agente centrale: esegue `claude -p` in una cartella progetto, con streaming e --resume."""
from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Iterator

import config


def costruisci_comando(resume: str | None = None) -> list[str]:
    cmd = [config.CLAUDE_BIN, "-p", "--output-format", "stream-json", "--verbose",
           "--include-partial-messages", "--permission-mode", config.CHAT_PERMISSION_MODE]
    if resume:
        cmd += ["--resume", resume]
    return cmd


def esegui_locale(prompt: str, cwd: str, resume: str | None = None) -> Iterator[dict]:
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
            costruisci_comando(resume), cwd=cartella, stdin=subprocess.PIPE,
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
