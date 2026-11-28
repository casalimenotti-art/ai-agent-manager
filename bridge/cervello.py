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
import threading
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
        # is_error = limite raggiunto o guasto: non è una risposta, così scatta la riserva
        elif ev.get("type") == "result" and not visto and ev.get("result") and not ev.get("is_error"):
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


def _esegui(cmd: list[str], prompt: str, estrai, timeout: float) -> Iterator[str]:
    cartella = Path(os.environ.get("GUARDIAN_HOME", Path.home() / ".guardian")) / "cervello"
    cartella.mkdir(parents=True, exist_ok=True)
    # la domanda passa da stdin: su Windows i .CMD spezzano gli argomenti lunghi con a capo e virgolette
    proc = subprocess.Popen(cmd, cwd=cartella, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
    try:
        proc.stdin.write(prompt); proc.stdin.close()  # type: ignore[union-attr]
    except OSError:
        pass  # il processo ha già chiuso: si legge comunque quello che ha scritto
    scaduto = threading.Timer(timeout, proc.kill)  # scatta anche se il processo non scrive nulla (Codex stampa solo alla fine)
    scaduto.start()
    visto = False
    try:
        for riga in estrai(proc.stdout):  # type: ignore[arg-type]
            visto = visto or bool(riga.strip())
            yield riga
    finally:
        scaduto.cancel()
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
    if proc.returncode and not visto:  # es. limite raggiunto: nessuna risposta → si prova l'altro motore
        raise RuntimeError(f"uscito con codice {proc.returncode}")


def chiedi_claude(prompt: str, bin_claude: str, timeout: float = 90) -> Iterator[str]:
    cmd = [bin_claude, "-p", "--output-format", "stream-json", "--verbose", "--permission-mode", "plan",
           "--disallowedTools", *VIETATI]
    return _esegui(cmd, prompt, testi_da_stream, timeout)


def chiedi_codex(prompt: str, bin_codex: str, timeout: float = 120) -> Iterator[str]:
    """Riserva: Codex CLI del titolare in sandbox di sola lettura; lo stdout contiene solo la risposta finale."""
    cmd = [bin_codex, "exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-"]
    return _esegui(cmd, prompt, iter, timeout)


def claude_al_limite(soglia: float = 98) -> bool:
    """True se l'utilizzo settimanale di Claude (statusline di Guardian) è oltre la soglia e non ancora azzerato."""
    f = Path(os.environ.get("GUARDIAN_USAGE_FILE", Path.home() / ".claude" / "guardian" / "usage.json"))
    try:
        sett = json.loads(f.read_text(encoding="utf-8"))["seven_day"]
        return sett["pct"] >= soglia and time.time() < sett.get("resets_at", float("inf"))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def codex_permesso(r: dict) -> bool:
    """Codex in sandbox read-only può comunque LEGGERE tutto il disco: risponde solo a chi è in GUARDIAN_CODEX_PER."""
    ammessi = {x.strip().lower() for x in os.environ.get("GUARDIAN_CODEX_PER", "menotti").split(",") if x.strip()}
    return str(r.get("utente", "")).strip().lower() in ammessi


def servi(client, bin_claude: str | None = None, intervallo: float = 1.5, giri: int = 0, modello: str | None = None,
          bin_codex: str | None = None) -> int:
    """Ciclo del cervello: Claude Code, con Codex come riserva. `giri` > 0 solo per i test."""
    bin_claude = bin_claude or os.environ.get("GUARDIAN_CLAUDE_BIN") or shutil.which("claude")
    bin_codex = bin_codex or os.environ.get("GUARDIAN_CODEX_BIN") or shutil.which("codex")
    motori = [m for m in (("claude-code", chiedi_claude, bin_claude), ("codex", chiedi_codex, bin_codex)) if m[2]]
    if not motori:
        print("Né 'claude' né 'codex' trovati: installane uno o imposta GUARDIAN_CLAUDE_BIN / GUARDIAN_CODEX_BIN.", file=sys.stderr)
        return 2
    print(f"Cervello di Guardian attivo ({', '.join(m[0] for m in motori)}, in sola risposta). Ctrl+C per fermare.")
    ultimo_battito, n = 0.0, 0
    try:
        while True:
            pronti = [m for m in motori if not (m[0] == "claude-code" and claude_al_limite())] or motori
            attuale = modello or pronti[0][0]
            if time.monotonic() - ultimo_battito > 20:
                client.call("bridge_cervello_battito", modello=attuale)
                ultimo_battito = time.monotonic()
            r = client.call("bridge_prendi_richiesta")
            if r:
                seq, errore = 0, None
                for nome, chiedi, bin_ in pronti:
                    if nome == "codex" and not codex_permesso(r):
                        client.call("bridge_rispondi", richiesta_id=r["id"], seq=seq, fine=True, errore=True,
                                    testo="Il cervello principale non è disponibile e quello di riserva è riservato all'amministratore.")
                        errore = None
                        break
                    try:
                        for f in frasi(chiedi(costruisci_prompt(r), bin_)):
                            client.call("bridge_rispondi", richiesta_id=r["id"], seq=seq, testo=f, fine=False, errore=False)
                            seq += 1
                        client.call("bridge_rispondi", richiesta_id=r["id"], seq=seq, testo="", fine=True, errore=False)
                        errore = None
                        if nome != attuale:  # l'HQ vede quale motore ha risposto
                            client.call("bridge_cervello_battito", modello=nome)
                        break
                    except Exception as e:
                        errore = e
                        if seq:  # risposta già iniziata: non si ricomincia con l'altro motore
                            break
                if errore is not None:  # la richiesta non resta mai appesa
                    client.call("bridge_rispondi", richiesta_id=r["id"], seq=seq, testo=f"Non sono riuscito a rispondere ({type(errore).__name__}).",
                                fine=True, errore=True)
            n += 1
            if giri and n >= giri:
                return 0
            if not r:
                time.sleep(intervallo)
    except KeyboardInterrupt:
        print("Cervello fermato.")
        return 0
