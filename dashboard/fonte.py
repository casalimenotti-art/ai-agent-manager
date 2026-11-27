"""Interfaccia "Fonte": unico punto da cui la dashboard legge dati ed esegue azioni.

FonteLocale  -> questo PC (psutil + filesystem + subprocess)
FonteRemota  -> agent HTTP su un altro PC (stessi metodi, token Bearer). SCHELETRO NON TESTATO
                contro un agent reale: il protocollo è descritto nella docstring della classe.
"""
from __future__ import annotations

import json
import math
import random
import time
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
    def attivita(self, limite: int = 80, tipi: set | None = None) -> list[dict]: ...  # cosa fanno gli agenti (feed)

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
    def esegui(self, prompt: str, cwd: str, resume: str | None = None, agente: str | None = None, ctrl: dict | None = None) -> Iterator[dict]: ...  # eventi stream-json

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

    def attivita(self, limite=80, tipi=None):
        return self._indice.attivita(limite, tipi=tipi)

    def ricavi(self):
        return monitor.leggi_ricavi()

    def imposta_ricavo(self, mese, importo):
        return monitor.scrivi_ricavo(mese, importo)

    def skill_elenco(self):
        return skill.elenca_skill()

    def esegui(self, prompt, cwd, resume=None, agente=None, ctrl=None):
        return chat.esegui_locale(prompt, cwd, resume, agente, ctrl)

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
    def attivita(self, limite=80, tipi=None): return self._json(f"/api/attivita?limite={int(limite)}")
    def ricavi(self): return self._json("/api/ricavi")

    def imposta_ricavo(self, mese, importo):
        with self._req("/api/ricavi", {"mese": mese, "importo": importo}) as r:
            return json.load(r)
    def skill_elenco(self): return self._json("/api/skill")

    def esegui(self, prompt, cwd, resume=None, agente=None, ctrl=None):
        try:
            with self._req("/api/chat", {"prompt": prompt, "cwd": cwd, "resume": resume, "agente": agente}, timeout=config.CHAT_TIMEOUT_S) as r:
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


