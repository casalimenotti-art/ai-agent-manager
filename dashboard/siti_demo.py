"""Generatore di siti demo: da un lead (nome, categoria, zona) produce una pagina HTML autonoma.

Regole: nessuna richiesta di rete (niente font/CDN/immagini esterne), tutto il testo variabile è escapato, e NESSUN fatto
inventato sull'attività: orari, telefono, indirizzo e prezzi sono segnaposto "da inserire". Serve a far vedere al titolare
come potrebbe essere il suo sito, non a pubblicare informazioni.
"""
from __future__ import annotations

import html
import re

TEMI = {
    "notte": {"bg": "#0b1020", "fg": "#e8f1ff", "muted": "#9aa6c4", "acc": "#00c8e8", "acc2": "#ff5f45", "card": "#121a33"},
    "caldo": {"bg": "#fff7ec", "fg": "#2a1a12", "muted": "#6e5a4c", "acc": "#c2410c", "acc2": "#7c2d12", "card": "#ffffff"},
    "mare": {"bg": "#f0f9ff", "fg": "#0c2a3a", "muted": "#4b6b7c", "acc": "#0284c7", "acc2": "#0e7490", "card": "#ffffff"},
}

# Contenuti per categoria: titolo del blocco "cosa trovi" e voci; call-to-action.
PACCHETTI = {
    "ristorante": ("Il menù e la sala", ["Menù aggiornato (da inserire)", "Prenota un tavolo online", "Eventi e serate"], "Prenota un tavolo"),
    "b&b": ("Camere e soggiorno", ["Camere e foto (da inserire)", "Disponibilità e prenotazione diretta", "Cosa vedere nei dintorni"], "Controlla le date"),
    "ottica": ("Occhiali e controllo della vista", ["Catalogo montature (da inserire)", "Prova gli occhiali dalla fotocamera", "Prenota un controllo della vista"], "Prenota un controllo"),
    "parrucchiere": ("Servizi e appuntamenti", ["Servizi e listino (da inserire)", "Prenota online", "Prima e dopo"], "Prenota un appuntamento"),
    "officina": ("Servizi e preventivi", ["Servizi di officina (da inserire)", "Richiedi un preventivo", "Orari e come arrivare"], "Richiedi un preventivo"),
    "studio": ("Aree di attività", ["Aree di attività (da inserire)", "Chi siamo", "Richiedi un primo contatto"], "Contattaci"),
}
GENERICO = ("Cosa offriamo", ["Servizi (da inserire)", "Contatti e orari", "Come raggiungerci"], "Contattaci")


def categoria_chiave(cat: str) -> str:
    c = (cat or "").lower()
    for k, alias in (("ristorante", ("ristor", "trattor", "bar", "pizz")), ("b&b", ("b&b", "bed", "casa vacanz", "affitt")),
                     ("ottica", ("ottic", "occhial")), ("parrucchiere", ("parrucch", "estetic", "barbier")),
                     ("officina", ("offic", "autoripar", "gommist")), ("studio", ("studio", "profession", "avvoc", "commercial"))):
        if any(a in c for a in alias):
            return k
    return "generico"


def _e(x) -> str:
    return html.escape(str(x or ""), quote=True)


