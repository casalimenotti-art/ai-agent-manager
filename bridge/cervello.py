"""Cervello di Guardian sul PC del titolare: risponde alle domande dell'HQ con Claude Code in SOLA RISPOSTA.

- Prende le richieste dal database (RPC bridge_prendi_richiesta, solo il PC di un admin).
- Chiama `claude -p` in modalità plan, senza strumenti di scrittura, in una cartella vuota (~/.guardian/cervello).
- Rimanda la risposta a frasi (bridge_rispondi): l'HQ la legge a voce mentre arriva.
Usa l'abbonamento Claude Code del titolare sul suo PC: funziona solo quando il PC è acceso e il comando è in esecuzione.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from guardian.core.models import SEGRETO  # noqa: E402

SISTEMA = ("Sei Guardian, il centro di comando dell'azienda NEXO (tre collaboratori e i loro agenti AI). "
           "Rispondi in italiano, in modo naturale e parlato, al massimo 3 frasi brevi, senza elenchi e senza markdown. "
           "Usa solo il contesto fornito; se un dato non c'è, dillo. Non promettere azioni: non puoi eseguire nulla, "
           "non modificare file e non usare strumenti. Le azioni esterne richiedono sempre un'approvazione umana.")
VIETATI = ["Bash", "Edit", "Write", "MultiEdit", "NotebookEdit", "WebFetch", "WebSearch", "Task"]
_FRASE = re.compile(r"(.+?[.!?])(\s+|$)", re.S)


def costruisci_prompt(r: dict) -> str:
    contesto = json.dumps(r.get("contesto") or {}, ensure_ascii=False)[:4000]
    return f"{SISTEMA}\n\nChi chiede: {r.get('utente', '?')}\nContesto attuale dell'HQ (JSON): {contesto}\n\nDomanda: {r['testo']}"


def testi_da_stream(righe: Iterable[str]) -> Iterator[str]:
    """Estrae il testo dalle righe stream-json di `claude -p --output-format stream-json`."""
    visto = False
    for riga in righe:
        try:
            ev = json.loads(riga)
        except ValueError:
            continue
        if ev.get("type") == "assistant":
            for blocco in (ev.get("message") or {}).get("content") or []:
                if blocco.get("type") == "text" and blocco.get("text"):
                    visto = True
                    yield blocco["text"]
        elif ev.get("type") == "result" and not visto and ev.get("result"):
            yield str(ev["result"])


def frasi(pezzi: Iterable[str]) -> Iterator[str]:
    """Raggruppa i pezzi di testo in frasi complete, appena sono pronte (senza segreti)."""
    buf = ""
    for p in pezzi:
        buf += p
        while (m := _FRASE.match(buf)):
            f = " ".join(m.group(1).split())
            buf = buf[m.end():]
            if f:
                yield SEGRETO.sub("[rimosso]", f)
    resto = " ".join(buf.split())
    if resto:
        yield SEGRETO.sub("[rimosso]", resto)


def chiedi_claude(prompt: str, bin_claude: str, timeout: float = 90) -> Iterator[str]:
    cartella = Path(os.environ.get("GUARDIAN_HOME", Path.home() / ".guardian")) / "cervello"
    cartella.mkdir(parents=True, exist_ok=True)
    cmd = [bin_claude, "-p", prompt, "--output-format", "stream-json", "--verbose", "--permission-mode", "plan",
           "--disallowedTools", *VIETATI]
    proc = subprocess.Popen(cmd, cwd=cartella, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
    inizio = time.monotonic()
    try:
        for riga in testi_da_stream(proc.stdout):  # type: ignore[arg-type]
            yield riga
            if time.monotonic() - inizio > timeout:
                raise TimeoutError("risposta troppo lenta")
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)


def servi(client, bin_claude: str | None = None, intervallo: float = 1.5, giri: int = 0, modello: str = "claude-code") -> int:
    """Ciclo del cervello. `giri` > 0 solo per i test."""
    bin_claude = bin_claude or os.environ.get("GUARDIAN_CLAUDE_BIN") or shutil.which("claude")
    if not bin_claude:
        print("Comando 'claude' non trovato: installa Claude Code o imposta GUARDIAN_CLAUDE_BIN.", file=sys.stderr)
        return 2
    print("Cervello di Guardian attivo (Claude Code in sola risposta). Ctrl+C per fermare.")
    ultimo_battito, n = 0.0, 0
    try:
        while True:
            if time.monotonic() - ultimo_battito > 20:
                client.call("bridge_cervello_battito", modello=modello)
                ultimo_battito = time.monotonic()
            r = client.call("bridge_prendi_richiesta")
            if r:
                seq = 0
                try:
                    for f in frasi(chiedi_claude(costruisci_prompt(r), bin_claude)):
                        client.call("bridge_rispondi", richiesta_id=r["id"], seq=seq, testo=f, fine=False, errore=False)
                        seq += 1
                    client.call("bridge_rispondi", richiesta_id=r["id"], seq=seq, testo="", fine=True, errore=False)
                except Exception as e:  # la richiesta non resta mai appesa
                    client.call("bridge_rispondi", richiesta_id=r["id"], seq=seq, testo=f"Non sono riuscito a rispondere ({type(e).__name__}).",
                                fine=True, errore=True)
            n += 1
            if giri and n >= giri:
                return 0
            if not r:
                time.sleep(intervallo)
    except KeyboardInterrupt:
        print("Cervello fermato.")
        return 0