class FonteDemo(FonteLocale):
    """Dati FINTI per mostrare Guardian a soci e clienti senza esporre i progetti veri.

    Tutto ciò che scrive o esegue è disattivato: niente chat, installazioni, foto, profilo azienda.
    """
    nome = "DEMO · dati finti"
    _OFF = {"ok": False, "messaggio": "Disattivato in modalità demo."}

    def __init__(self):
        super().__init__()
        self._visite: dict[str, dict] = {}
        self._ricavi = {time.strftime("%Y-%m"): 3200.0}

    def processi(self):
        t = time.time()
        lista = [{"pid": 1000 + i, "nome": "claude", "cpu": round(max(0.0, 6 + 5 * math.sin(t / (7 + i)) + i), 1),
                  "ram_mb": 280 + 40 * i, "cmd": f"claude --agent demo-{i}"} for i in range(3)]
        return {"n": 3, "cpu": round(sum(x["cpu"] for x in lista), 1), "ram_mb": sum(x["ram_mb"] for x in lista), "lista": lista}

    def cpu_totale(self):
        t = time.time()
        storico = []
        for k in range(120, -1, -1):
            x = t - k
            tot = 30 + 18 * math.sin(x / 9) + 7 * math.sin(x / 2.3)
            storico.append([-k, round(max(2, min(95, tot)), 1), round(max(0.5, 6 + 3 * math.sin(x / 7)), 1)])
        return {"cpu": storico[-1][1], "n_core": 8, "ram_pct": 41.0, "ram_tot_mb": 16384, "storico": storico}

    def sessioni(self):
        t = time.time()
        base = [("sito-ottico", "sessione", "", "Edit", "Aggiorno la pagina del catalogo occhiali", 4),
                ("sito-ottico", "subagente", "a1b2c3d", "WebSearch", "Cerco esempi di prova virtuale occhiali", 9),
                ("ricerca-clienti", "subagente", "e4f5a6b", "WebFetch", "Verifico il sito di un ristorante", 30),
                ("dashboard", "sessione", "", "Bash", "Eseguo i test della dashboard", 400)]
        return [{"progetto": p, "cwd": f"/demo/{p}", "sessione": f"demo-{i}", "tipo": ty, "agente": ag, "padre": "demo-0" if ag else "",
                 "stato": "al lavoro" if eta < 120 else "fermo", "strumento": tool, "messaggio": msg,
                 "ultimo_agg": t - eta, "fonte": "demo", "token_in": 90 + 10 * i, "token_out": 14000 + 900 * i,
                 "cache_read": 600000 + 40000 * i, "cache_write": 30000, "costo": round(0.8 + 0.45 * i, 4),
                 "modello": "claude-sonnet-5-5"} for i, (p, ty, ag, tool, msg, eta) in enumerate(base)]

    def costi(self, giorni=30):
        rnd = random.Random(7)
        oggi = time.time()
        serie = []
        for k in range(giorni - 1, -1, -1):
            d = time.strftime("%Y-%m-%d", time.localtime(oggi - k * 86400))
            c = 0.0 if rnd.random() < 0.2 else round(rnd.uniform(0.8, 6.5), 4)
            serie.append({"data": d, "costo": c, "token_in": int(c * 40), "token_out": int(c * 9000), "cache": int(c * 700000),
                          "msgs": int(c * 14), "tools": int(c * 22), "edits": int(c * 4)})
        mese = sum(x["costo"] for x in serie[-time.localtime().tm_mday:])
        media7 = sum(x["costo"] for x in serie[-7:]) / 7
        return {"giorni": serie, "progetti": [{"progetto": "sito-ottico", "costo": 31.2}, {"progetto": "ricerca-clienti", "costo": 18.4},
                                              {"progetto": "dashboard", "costo": 12.9}],
                "modelli": [{"modello": "claude-sonnet-5-5", "costo": 44.0}, {"modello": "claude-opus-5-5", "costo": 18.5}],
                "ultime_5h": 2.1, "burn_orario": 0.42, "ore": {}, "oggi": serie[-1]["costo"], "ultimi7": round(media7 * 7, 4),
                "ultimi30": round(sum(x["costo"] for x in serie[-30:]), 4), "mese": round(mese, 4), "media7": round(media7, 4),
                "proiezione_mese": round(mese + media7 * 10, 4), "mese_id": time.strftime("%Y-%m")}

    def attivita(self, limite=80, tipi=None):
        t = time.time()
        passi = [
            ("delega", "guardian-manager", "cacciatore-clienti: ristoranti Cagliari", "", "Trova 10 ristoranti di Cagliari senza sito, con prova", "ok: 9 lead"),
            ("web-ricerca", "cacciatore-clienti", "ristoranti Cagliari senza sito web", "", "", "12 risultati: elenchi di directory e pagine social"),
            ("web-apri", "cacciatore-clienti", "c'è un sito proprio?", "https://example.com/trattoria-demo", "", "Solo una pagina Facebook, nessun sito"),
            ("delega", "guardian-manager", "analista-presenza-online: ESEMPIO Trattoria", "", "Audit con prove di sito, scheda Google, prenotazioni", ""),
            ("browser", "analista-presenza-online", "", "https://example.com/trattoria-demo/menu", "", "Menu in PDF, non leggibile dal telefono"),
            ("file", "analista-presenza-online", "audit/esempio-trattoria.md", "", "", ""),
            ("dice", "scopritore-problemi", "Trovato: prenotazioni solo al telefono e martedì vuoto: chatbot + offerta nel giorno debole", "", "", ""),
            ("file", "compilatore-schede-visita", "visite/esempio-trattoria.md", "", "", ""),
        ]
        out = [{"ts": t - 3 * (len(passi) - i), "tipo": ty, "strumento": "", "testo": tx, "url": u, "brief": b, "risultato": r,
                "chi": f"demo · {chi}", "sidechain": chi != "guardian-manager", "sessione": "demo"}
               for i, (ty, chi, tx, u, b, r) in enumerate(passi)]
        out = [e for e in out if not tipi or e["tipo"] in tipi]
        return sorted(out, key=lambda e: e["ts"], reverse=True)[:limite]

    def clienti(self):
        demo = [("ESEMPIO Trattoria", "ristorante", "Cagliari", 5, "Solo pagina Facebook, nessun sito", "prenotazioni online + offerta nei giorni deboli"),
                ("ESEMPIO Ottica", "ottica", "Cagliari", 5, "Sito non adatto al telefono", "catalogo con prova virtuale degli occhiali"),
                ("ESEMPIO B&B", "B&B", "Quartu S.E.", 4, "Prenotazioni solo al telefono", "sito immediato con prenotazione"),
                ("ESEMPIO Parrucchiere", "parrucchiere", "Selargius", 4, "Recensioni senza risposta", "prenotazioni + promemoria"),
                ("ESEMPIO Officina", "officina", "Elmas", 3, "Nessun sito, orari incoerenti", "sito vetrina"),
                ("ESEMPIO Studio", "studio", "Cagliari", 2, "Non verificato", "da verificare")]
        out = []
        for n, cat, z, fit, prova, opp in demo:
            s = clienti.slug(n)
            v = self._visite.get(s, {})
            out.append({"azienda": n, "categoria": cat, "zona": z, "contatto": "non pubblico", "prova": prova, "fonte": "",
                        "adattamento": fit, "motivo": prova, "da_verificare": "sì" if fit < 3 else "no", "opportunita": opp,
                        "slug": s, "file": "demo.csv", "stato": v.get("stato", "da visitare"), "note": v.get("note", ""),
                        "consenso_foto": False, "aggiornato": 0})
        return out

    def imposta_visita(self, slug, stato, note, consenso_foto):
        if stato not in clienti.STATI:
            return {"ok": False, "messaggio": "Stato non valido."}
        self._visite[slug] = {"stato": stato, "note": note[:200]}
        return {"ok": True, "messaggio": "Salvato (solo in memoria, demo)."}

    def salva_foto(self, slug, dati, consenso): return dict(self._OFF)
    def foto(self, slug): return []
    def scheda_visita(self, slug): return ""
    def ricavi(self): return dict(self._ricavi)

    def imposta_ricavo(self, mese, importo):
        self._ricavi[mese] = float(importo)
        return dict(self._ricavi)

    def progetti(self): return ["/demo/sito-ottico", "/demo/ricerca-clienti"]
    def installa_skill(self, url): return dict(self._OFF)
    def installa_catalogo(self, id_skill): return dict(self._OFF)
    def installa_squadra(self): return dict(self._OFF)
    def imposta_azienda(self, testo): return dict(self._OFF)
    def azienda(self): return "Profilo azienda (esempio): siti web immediati e software su misura a Cagliari."

    def esegui(self, prompt, cwd, resume=None, agente=None, ctrl=None):
        yield {"type": "guardian_end", "returncode": -1, "stderr": "La chat è disattivata in modalità demo."}


def crea_fonte() -> Fonte:
    if config.SOURCE == "demo":
        return FonteDemo()
    if config.SOURCE == "remote":
        return FonteRemota(config.AGENT_URL, config.TOKEN)
    return FonteLocale()
