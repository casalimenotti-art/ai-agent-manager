"""Chat parallele: da 1 a 5 chat, ognuna con la sua conversazione, cartella e agente, che lavorano nello stesso momento.

Ogni lavoro gira in un thread in background (un processo `claude` per chat) e la dashboard lo legge a intervalli: chiudere la
pagina non lo ferma. Nessuna chiamata a Streamlit qui dentro (i thread non possono usarlo). Cronologia salvata su disco.
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

import chat
import config

MAX_CHAT = 5
MAX_MSG, MAX_TESTO, MAX_PROMPT = 100, 20_000, 8_000


class Lavoro:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.risposta = chat.Risposta()
        self.fatto = False
        self.ctrl: dict = {}
        self.stop = threading.Event()
        self.t0 = time.time()
        self.t1: float | None = None

    @property
    def durata(self) -> float:
        return (self.t1 or time.time()) - self.t0


class Chat:
    def __init__(self, id: str, nome: str, cwd: str = "", agente: str | None = None, parla: bool = False):
        self.id, self.nome, self.cwd, self.agente, self.parla = id, nome, cwd, agente, parla
        self.sid: str | None = None
        self.msgs: list[dict] = []
        self.lavoro: Lavoro | None = None
        self.parlato = ""                 # testo già detto a voce (stato per il parlato in streaming)
        self.da_leggere = False           # c'è una risposta nuova da dire a voce
        self.flag_lavora = False          # ultimo segnale inviato al microfono a mani libere

    @property
    def in_corso(self) -> bool:
        return bool(self.lavoro and not self.lavoro.fatto)


def _ko(m: str) -> dict:
    return {"ok": False, "messaggio": m}


class Lavori:
    def __init__(self, fonte, percorso: Path | None = None, iniziali: int = 3, cwd_default: str = ""):
        self.fonte = fonte
        self.percorso = percorso
        self._lock = threading.RLock()
        self.chats: dict[str, Chat] = {}
        self._carica()
        while len(self.chats) < max(1, min(iniziali, MAX_CHAT)):
            self.nuova(cwd=cwd_default)
        for i, c in enumerate(self.chats.values()):      # la prima è il manager e parla; le altre sono Claude Code normale
            if i == 0 and not c.agente and not c.msgs:
                c.agente, c.parla = config.MANAGER_AGENT, True

    # ---- gestione chat
    def nuova(self, nome: str | None = None, cwd: str = "", agente: str | None = None) -> Chat | None:
        with self._lock:
            if len(self.chats) >= MAX_CHAT:
                return None
            n = 1
            while f"Chat {n}" in {c.nome for c in self.chats.values()}:
                n += 1
            c = Chat(uuid.uuid4().hex[:8], (nome or f"Chat {n}")[:40], cwd, agente)
            self.chats[c.id] = c
        self._salva()
        return c

    def chiudi(self, id: str) -> bool:
        with self._lock:
            c = self.chats.get(id)
            if not c or c.in_corso or len(self.chats) <= 1:
                return False
            del self.chats[id]
        self._salva()
        return True

    def imposta(self, id: str, cwd: str | None = None, agente: str | None | bool = False, parla: bool | None = None):
        with self._lock:
            c = self.chats.get(id)
            if not c:
                return
            if cwd is not None and cwd != c.cwd:
                c.cwd, c.sid = cwd, None           # altra cartella = altra conversazione
            if agente is not False and agente != c.agente:
                c.agente, c.sid = agente, None     # altro agente = altra conversazione
            if parla is not None:
                c.parla = bool(parla)
        self._salva()

    def reset(self, id: str) -> bool:
        with self._lock:
            c = self.chats.get(id)
            if not c or c.in_corso:
                return False
            c.msgs, c.sid, c.lavoro, c.parlato = [], None, None, ""
        self._salva()
        return True

    def segna_letto(self, id: str) -> None:
        with self._lock:
            c = self.chats.get(id)
            if c:
                c.da_leggere = False

    def get(self, id: str) -> Chat | None:
        return self.chats.get(id)

    def ids(self) -> list[str]:
        with self._lock:
            return list(self.chats)

    def in_corso(self) -> int:
        with self._lock:
            return sum(c.in_corso for c in self.chats.values())

    # ---- lavori
    def invia(self, id: str, testo: str) -> dict:
        testo = (testo or "").strip()
        with self._lock:
            c = self.chats.get(id)
            if not c:
                return _ko("Chat inesistente.")
            if c.in_corso:
                return _ko("Questa chat sta ancora lavorando.")
            if not testo:
                return _ko("Scrivi qualcosa.")
            if len(testo) > MAX_PROMPT:
                return _ko(f"Messaggio troppo lungo (max {MAX_PROMPT} caratteri).")
            if not c.cwd:
                return _ko("Scegli una cartella progetto.")
            lav = Lavoro(testo)
            c.lavoro, c.parlato, c.da_leggere = lav, "", c.parla
            c.msgs.append({"ruolo": "user", "testo": testo})
            del c.msgs[:-MAX_MSG]
        threading.Thread(target=self._corri, args=(c, lav), daemon=True, name=f"chat-{c.id}").start()
        return {"ok": True, "messaggio": "Avviato."}

    def ferma(self, id: str) -> bool:
        with self._lock:
            c = self.chats.get(id)
            lav = c.lavoro if c else None
            if not lav or lav.fatto:
                return False
            lav.stop.set()
        p = lav.ctrl.get("proc")
        if p is not None:
            try:
                p.kill()
            except OSError:
                pass
        return True

    def _corri(self, c: Chat, lav: Lavoro) -> None:
        gen = None
        try:
            gen = self.fonte.esegui(lav.prompt, c.cwd, c.sid, c.agente, ctrl=lav.ctrl)
            for ev in gen:
                lav.risposta.aggiungi(ev)
                if lav.stop.is_set():
                    break
        except Exception as e:                       # il thread non deve mai morire senza chiudere il lavoro
            lav.risposta.errore = f"{type(e).__name__}: {str(e)[:200]}"
        finally:
            if gen is not None:
                try:
                    gen.close()
                except Exception:
                    pass
            r = lav.risposta
            if lav.stop.is_set():
                r.errore = "Interrotto dal titolare."
            nota = " · ".join(x for x in (("🔧 " + ", ".join(r.strumenti[-8:])) if r.strumenti else "",
                                          f"≈${r.costo:.3f}" if r.costo else "") if x)
            testo_finale = r.testo or r.errore or ""
            if lav.stop.is_set():
                testo_finale = (r.testo + "\n\n⏹ Interrotto dal titolare.") if r.testo else "⏹ Interrotto dal titolare."
            with self._lock:
                if r.session_id and (not r.errore or lav.stop.is_set()):
                    c.sid = r.session_id
                c.msgs.append({"ruolo": "assistant", "testo": testo_finale[:MAX_TESTO], "nota": nota, "errore": bool(r.errore)})
                del c.msgs[:-MAX_MSG]
                lav.t1 = time.time()
                lav.fatto = True
            self._salva()

    # ---- lettura per la UI
    def istantanea(self, id: str) -> dict | None:
        with self._lock:
            c = self.chats.get(id)
            if not c:
                return None
            lav = c.lavoro
            r = lav.risposta if lav else None
            return {"id": c.id, "nome": c.nome, "cwd": c.cwd, "agente": c.agente, "parla": c.parla, "sid": c.sid, "msgs": list(c.msgs),
                    "in_corso": c.in_corso, "da_leggere": c.da_leggere, "parlato": c.parlato, "testo": (r.testo if r else ""), "strumenti": list(r.strumenti) if r else [],
                    "errore": (r.errore if r else None), "durata": (lav.durata if lav else 0.0), "fatto": bool(lav and lav.fatto)}

    # ---- persistenza
    def _salva(self) -> None:
        if not self.percorso:
            return
        with self._lock:
            dati = {"chats": [{"id": c.id, "nome": c.nome, "cwd": c.cwd, "agente": c.agente, "sid": c.sid, "parla": c.parla,
                               "msgs": c.msgs[-MAX_MSG:]} for c in self.chats.values()]}
        try:
            self.percorso.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.percorso.with_suffix(".tmp")
            tmp.write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.percorso)
        except OSError:
            pass

    def _carica(self) -> None:
        if not self.percorso:
            return
        try:
            d = json.loads(self.percorso.read_text(encoding="utf-8"))
            for x in d.get("chats", [])[:MAX_CHAT]:
                c = Chat(str(x["id"])[:16], str(x.get("nome", "Chat"))[:40], str(x.get("cwd", "")), x.get("agente") or None, bool(x.get("parla")))
                c.sid = x.get("sid") or None
                c.msgs = [{"ruolo": m["ruolo"], "testo": str(m["testo"])[:MAX_TESTO], "nota": str(m.get("nota", ""))[:300],
                           "errore": bool(m.get("errore"))} for m in x.get("msgs", [])[-MAX_MSG:]
                          if isinstance(m, dict) and m.get("ruolo") in ("user", "assistant")]
                self.chats[c.id] = c
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self.chats = {}
