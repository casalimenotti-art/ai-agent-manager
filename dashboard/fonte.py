"""Interfaccia "Fonte": unico punto da cui la dashboard legge dati ed esegue azioni.

FonteLocale  -> questo PC (psutil + filesystem + subprocess)
FonteRemota  -> agent HTTP su un altro PC (stessi metodi, token Bearer). SCHELETRO NON TESTATO
                contro un agent reale: il protocollo è descritto nella docstring della classe.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Iterator
from urllib.parse import urlparse

import agenti
import chat
import clienti
import config
import monitor
import skill


class Fonte(ABC):
    nome = "?"

    @abstractmethod
    def processi(self) -> dict: ...          # {n, cpu, ram_mb, lista:[{pid,nome,cpu,ram_mb,cmd}]}

    @abstractmethod
    def cpu_totale(self) -> dict: ...        # {cpu, n_core, ram_pct, ram_tot_mb, storico:[[sec_rel, pct_tot, pct_claude]]}

    @abstractmethod
    def sessioni(self) -> list[dict]: ...    # vedi agenti.Indice.sessioni

    @abstractmethod
    def costi(self, giorni: int = 30) -> dict: ...  # vedi agenti.Indice.costi

    @abstractmethod
    def ricavi(self) -> dict: ...            # {"YYYY-MM": importo_usd}

    @abstractmethod
    def imposta_ricavo(self, mese: str, importo: float) -> dict: ...

    @abstractmethod
    def progetti(self) -> list[str]: ...

    @abstractmethod
    def skill_elenco(self) -> list[dict]: ...  # [{nome, descrizione, cartella}]

    @abstractmethod
    def catalogo(self) -> list[dict]: ...    # skill del catalogo verificato + flag "installata"

    @abstractmethod
    def installa_catalogo(self, id_skill: str) -> dict: ...  # {ok, messaggio}

    @abstractmethod
    def squadra(self) -> list[dict]: ...      # agenti Claude Code della squadra + flag "installata"

    @abstractmethod
    def installa_squadra(self) -> dict: ...

    @abstractmethod
    def azienda(self) -> str: ...

    @abstractmethod
    def imposta_azienda(self, testo: str) -> dict: ...

    @abstractmethod
    def clienti(self) -> list[dict]: ...      # lead dai CSV + stato visita

    @abstractmethod
    def imposta_visita(self, slug: str, stato: str, note: str, consenso_foto: bool) -> dict: ...

    @abstractmethod
    def salva_foto(self, slug: str, dati: bytes, consenso: bool) -> dict: ...

    @abstractmethod
    def foto(self, slug: str) -> list[dict]: ...  # [{nome, dati}]

    @abstractmethod
    def scheda_visita(self, slug: str) -> str: ...

    @abstractmethod
    def esegui(self, prompt: str, cwd: str, resume: str | None = None) -> Iterator[dict]: ...  # eventi stream-json

    @abstractmethod
    def installa_skill(self, url: str) -> dict: ...  # {ok, messaggio}


class FonteLocale(Fonte):
    nome = "Questo PC"

    def __init__(self):
        self._camp = monitor.Campionatore()
        self._indice = agenti.Indice()

    def processi(self):
        return self._camp.processi()

    def cpu_totale(self):
        return self._camp.cpu_totale()

    def sessioni(self):
        return self._indice.sessioni()

    def progetti(self):
        return self._indice.progetti()

    def costi(self, giorni=30):
        return self._indice.costi(giorni)

    def ricavi(self):
        return monitor.leggi_ricavi()

    def imposta_ricavo(self, mese, importo):
        return monitor.scrivi_ricavo(mese, importo)

    def skill_elenco(self):
        return skill.elenca_skill()

    def esegui(self, prompt, cwd, resume=None):
        return chat.esegui_locale(prompt, cwd, resume)

    def installa_skill(self, url):
        return skill.installa_locale(url)

    def catalogo(self):
        return skill.catalogo_locale()

    def squadra(self):
        return skill.squadra_locale()

    def clienti(self):
        return clienti.clienti()

    def imposta_visita(self, slug, stato, note, consenso_foto):
        return clienti.imposta_visita(slug, stato, note, consenso_foto)

    def salva_foto(self, slug, dati, consenso):
        return clienti.salva_foto(slug, dati, consenso)

    def foto(self, slug):
        return clienti.foto(slug)

    def scheda_visita(self, slug):
        return clienti.scheda_visita(slug)

    def installa_squadra(self):
        return skill.installa_squadra_locale()

    def azienda(self):
        return skill.leggi_azienda()

    def imposta_azienda(self, testo):
        return skill.scrivi_azienda(testo)

    def installa_catalogo(self, id_skill):
        return skill.installa_catalogo_locale(id_skill)


class FonteRemota(Fonte):
    """Legge un agent HTTP (da scrivere) che espone, con `Authorization: Bearer <token>`:

    GET  /api/processi | /api/cpu | /api/sessioni | /api/progetti | /api/skill | /api/costi?giorni=N | /api/ricavi   -> JSON (stessi formati di Fonte)
    POST /api/chat           {prompt, cwd, resume}  -> NDJSON: un evento stream-json per riga
    POST /api/skill/installa {url}                  -> {ok, messaggio}   (l'agent RI-valida l'URL)
    """

    def __init__(self, url: str, token: str):
        u = urlparse(url)
        locale = u.hostname in ("localhost", "127.0.0.1", "::1")
        if u.scheme != "https" and not (u.scheme == "http" and locale):
            raise ValueError("GUARDIAN_AGENT_URL deve essere https:// (il token viaggia in chiaro con http)")
        if not token:
            raise ValueError("GUARDIAN_TOKEN mancante")
        self.base, self.token = url.rstrip("/"), token
        self.nome = f"Remoto ({u.hostname})"

    def _req(self, path, dati=None, timeout=10):
        req = urllib.request.Request(
            self.base + path, method="POST" if dati is not None else "GET",
            data=json.dumps(dati).encode() if dati is not None else None,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        return urllib.request.urlopen(req, timeout=timeout)

    def _json(self, path):
        with self._req(path) as r:
            return json.load(r)

    def processi(self): return self._json("/api/processi")
    def cpu_totale(self): return self._json("/api/cpu")
    def sessioni(self): return self._json("/api/sessioni")
    def progetti(self): return self._json("/api/progetti")
    def costi(self, giorni=30): return self._json(f"/api/costi?giorni={int(giorni)}")
    def ricavi(self): return self._json("/api/ricavi")

    def imposta_ricavo(self, mese, importo):
        with self._req("/api/ricavi", {"mese": mese, "importo": importo}) as r:
            return json.load(r)
    def skill_elenco(self): return self._json("/api/skill")

    def esegui(self, prompt, cwd, resume=None):
        try:
            with self._req("/api/chat", {"prompt": prompt, "cwd": cwd, "resume": resume}, timeout=config.CHAT_TIMEOUT_S) as r:
                for riga in r:
                    if riga.strip():
                        yield json.loads(riga)
        except (urllib.error.URLError, OSError, ValueError) as e:
            yield {"type": "guardian_end", "returncode": -1, "stderr": f"Agent remoto: {e}"}

    def catalogo(self): return self._json("/api/catalogo")
    def squadra(self): return self._json("/api/squadra")
    def clienti(self): return self._json("/api/clienti")
    def scheda_visita(self, slug): return self._json(f"/api/clienti/{slug}/scheda").get("testo", "")
    def foto(self, slug): return []            # le foto restano sul PC dove sono state scattate

    def salva_foto(self, slug, dati, consenso):
        return {"ok": False, "messaggio": "Le foto si salvano solo sul PC locale."}

    def imposta_visita(self, slug, stato, note, consenso_foto):
        with self._req("/api/clienti/visita", {"slug": slug, "stato": stato, "note": note, "consenso_foto": consenso_foto}) as r:
            return json.load(r)
    def azienda(self): return self._json("/api/azienda")["testo"]

    def installa_squadra(self):
        with self._req("/api/squadra/installa", {}) as r:
            return json.load(r)

    def imposta_azienda(self, testo):
        with self._req("/api/azienda", {"testo": testo}) as r:
            return json.load(r)

    def installa_catalogo(self, id_skill):
        try:
            with self._req("/api/catalogo/installa", {"id": id_skill}, timeout=200) as r:
                return json.load(r)
        except (urllib.error.URLError, OSError, ValueError) as e:
            return {"ok": False, "messaggio": f"Agent remoto: {e}"}

    def installa_skill(self, url):
        try:
            with self._req("/api/skill/installa", {"url": url}, timeout=200) as r:
                return json.load(r)
        except (urllib.error.URLError, OSError, ValueError) as e:
            return {"ok": False, "messaggio": f"Agent remoto: {e}"}


def crea_fonte() -> Fonte:
    if config.SOURCE == "remote":
        return FonteRemota(config.AGENT_URL, config.TOKEN)
    return FonteLocale()
