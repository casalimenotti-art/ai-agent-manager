"""Clienti: legge i lead (CSV) prodotti dagli agenti e tiene stato, note e foto delle visite di persona."""
from __future__ import annotations

import csv
import io
import json
import re
import time
from pathlib import Path

import config

STATI = ("da visitare", "visitato", "interessato", "richiamare", "no")
_SLUG = re.compile(r"^[a-z0-9-]{1,80}$")
MAX_NOTE, MAX_FOTO_BYTES, MAX_FOTO_PER_LEAD = 2000, 10 * 1024 * 1024, 40
_CHIAVI = {"azienda": "azienda", "nome": "azienda", "categoria": "categoria", "settore": "categoria", "zona": "zona",
           "contatto_pubblico": "contatto", "contatto": "contatto", "prova": "prova", "fonte_url": "fonte",
           "fonte": "fonte", "adattamento": "adattamento", "motivo": "motivo", "da_verificare": "da_verificare",
           "opportunita_principale": "opportunita"}


def slug(nome: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (nome or "").lower()).strip("-")[:80] or "senza-nome"


def url_sicuro(u: str) -> str:
    """Solo http/https: niente javascript:, data: ecc. nei link mostrati."""
    u = (u or "").strip()
    return u if re.match(r"^https?://[^\s<>\"']+$", u) else ""


def _righe_csv(testo: str) -> list[dict]:
    testo = testo.lstrip("﻿")
    try:
        dialetto = csv.Sniffer().sniff(testo[:2000], delimiters=",;\t")
    except csv.Error:
        dialetto = csv.excel
    out = []
    for r in csv.DictReader(io.StringIO(testo), dialect=dialetto):
        riga = {}
        for k, v in r.items():
            chiave = _CHIAVI.get((k or "").strip().lower().split("(")[0].strip())
            if chiave and v:
                riga[chiave] = v.strip()
        if riga.get("azienda"):
            out.append(riga)
    return out


def leggi_leads(leads_dir: Path = None) -> list[dict]:
    base = leads_dir or config.LEADS_DIR
    visti: dict[str, dict] = {}
    for f in sorted(base.glob("*.csv")) if base.is_dir() else []:
        try:
            righe = _righe_csv(f.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        for r in righe:
            s = slug(r["azienda"])
            try:
                r["adattamento"] = max(0, min(5, int(float(r.get("adattamento", 0) or 0))))
            except ValueError:
                r["adattamento"] = 0
            r["slug"], r["file"] = s, f.name
            if s not in visti or r["adattamento"] > visti[s]["adattamento"]:   # doppioni: tieni il migliore
                visti[s] = r
    return sorted(visti.values(), key=lambda r: (-r["adattamento"], r["azienda"].lower()))


def _file_stati(dir_: Path) -> Path:
    return dir_ / "visite.json"


def leggi_stati(dir_: Path = None) -> dict:
    try:
        d = json.loads(_file_stati(dir_ or config.VISITE_DIR).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def clienti(leads_dir: Path = None, dir_: Path = None) -> list[dict]:
    stati = leggi_stati(dir_)
    out = []
    for r in leggi_leads(leads_dir):
        s = stati.get(r["slug"], {})
        out.append({**r, "stato": s.get("stato", "da visitare"), "note": s.get("note", ""),
                    "consenso_foto": bool(s.get("consenso_foto", False)), "aggiornato": s.get("aggiornato", 0)})
    return out


def imposta_visita(s: str, stato: str, note: str, consenso_foto: bool, dir_: Path = None) -> dict:
    if not _SLUG.match(s or ""):
        return {"ok": False, "messaggio": "Cliente non valido."}
    if stato not in STATI:
        return {"ok": False, "messaggio": "Stato non valido."}
    if not isinstance(note, str) or len(note) > MAX_NOTE:
        return {"ok": False, "messaggio": f"Note troppo lunghe (max {MAX_NOTE} caratteri)."}
    d = dir_ or config.VISITE_DIR
    dati = leggi_stati(d)
    dati[s] = {"stato": stato, "note": note, "consenso_foto": bool(consenso_foto), "aggiornato": time.time()}
    d.mkdir(parents=True, exist_ok=True)
    tmp = _file_stati(d).with_suffix(".tmp")
    tmp.write_text(json.dumps(dati, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(_file_stati(d))
    return {"ok": True, "messaggio": "Salvato."}


_MAGIC = {b"\xff\xd8\xff": "jpg", b"\x89PNG\r\n\x1a\n": "png", b"RIFF": "webp"}


def _tipo_immagine(dati: bytes) -> str | None:
    for m, ext in _MAGIC.items():
        if dati.startswith(m) and (ext != "webp" or dati[8:12] == b"WEBP"):
            return ext
    return None


def salva_foto(s: str, dati: bytes, consenso: bool, dir_: Path = None) -> dict:
    """Salva una foto solo se: cliente valido, consenso del titolare dichiarato, vera immagine (non solo l'estensione)."""
    if not _SLUG.match(s or ""):
        return {"ok": False, "messaggio": "Cliente non valido."}
    if not consenso:
        return {"ok": False, "messaggio": "Spunta il consenso del titolare prima di salvare foto."}
    if not isinstance(dati, (bytes, bytearray)) or not dati or len(dati) > MAX_FOTO_BYTES:
        return {"ok": False, "messaggio": "Foto vuota o troppo grande (max 10 MB)."}
    ext = _tipo_immagine(bytes(dati))
    if not ext:
        return {"ok": False, "messaggio": "Formato non valido: solo JPG, PNG o WEBP."}
    cartella = (dir_ or config.VISITE_DIR) / "foto" / s
    cartella.mkdir(parents=True, exist_ok=True)
    if len(list(cartella.iterdir())) >= MAX_FOTO_PER_LEAD:
        return {"ok": False, "messaggio": f"Troppe foto per questo cliente (max {MAX_FOTO_PER_LEAD})."}
    nome = f"{time.strftime('%Y%m%d-%H%M%S')}-{len(list(cartella.iterdir())):02d}.{ext}"
    (cartella / nome).write_bytes(bytes(dati))
    return {"ok": True, "messaggio": f"Foto salvata ({nome})."}


def foto(s: str, dir_: Path = None, massimo: int = 6) -> list[dict]:
    if not _SLUG.match(s or ""):
        return []
    cartella = (dir_ or config.VISITE_DIR) / "foto" / s
    if not cartella.is_dir():
        return []
    files = sorted(cartella.iterdir(), reverse=True)[:massimo]
    return [{"nome": f.name, "dati": f.read_bytes()} for f in files if f.is_file() and f.suffix in (".jpg", ".png", ".webp")]


def scheda_visita(s: str, base: Path = None) -> str:
    """Scheda scritta dal compilatore-schede-visita (testo dell'agente: da mostrare come dato, mai come HTML)."""
    if not _SLUG.match(s or ""):
        return ""
    p = (base or config.LEADS_DIR.parent) / "visite" / f"{s}.md"
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:20000]
    except OSError:
        return ""