def genera_sito(nome: str, categoria: str, zona: str, tema: str = "notte", opportunita: str = "") -> str:
    t = TEMI.get(tema, TEMI["notte"])
    chiave = categoria_chiave(categoria)
    titolo, voci, cta = PACCHETTI.get(chiave, GENERICO)
    nome_s = (nome or "La tua attività").strip()[:80]
    zona_s = (zona or "Cagliari").strip()[:60]
    voci_html = "".join(f"<li>{_e(v)}</li>" for v in voci)
    prova = ""
    if chiave == "ottica":
        prova = ("<section class='box'><h2>Provali da casa</h2><p>Con la fotocamera del telefono vedi la tua faccia con le montature, "
                 "senza inviare foto a nessuno: l'elaborazione avviene sul tuo dispositivo.</p>"
                 "<p class='note'>Nel sito vero è una funzione da attivare con modelli 3D delle montature.</p></section>")
    extra = f"<p class='note'>Opportunità individuata: {_e(opportunita)}</p>" if opportunita else ""
    css = (":root{--bg:%(bg)s;--fg:%(fg)s;--muted:%(muted)s;--acc:%(acc)s;--acc2:%(acc2)s;--card:%(card)s}"
           "*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--fg);"
           "font:16px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}"
           "header{padding:20px 6vw;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}"
           ".logo{font-weight:800;letter-spacing:.04em}nav a{color:var(--muted);margin-left:18px;text-decoration:none}"
           "nav a:hover,nav a:focus-visible{color:var(--acc)}"
           ".hero{padding:9vh 6vw 8vh;max-width:1100px;margin:auto}"
           ".hero h1{font-size:clamp(34px,6vw,64px);line-height:1.05;margin:0 0 14px;"
           "background:linear-gradient(90deg,var(--acc),var(--acc2));-webkit-background-clip:text;background-clip:text;color:transparent}"
           ".hero p{color:var(--muted);max-width:56ch;font-size:1.15rem}"
           ".btn{display:inline-block;margin-top:20px;padding:14px 26px;border-radius:999px;background:var(--acc);color:#fff;"
           "font-weight:700;text-decoration:none;transition:transform .15s,box-shadow .15s}"
           ".btn:hover,.btn:focus-visible{transform:translateY(-2px);box-shadow:0 10px 30px rgba(0,0,0,.25)}"
           ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;padding:0 6vw 6vh;max-width:1100px;margin:auto}"
           ".box{background:var(--card);border-radius:18px;padding:22px;margin:0 auto;max-width:1100px}"
           ".grid .box{margin:0}.box h2{margin:0 0 10px;font-size:1.15rem}ul{padding-left:18px;margin:0}li{margin:6px 0}"
           ".sez{max-width:1100px;margin:auto;padding:0 6vw 6vh}.sez h2{font-size:1.6rem}"
           ".note{color:var(--muted);font-size:.9rem}footer{padding:28px 6vw;color:var(--muted);border-top:1px solid rgba(128,128,128,.25)}"
           ".reveal{animation:r .7s ease both}@keyframes r{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}"
           "@media (prefers-reduced-motion:reduce){.reveal{animation:none}html{scroll-behavior:auto}.btn{transition:none}}") % t
    return (
        "<!doctype html><html lang='it'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{_e(nome_s)} · {_e(zona_s)}</title>"
        f"<meta name='description' content='{_e(nome_s)}, {_e(categoria)} a {_e(zona_s)}. Sito dimostrativo.'>"
        f"<style>{css}</style></head><body>"
        f"<header><div class='logo'>{_e(nome_s)}</div><nav><a href='#cosa'>{_e(titolo)}</a><a href='#contatti'>Contatti</a></nav></header>"
        f"<section class='hero reveal'><h1>{_e(nome_s)}</h1><p>{_e(categoria or 'Attività locale')} a {_e(zona_s)}. "
        f"Un sito pensato per farti trovare e farti scegliere dal telefono.</p><a class='btn' href='#contatti'>{_e(cta)}</a></section>"
        f"<section id='cosa' class='sez'><h2>{_e(titolo)}</h2><div class='grid' style='padding:0'>"
        + "".join(f"<div class='box'><h2>{_e(v)}</h2><p class='note'>Contenuto da personalizzare con l'attività.</p></div>" for v in voci)
        + f"</div></section>{prova}"
        f"<section id='contatti' class='sez'><h2>Contatti</h2><div class='box'><ul><li>Indirizzo: da inserire</li><li>Telefono: da inserire</li>"
        f"<li>Orari: da inserire</li></ul>{extra}</div></section>"
        "<footer>Sito dimostrativo: nessuna informazione reale. Testi, orari e contatti vanno confermati con il titolare.</footer>"
        "</body></html>"
    )


def slug_file(nome: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (nome or "").lower()).strip("-")[:60] or "sito"
