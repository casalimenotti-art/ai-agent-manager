"""Tema cyberpunk-minimal di Guardian: CSS, componenti HTML e grafico CPU.

Colori dei DATI (grafico) validati con validate_palette.js (dark, superficie #080a12):
ciano #00aed1 + arancio #ff5f45 -> lightness, chroma, CVD ΔE 20.5, contrasto: tutti PASS.
I neon più accesi (#00f0ff, #ff2bd6) sono usati solo per decorazioni, mai per codificare dati.
Nessun font/risorsa esterna: tutto è locale.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

SURFACE = "#080a12"
SERIE_TOT, SERIE_CLAUDE = "#00aed1", "#ff5f45"
INK, INK2 = "#e8f1ff", "#8b97b3"

CSS = f"""
<style>
:root {{
  --bg:{SURFACE}; --panel:#0d1020; --line:#1c2340; --ink:{INK}; --ink2:{INK2};
  --cy:#00f0ff; --mg:#ff2bd6; --ok:#3dffa0; --warn:#ffd23d;
  --mono: ui-monospace,"JetBrains Mono","SF Mono","Cascadia Code",Menlo,Consolas,monospace;
}}
html {{ color-scheme:dark; }}
html, body, .stApp {{ background:var(--bg) !important; color:var(--ink); font-family:var(--sans); }}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stToolbar"], #MainMenu, footer {{ visibility:hidden; }}
.block-container {{ padding-top:2rem; max-width:1380px; }}
h1,h2,h3,h4,p,span,label,div {{ font-family:var(--sans); }}
h3, h4 {{ text-transform:uppercase; letter-spacing:.08em; font-size:.78rem !important; color:var(--ink2);
  font-weight:600 !important; margin-top:.4rem; }}
hr {{ border-color:var(--line) !important; }}
a {{ color:var(--cy); }}

/* header */
.g-head {{ display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap;
  border-bottom:1px solid var(--line); padding-bottom:.9rem; margin-bottom:.4rem; }}
.g-logo {{ font-size:2.1rem; font-weight:800; letter-spacing:.2em; line-height:1; color:var(--ink); }}
.g-logo b {{ color:var(--cy); }}
.g-tag {{ color:var(--ink2); font-size:.72rem; letter-spacing:.28em; margin-top:.55rem; text-transform:uppercase; }}
.g-chips {{ display:flex; gap:.5rem; flex-wrap:wrap; }}
.g-chip {{ border:1px solid var(--line); color:var(--ink2); padding:.28rem .65rem; font-size:.7rem;
  letter-spacing:.14em; text-transform:uppercase; background:rgba(13,16,32,.7); }}
.g-chip i, .pill i {{ display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--ok);
  margin-right:.45rem; vertical-align:middle; }}

/* tabs */
[data-baseweb="tab-list"] {{ gap:.4rem; border-bottom:1px solid var(--line); }}
button[data-baseweb="tab"] {{ background:transparent; color:var(--ink2); letter-spacing:.16em; text-transform:uppercase;
  font-size:.75rem; padding:.7rem 1rem; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color:var(--cy); }}
[data-baseweb="tab-highlight"] {{ background:var(--cy) !important; height:2px; }}
[data-baseweb="tab-border"] {{ background:transparent; }}

/* cards */
.g-card {{ position:relative; border:1px solid var(--line); padding:var(--pad,1.1rem); margin-bottom:var(--gap,1rem); min-height:6.1rem; }}
.g-label {{ font-size:.72rem; letter-spacing:.1em; text-transform:uppercase; color:var(--ink2); }}
.g-value {{ font-family:var(--mono); font-size:2rem; font-weight:700; color:var(--ink); margin-top:.3rem; line-height:1.1;
  font-variant-numeric:tabular-nums; }}
.g-value small {{ font-size:.85rem; color:var(--ink2); margin-left:.25rem; font-weight:500; }}
.g-sub {{ font-size:.7rem; color:var(--ink2); margin-top:.35rem; }}
.g-gauge {{ height:3px; background:#151b34; margin-top:.55rem; }}
.g-gauge i {{ display:block; height:100%; background:var(--cy); }}
.g-skill {{ min-height:8.2rem; }}
.g-skill .g-name {{ color:var(--cy); font-weight:700; letter-spacing:.06em; }}
.g-skill .g-desc {{ color:var(--ink2); font-size:.78rem; margin-top:.45rem; line-height:1.45; }}
.g-skill:hover {{ border-color:var(--cy); }}

/* tabella agenti */
.g-table {{ width:100%; border-collapse:collapse; font-size:.78rem; }}
.g-table th {{ text-align:left; color:var(--ink2); font-weight:500; font-size:.65rem; letter-spacing:.08em;
  text-transform:uppercase; padding:.55rem .7rem; border-bottom:1px solid var(--line); }}
.g-table td {{ padding:.65rem .7rem; border-bottom:1px solid rgba(28,35,64,.6); color:var(--ink); vertical-align:middle; }}
.g-table tr:hover td {{ background:rgba(0,240,255,.04); }}
.g-table td.msg {{ max-width:420px; overflow-wrap:anywhere; color:var(--ink2); }}
.g-table td.num {{ text-align:right; font-family:var(--mono); font-variant-numeric:tabular-nums; }}
.g-wrap {{ border:1px solid var(--line); overflow-x:auto; }}
.pill {{ display:inline-block; padding:.18rem .6rem; font-size:.66rem; letter-spacing:.16em; border:1px solid; white-space:nowrap; }}
.pill.on {{ color:var(--ok); border-color:rgba(61,255,160,.5); background:rgba(61,255,160,.07); }}
.pill.off {{ color:var(--ink2); border-color:var(--line); }}
.pill.off i {{ background:#4a5578; box-shadow:none; }}
.tool {{ color:var(--warn); }}

/* widget */
.stButton > button, .stFormSubmitButton > button {{ background:transparent; color:var(--cy); border:1px solid var(--line);
  border-radius:12px; letter-spacing:.08em; text-transform:uppercase; font-size:.72rem; font-family:var(--sans);
  transition:border-color .15s; }}
.stButton > button:hover, .stFormSubmitButton > button:hover {{ border-color:var(--cy); color:var(--ink); }}
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {{ background:rgba(13,16,32,.9) !important;
  border-radius:0 !important; border:1px solid var(--line) !important; }}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"]:focus-within > div {{
  border-color:var(--cy) !important; box-shadow:none !important; }}
input, textarea {{ color:var(--ink) !important; font-family:var(--sans) !important; }}
[data-testid="stForm"] {{ border:1px solid var(--line); border-radius:0; background:rgba(13,16,32,.55); }}
[data-testid="stExpander"] {{ border:1px solid var(--line); border-radius:0; background:rgba(13,16,32,.55); }}
[data-testid="stChatMessage"] {{ background:rgba(13,16,32,.7); border:1px solid var(--line); border-left:2px solid var(--cy);
  border-radius:0; }}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{ border-left-color:var(--mg); }}
[data-testid="stChatInput"] {{ border-radius:0; background:rgba(13,16,32,.95); border:1px solid rgba(0,240,255,.35); }}
[data-testid="stCaptionContainer"], .stCaption {{ color:var(--ink2); }}
code {{ color:var(--cy); background:rgba(0,240,255,.08); }}

/* fix: sfondi widget (Streamlit usa un grigio caldo di default) */
[data-baseweb="base-input"], [data-baseweb="base-input"] input, [data-baseweb="base-input"] textarea,
[data-baseweb="select"] > div, [data-baseweb="select"] div[value], [data-testid="stChatInput"] > div,
[data-testid="stChatInput"] textarea, [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
  background-color:#0d1020 !important; color:var(--ink) !important; }}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {{ background:#0d1020 !important; border:1px solid var(--line); }}
[data-baseweb="menu"] li:hover, [data-baseweb="menu"] [aria-selected="true"] {{ background:rgba(0,240,255,.12) !important; }}
[data-testid="stChatInput"] button {{ background:transparent !important; color:var(--cy) !important; }}
button[data-baseweb="tab"][aria-selected="true"], button[data-baseweb="tab"][aria-selected="true"] * {{ color:var(--cy) !important; }}
[data-testid^="stChatMessageAvatar"] {{ background:#0d1020 !important; border:1px solid var(--line); border-radius:0 !important; color:var(--cy) !important; }}
[data-testid^="stChatMessageAvatar"] svg {{ color:var(--cy); fill:var(--cy); }}
[data-testid="stCaptionContainer"], .stCaption, .stCaption p {{ color:#a3aecb !important; }}
[data-testid="stElementToolbar"], .vega-embed summary, .vega-embed .vega-actions, .vega-embed details {{ display:none !important; }}
.g-table {{ margin:0 !important; }} .g-table tr {{ border:0; }}
.g-wrap table, .g-wrap td, .g-wrap th {{ border-left:0; border-right:0; border-top:0; }}
.g-legend {{ display:flex; gap:1.4rem; margin:.1rem 0 .4rem; font-size:.74rem; color:var(--ink); }}
.g-leg i {{ display:inline-block; width:18px; height:3px; margin-right:.5rem; vertical-align:middle; }}
.g-bar {{ display:grid; grid-template-columns:minmax(80px,170px) 1fr 70px; gap:.6rem; align-items:center; font-size:.76rem; margin:.45rem 0; }}
.g-bar .n {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--ink); }}
.g-bar .b {{ height:6px; background:#151b34; }} .g-bar .b i {{ display:block; height:100%; background:{SERIE_TOT}; }}
.g-bar .v {{ text-align:right; color:var(--ink2); font-variant-numeric:tabular-nums; }}
.risk.ok {{ color:var(--ok); }} .risk.mid {{ color:var(--warn); }}
:focus-visible {{ outline:2px solid var(--cy) !important; outline-offset:2px; }}
.g-dot {{ animation:g-pulse 1.8s ease-in-out infinite; }}
@keyframes g-pulse {{ 50% {{ opacity:.45; }} }}
@media (prefers-reduced-motion: reduce) {{ .g-dot, .pill.on i {{ animation:none; }} }}
@media (max-width: 700px) {{ .g-logo {{ font-size:1.5rem; letter-spacing:.12em; }} .g-value {{ font-size:1.5rem; }} }}
</style>
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


_LOGO_CLASSI = (('class="a"', 'class="lg-a"'), ('class="b"', 'class="lg-b"'), ('class="c"', 'class="lg-c"'),
                ('<circle cx="64" cy="64" r="48"', '<circle class="lg-d" cx="64" cy="64" r="48"'),
                ('<path d="M64 20', '<path class="lg-t" d="M64 20'),
                ('<circle cx="64" cy="64" r="24"', '<circle class="lg-i" cx="64" cy="64" r="24"'))
_LOGO_CACHE: dict = {}


def logo_svg(stato: str = "riposo", px: int = 56) -> str:
    """Logo animato inline (assets/logo/guardian-mark.svg): lo stato (riposo/ascolto/pensa/parla) è una classe sul contenitore.
    Il file è nostro; si tolgono il suo <style> e il titolo, le animazioni stanno in CSS_PLANCIA. Se manca il file: stringa vuota."""
    if stato not in ("riposo", "ascolto", "pensa", "parla"):
        stato = "riposo"
    if "svg" not in _LOGO_CACHE:
        try:
            t = (Path(__file__).resolve().parent / "assets" / "logo" / "guardian-mark.svg").read_text(encoding="utf-8")
            t = re.sub(r"<style>.*?</style>", "", t, flags=re.S)
            for a, b in _LOGO_CLASSI:
                t = t.replace(a, b)
            t = re.sub(r'\s+role="img" aria-labelledby="t"', ' aria-hidden="true" focusable="false"', t)
            t = re.sub(r"<title.*?</title>", "", t, flags=re.S)
            _LOGO_CACHE["svg"] = " ".join(t.split())
        except OSError:
            _LOGO_CACHE["svg"] = ""
    return f"<span class='g-logomark {stato}' style='width:{int(px)}px;height:{int(px)}px'>{_LOGO_CACHE['svg']}</span>"


def intestazione(sorgente: str, permessi: str, ogni_s: int) -> str:
    return (
        f"<div class='g-head'><div class='g-head-logo'>{logo_svg('riposo', 66)}<div><div class='g-logo'>GUARD<b>I</b>AN</div>"
        "<div class='g-tag'>AI Control Room</div></div></div>"
        "<div class='g-chips'>"
        f"<span class='g-chip'><i></i>link: {esc(sorgente)}</span>"
        f"<span class='g-chip'>refresh {ogni_s}s</span>"
        f"<span class='g-chip'>permessi: {esc(permessi)}</span></div></div>"
    )


def metrica(label: str, valore: str, unita: str = "", sub: str = "", pct: float | None = None) -> str:
    gauge = f"<div class='g-gauge'><i style='width:{max(0, min(100, pct)):.0f}%'></i></div>" if pct is not None else ""
    u = f"<small>{esc(unita)}</small>" if unita else ""
    s = f"<div class='g-sub'>{esc(sub)}</div>" if sub else ""
    return f"<div class='g-card'><div class='g-label'>{esc(label)}</div><div class='g-value'>{esc(valore)}{u}</div>{gauge}{s}</div>"


ETICHETTA_ORIGINE = {"installata": "installata", "account": "dal tuo account", "plugin": "plugin"}


def card_skill(nome: str, descrizione: str, origine: str = "installata", slug: str = "") -> str:
    sl = f"<div class='g-sub'><code>{esc(slug)}</code></div>" if slug else ""
    return (f"<div class='g-card g-skill'><div class='g-name'>{esc(nome)}</div>{sl}{_desc_3righe(descrizione)}"
            f"<div class='g-sub'>{esc(ETICHETTA_ORIGINE.get(origine, origine))}</div></div>")


def _desc_3righe(testo: str) -> str:
    """Descrizione troncata a 3 righe (CSS); se lunga, «mostra tutto» la espande (details, nessuno script)."""
    if len(testo or "") < 150:
        return f"<div class='g-desc' title='{esc(testo)}'>{esc(testo)}</div>"
    return f"<details class='g-more'><summary class='g-desc' title='{esc(testo)}'>{esc(testo)}</summary></details>"


def card_scoperta(titolo: str, perche: str, meta: str = "", url: str = "", comando: str = "", sottotitolo: str = "") -> str:
    """Scoperta (repo o skill): tutto testo escapato; URL e comando solo come testo, nessun link."""
    u = f"<div class='g-sub' title='{esc(url)}'>{esc(url)}</div>" if url else ""
    c = f"<div class='g-cmd' title='{esc(comando)}'><code>{esc(comando)}</code></div>" if comando else ""
    m = f"<div class='g-sub'>{esc(meta)}</div>" if meta else ""
    st_ = f"<div class='g-sub' title='{esc(sottotitolo)}'>{esc(sottotitolo)}</div>" if sottotitolo else ""
    return (f"<div class='g-card g-skill'><div class='g-name'>{esc(titolo)}</div>{st_}{_desc_3righe(perche)}"
            f"{m}{u}{c}</div>")


def tabella_agenti(righe: list[dict], fa) -> str:
    if not righe:
        return ""
    corpo = []
    for r in righe:
        on = r["stato"] == "al lavoro"
        pill = (f"<span class='pill {'on' if on else 'off'}'><i class='{'g-dot' if on else ''}'></i>"
                f"{esc(r['stato'].upper())}</span>")
        import plancia as _p
        if r.get("tipo") == "subagente" or r.get("nome_agente"):
            tipo = _p.nome_ruolo(r.get("nome_agente") or "", r.get("compito") or "") + (f" · {r['compito']}" if r.get("compito") else "")
        else:
            tipo = "Sessione principale"
        msg = r["messaggio"]
        corpo.append(
            f"<tr><td class='nw'>{pill}</td><td class='nw' title='{esc(tipo)}'>{esc(_p.accorcia(tipo, 40))}</td>"
            f"<td class='nw tool' title='{esc(r['strumento'] or '')}'>{esc(_p.nome_strumento(r['strumento']) or '—')}</td>"
            f"<td class='msg' title='{esc(msg)}'>{esc(_p.accorcia(msg, 60))}</td></tr>"
        )
    testa = "".join(f"<th scope='col'>{h}</th>" for h in ("Stato", "Chi", "Strumento", "Ultimo evento"))
    return f"<div class='g-wrap' tabindex='0' role='region' aria-label='Tabella scorrevole'><table class='g-table'><thead><tr>{testa}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"


def tabella_processi(lista: list[dict]) -> str:
    corpo = "".join(
        f"<tr><td class='num'>{p['pid']}</td><td>{esc(p['nome'])}</td><td class='num'>{p['cpu']:.1f}</td>"
        f"<td class='num'>{p['ram_mb']:.1f}</td><td class='msg' title='{esc(p.get('cmd', ''))}'>{esc(p.get('cmd', ''))}</td></tr>"
        for p in lista
    )
    testa = "".join(f"<th>{h}</th>" for h in ("PID", "Nome", "CPU %", "RAM MB", "Comando"))
    return f"<div class='g-wrap' tabindex='0' role='region' aria-label='Tabella scorrevole'><table class='g-table'><thead><tr>{testa}</tr></thead><tbody>{corpo}</tbody></table></div>"


def grafico_cpu(storico: list[list[float]], n_core: int) -> alt.Chart:
    """Area+linea 2px, fascia al 10%, punto finale con anello, crosshair+tooltip al passaggio.

    storico: righe [secondi_relativi, cpu_totale_pct, cpu_claude_pct_della_macchina].
    """
    import altair as alt   # import tardivo: pesante, serve solo ai grafici
    import pandas as pd
    righe = []
    for r in storico:
        righe.append({"secondi": r[0], "CPU macchina": r[1], "CPU Claude": r[2] if len(r) > 2 else 0.0})
    wide = pd.DataFrame(righe)
    long = wide.melt("secondi", var_name="serie", value_name="valore")
    dominio = ["CPU macchina", "CPU Claude"]
    scala = alt.Scale(domain=dominio, range=[SERIE_TOT, SERIE_CLAUDE])
    colore = alt.Color("serie:N", scale=scala, legend=None)  # legenda HTML: vedi legenda_cpu()
    x = alt.X("secondi:Q", title=None, scale=alt.Scale(domain=[-120, 0]),
              axis=alt.Axis(values=[-120, -90, -60, -30, 0], labelExpr="datum.value == 0 ? 'ora' : abs(datum.value) + 's'",
                            labelColor=INK2, domain=False, tickColor="#1c2340", grid=False, labelFont="monospace"))
    y = alt.Y("valore:Q", title=None, scale=alt.Scale(domain=[0, 100]),
              axis=alt.Axis(values=[0, 25, 50, 75, 100], labelExpr="datum.value + '%'", labelColor=INK2, domain=False,
                            gridColor="#141a33", gridWidth=1, tickSize=0, labelFont="monospace"))
    nearest = alt.selection_point(nearest=True, on="pointerover", fields=["secondi"], empty=False, clear="pointerout")
    senza_legenda = colore
    base = alt.Chart(long).encode(x=x, y=y, color=senza_legenda)
    area = base.mark_area(opacity=0.10, interpolate="monotone")
    linea = base.mark_line(strokeWidth=2, interpolate="monotone", strokeJoin="round", strokeCap="round")
    ultimo = long[long["secondi"] == long["secondi"].max()]
    fine = alt.Chart(ultimo).mark_point(filled=True, size=70, stroke=SURFACE, strokeWidth=2).encode(x=x, y=y, color=senza_legenda)
    punti = base.mark_point(filled=True, size=70, stroke=SURFACE, strokeWidth=2).encode(
        opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
    guida = (alt.Chart(long).transform_pivot("serie", value="valore", groupby=["secondi"])
             .mark_rule(color="#2a3566").encode(
                 x=x, opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
                 tooltip=[alt.Tooltip("secondi:Q", title="secondi fa", format=".0f"),
                          alt.Tooltip("CPU macchina:Q", format=".1f"), alt.Tooltip("CPU Claude:Q", format=".1f")])
             .add_params(nearest))
    return (alt.layer(area, linea, fine, guida, punti).properties(height=250, background="transparent")
            .configure_view(stroke=None).configure(font="monospace"))


def legenda_cpu() -> str:
    """Legenda sempre presente (2 serie): swatch a linea + etichetta, in testo neutro."""
    voce = lambda col, nome: (f"<span class='g-leg'><i style='background:{col}'></i>{esc(nome)}</span>")
    return ("<div class='g-legend'>" + voce(SERIE_TOT, "CPU macchina") + voce(SERIE_CLAUDE, "CPU Claude (% della macchina)") + "</div>")


def grafico_costi(giorni: list[dict]) -> alt.Chart:
    """Colonne giornaliere: <=24px, estremo superiore arrotondato 4px, base squadrata, tooltip."""
    import altair as alt   # import tardivo: pesante, serve solo ai grafici
    import pandas as pd
    df = pd.DataFrame(giorni)
    df["giorno"] = pd.to_datetime(df["data"])
    barre = alt.Chart(df).mark_bar(size=14, cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color=SERIE_TOT).encode(
        x=alt.X("giorno:T", title=None, axis=alt.Axis(format="%d/%m", labelColor=INK2, domain=False, tickColor="#1c2340", tickCount={"interval": "day", "step": 5},
                                                       labelFont="monospace", labelOverlap="greedy", grid=False)),
        y=alt.Y("costo:Q", title=None, axis=alt.Axis(format="$.2f", labelColor=INK2, domain=False, gridColor="#141a33",
                                                      tickSize=0, labelFont="monospace")),
        tooltip=[alt.Tooltip("data:N", title="giorno"), alt.Tooltip("costo:Q", format="$.2f", title="costo ≈"),
                 alt.Tooltip("msgs:Q", title="messaggi"), alt.Tooltip("tools:Q", title="strumenti"),
                 alt.Tooltip("edits:Q", title="file modificati")],
        opacity=alt.condition(alt.datum.costo > 0, alt.value(1), alt.value(0.25)),
    )
    return barre.properties(height=240, background="transparent").configure_view(stroke=None).configure(font="monospace")


def barre_orizzontali(righe: list[tuple[str, float]], fmt=lambda v: f"${v:.2f}") -> str:
    """Classifica con barre CSS (valore in testo: nessuna informazione solo a colore)."""
    if not righe:
        return "<div class='g-sub'>nessun dato</div>"
    massimo = max(v for _, v in righe) or 1
    out = []
    for nome, v in righe[:8]:
        out.append(f"<div class='g-bar'><span class='n' title='{esc(nome)}'>{esc(nome)}</span>"
                   f"<span class='b'><i style='width:{max(2, v / massimo * 100):.0f}%'></i></span><span class='v'>{esc(fmt(v))}</span></div>")
    return "<div class='g-bars'>" + "".join(out) + "</div>"


def heatmap_giorni(giorni: list[dict]) -> alt.Chart:
    """Heatmap a settimane (colonne) x giorno della settimana (righe) della spesa giornaliera."""
    import altair as alt   # import tardivo: pesante, serve solo ai grafici
    import pandas as pd
    df = pd.DataFrame(giorni)
    d = pd.to_datetime(df["data"])
    df["settimana"] = (d - pd.Timestamp(d.min()) + pd.Timedelta(days=int(d.min().weekday()))).dt.days // 7
    df["giorno_sett"] = d.dt.weekday
    df["etichetta_sett"] = d.dt.strftime("%d/%m")
    giorni_nome = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
    return (alt.Chart(df).mark_rect(stroke=SURFACE, strokeWidth=3, cornerRadius=2).encode(
        x=alt.X("settimana:O", title=None, axis=None),
        y=alt.Y("giorno_sett:O", title=None, sort=list(range(7)),
                axis=alt.Axis(labelExpr="['lun','mar','mer','gio','ven','sab','dom'][datum.value]", labelColor=INK2,
                              domain=False, ticks=False, labelFont="monospace")),
        color=alt.Color("costo:Q", scale=alt.Scale(range=["#10182c", "#0b4a63", SERIE_TOT, "#00e5ff"], type="sqrt"),
                        legend=alt.Legend(orient="bottom", title="spesa giornaliera", format="$.2f", gradientLength=160,
                                          labelColor=INK2, titleColor=INK2, labelFont="monospace", titleFont="monospace")),
        tooltip=[alt.Tooltip("data:N", title="giorno"), alt.Tooltip("costo:Q", format="$.2f", title="costo ≈"),
                 alt.Tooltip("msgs:Q", title="messaggi")])
        .properties(width=alt.Step(24), height=alt.Step(22), background="transparent").configure_view(stroke=None).configure(font="monospace"))


def card_store(voce: dict) -> str:
    rischio = voce["rischio"]
    classe = "ok" if rischio == "basso" else "mid"
    stato = "<span class='pill on'><i></i>INSTALLATA</span>" if voce["installata"] else ""
    return (f"<div class='g-card g-skill'><div class='g-name'>{esc(voce['titolo'])} {stato}</div>"
            f"{_desc_3righe(voce['descrizione'])}"
            f"<div class='g-sub'>rischio: <b class='risk {classe}'>{esc(rischio)}</b> · {esc(voce['repo'])}</div></div>")


def tabella_clienti(righe: list[dict]) -> str:
    """Lead con punteggio, stato visita e prova. Tutto il testo viene da file scritti da agenti: sempre escapato."""
    if not righe:
        return ""
    import clienti as _c
    corpo = []
    for r in righe:
        fonte = _c.url_sicuro(r.get("fonte", ""))
        import plancia as _p
        dom = _p.dominio(fonte)
        link = (f"<a class='url' href='{esc(fonte)}' target='_blank' rel='noopener noreferrer' title='{esc(fonte)}'>{esc(dom)}</a>"
                if fonte and dom else "—")
        on = r["stato"] == "interessato"
        corpo.append(
            f"<tr><td class='num'><b>{r['adattamento']}</b>/5</td><td>{esc(r['azienda'])}</td><td>{esc(r.get('categoria', '—'))}</td>"
            f"<td>{esc(r.get('zona', '—'))}</td><td><span class='pill {'on' if on else 'off'}'><i></i>{esc(r['stato'].upper())}</span></td>"
            f"<td class='msg' title='{esc(r.get('prova', ''))}'>{esc((r.get('opportunita') or r.get('prova') or r.get('motivo') or '—')[:160])}</td>"
            f"<td>{link}</td></tr>")
    testa = "".join(f"<th scope='col'>{h}</th>" for h in ("Fit", "Attività", "Categoria", "Zona", "Visita", "Opportunità / prova", "Fonte"))
    return f"<div class='g-wrap' tabindex='0' role='region' aria-label='Tabella scorrevole'><table class='g-table'><thead><tr>{testa}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"


# ---------------------------------------------------------------- navigazione, transizioni, feed agenti
CSS_EXTRA = """
<style>
/* Transizione tra spazi: ogni sezione vive in un contenitore con chiave diversa, quindi al cambio il DOM nasce nuovo
   e l'animazione parte una volta sola (i fragment che si aggiornano dentro non la rifanno). */
/* (nessuna animazione di entrata: una sola animazione, il pallino "al lavoro") */

/* barra di navigazione */
[data-testid="stButtonGroup"] [role="radiogroup"] { gap:.35rem; flex-wrap:wrap; }
button[data-variant="segmented_control"] { letter-spacing:.08em; text-transform:uppercase; font-size:.7rem !important; padding:.5rem .9rem !important; }

/* tessere del Centro */
.g-tile { position:relative; border:1px solid #1c2340;
  padding:1.05rem 1.1rem; min-height:8.2rem; margin-bottom:.4rem; transition:border-color .15s; }
.g-tile:hover { border-color:#22D3EE; }
.g-tile .t { font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; color:#8FA3B5; }
.g-tile .v { font-family:var(--mono); font-size:2rem; font-weight:700; margin-top:.3rem; font-variant-numeric:tabular-nums; color:#e8f1ff; }
.g-tile .s { font-size:.78rem; color:#a3aecb; margin-top:.3rem; }

/* feed degli agenti */
.g-feed { border:1px solid #1c2340; max-height:560px; overflow-y:auto; }
.g-ev { display:grid; grid-template-columns:62px 1fr; gap:.2rem .8rem; padding:.7rem .9rem; border-bottom:1px solid rgba(28,35,64,.6); font-size:.8rem; }
.g-ev:hover { background:#17212D; }
.g-ev .ora { color:#8b97b3; font-variant-numeric:tabular-nums; }
.g-ev .chi { color:#8b97b3; font-size:.7rem; }
.g-ev .tag { display:inline-block; padding:.05rem .5rem; margin-right:.55rem; font-size:.62rem; letter-spacing:.14em; border:1px solid; text-transform:uppercase; }
.tag.delega, .tag.web { color:#22D3EE; border-color:rgba(34,211,238,.55); }
.tag.file, .tag.comando { color:#FBBF24; border-color:rgba(251,191,36,.5); }
.tag.dice, .tag.altro { color:#8FA3B5; border-color:#2A3A4D; }
.g-ev .corpo { color:#e8f1ff; word-break:break-word; } .g-ev .sub { grid-column:2; color:#a3aecb; font-size:.76rem; }
.g-ev .sub b { color:#00d4f2; font-weight:600; }
.g-ev.nuovo { border-left:2px solid #22D3EE; animation:g-event-in .3s ease-out both; }
@keyframes g-event-in { from { opacity:.55; transform:translateY(-4px); } to { opacity:1; transform:none; } }
@media (prefers-reduced-motion: reduce) { .g-ev.nuovo { animation:none; } }

/* plancia: alto compatto (Guardian + utilizzo) e griglia di schede agente */
.g-bar { margin:.35rem 0 .6rem; }
.g-piccolo { font-size:.68rem; color:#8b97b3; letter-spacing:.04em; }
.g-agente { border:1px solid #1c2340; padding:.7rem .8rem; margin-bottom:.6rem; }
.g-agente.on { border-color:#4ADE80; }
.g-agente .nome { font-weight:700; color:#e8f1ff; word-break:break-word; } .g-agente .nome span { color:#a3aecb; font-weight:400; }
.g-agente .meta { font-size:.72rem; color:#8b97b3; margin:.3rem 0 .5rem; }
.g-agente .ev { font-size:.74rem; padding:.28rem 0; border-top:1px solid rgba(28,35,64,.6); word-break:break-word; color:#e8f1ff; }
.g-agente .ev .tag { margin-right:.4rem; padding:.02rem .35rem; font-size:.64rem; letter-spacing:.1em; border:1px solid; text-transform:uppercase; }
.g-agente .ev .sub { color:#a3aecb; font-size:.7rem; } .g-agente .ev .sub b { color:#00d4f2; font-weight:600; }
.g-agente .file { font-size:.7rem; color:#FBBF24; margin-top:.4rem; word-break:break-all; }
</style>
"""

_TAG = {"delega": ("delega", "DELEGA"), "web-ricerca": ("web", "CERCA"), "web-apri": ("web", "APRE"), "browser": ("web", "BROWSER"),
        "file": ("file", "FILE"), "comando": ("comando", "CMD"), "dice": ("dice", "DICE"), "lettura": ("altro", "LEGGE"),
        "strumento": ("altro", "USA")}


def tessera(titolo: str, valore: str, sub: str = "") -> str:
    return f"<div class='g-tile'><div class='t'>{esc(titolo)}</div><div class='v'>{esc(valore)}</div><div class='s'>{esc(sub)}</div></div>"


def _nome_strumento(t) -> str:
    import plancia as _p
    return _p.nome_strumento(t)


def _testo_ev(e: dict) -> str:
    import plancia as _p
    return _p.testo_evento(e)


def feed_attivita(righe: list[dict], fa, ora: float, nuovi_da: float = 0.0) -> str:
    """Feed live: chi fa cosa, quali pagine apre, cosa ne ricava. Tutto il testo viene da agenti: sempre escapato."""
    import time as _t
    import clienti as _c
    if not righe:
        return "<div class='g-feed' tabindex='0' role='region' aria-label='Attività recenti'><div class='g-ev'><div></div><div class='corpo'>Nessuna attività recente.</div></div></div>"
    out = []
    for e in righe:
        classe, etichetta = _TAG.get(e["tipo"], ("altro", "USA"))
        url = _c.url_sicuro(e.get("url", ""))
        if url:
            dominio = re.sub(r"^https?://", "", url).split("/")[0]
            corpo = f"<b class='url' title='{esc(url)}'>{esc(dominio)}</b> {esc(_testo_ev(e) if e.get('tipo') == 'browser' else e.get('testo', ''))}"
        else:
            corpo = esc(_testo_ev(e))
        sub = ""
        if e.get("brief"):
            sub += f"<div class='sub'>Brief: {esc(e['brief'][:320])}</div>"
        if e.get("risultato"):
            import plancia as _pl
            preso = _pl.riassumi_risultato(e["risultato"])
            if preso:
                sub += f"<div class='sub' title='{esc(_pl.pulisci_risultato(e['risultato'])[:400])}'><b>ha preso:</b> {esc(_pl.accorcia(preso, 140))}</div>"
        nuovo = " nuovo" if e["ts"] > nuovi_da > 0 else ""
        out.append(f"<div class='g-ev{nuovo}'><div class='ora'>{_t.strftime('%H:%M:%S', _t.localtime(e['ts']))}</div>"
                   f"<div><span class='tag {classe}'>{etichetta}</span><span class='corpo'>{corpo}</span> "
                   f"<span class='chi'>· {esc(e.get('chi', ''))}</span></div>{sub}</div>")
    return f"<div class='g-feed' tabindex='0' role='region' aria-label='Attività recenti'>{''.join(out)}</div>"


def livello_utilizzo(pct: float) -> tuple[str, str]:
    """Classe colore + parola di stato (il colore non è mai l'unica informazione)."""
    if pct >= 85:
        return "crit", "CRITICO"
    if pct >= 60:
        return "warn", "ATTENZIONE"
    return "ok", "OK"


def barra_utilizzo(titolo: str, pct: float, reset: str) -> str:
    p = max(0.0, min(100.0, float(pct)))
    classe, parola = livello_utilizzo(p)
    return (f"<div class='g-uso {classe}' role='group' aria-label='{esc(titolo)}: {p:.0f}% usato, {esc(parola)}'>"
            f"<div class='testa'><span class='nome'>{esc(titolo)}</span><span class='stato'>{parola}</span></div>"
            f"<div class='num'>{p:.0f}<small>%</small></div>"
            f"<div class='pista' aria-hidden='true'><div class='riempi' style='width:{p:.0f}%'></div></div>"
            f"<div class='reset'>{esc(reset)}</div></div>")


def scheda_agente(c: dict, fa, max_ev: int = 5) -> str:
    """Scheda di un agente (da plancia.raggruppa_agenti). Tutto il testo viene da agenti: sempre escapato."""
    import time as _t
    on = c["stato"] == "al lavoro"
    stato = {"al lavoro": "on", "finito": "fine"}.get(c["stato"], "off")
    testa = (f"<div class='testa'><span class='stato {stato}'><i aria-hidden='true'></i>{esc(c['stato'].upper())}</span>"
             f"<span class='quando'>{esc(fa(c['ultimo_agg']))}</span></div>")
    nome = f"<div class='nome'>{esc(c['nome'])}</div>" + (f"<div class='compito'>{esc(c['compito'][:120])}</div>" if c["compito"] else "")
    meta = (f"<div class='chips'><span title='{esc(c['strumento'] or '')}'>strumento <b>{esc(_nome_strumento(c['strumento']) or '—')}</b></span>"
            f"<span>{esc(c['progetto'])}</span><span>{len(c['eventi'])} eventi</span></div>")
    righe = []
    for e in c["eventi"][:max_ev]:
        classe, etichetta = _TAG.get(e["tipo"], ("altro", "USA"))
        if e.get("strumento") == "SubagentHandback":
            classe, etichetta, e = "file", "CONSEGNA", {**e, "testo": "rapporto finale consegnato al manager", "strumento": ""}
        import clienti as _c
        import plancia as _p
        url = _c.url_sicuro(e.get("url", ""))
        testo = (re.sub(r"^https?://", "", url).split("/")[0] + " " if url else "") +             _p.testo_evento(e)
        preso = _p.riassumi_risultato(e.get("risultato"))
        sub = f"<div class='sub' title='{esc(_p.pulisci_risultato(e.get('risultato'))[:400])}'><b>ha preso:</b> {esc(preso)}</div>" if preso else ""
        righe.append(f"<div class='ev' title='{esc(testo)}'><span class='tag {classe}'>{etichetta}</span>{esc(_p.accorcia(testo, 140))}"
                     f" <span class='g-piccolo'>{_t.strftime('%H:%M:%S', _t.localtime(e['ts']))}</span>{sub}</div>")
    if not righe:
        righe.append("<div class='ev g-piccolo'>Nessun evento registrato.</div>")
    nomi = [re.split(r"[\\/]", f)[-1] for f in c["file"][:6]]
    files = (f"<div class='file' title='{esc(chr(10).join(c['file']))}'>file: {esc(', '.join(nomi))}</div>") if c["file"] else ""
    return (f"<article class='g-agente{' on' if on else ''}'>{testa}{nome}{meta}"
            f"<div class='linea'>{''.join(righe)}</div>{files}</article>")


def dettaglio_agente(c: dict, fa) -> str:
    """Pannello di dettaglio di un agente: ruolo, compito completo, stato, durata, TUTTI gli eventi, file con percorso completo.
    Tutto il testo viene da agenti: sempre escapato."""
    import time as _t
    import clienti as _c
    import plancia as _p
    righe = []
    for e in c["eventi"]:
        classe, etichetta = _TAG.get(e["tipo"], ("altro", "USA"))
        url = _c.url_sicuro(e.get("url", ""))
        testo = (re.sub(r"^https?://", "", url).split("/")[0] + " " if url else "") + _testo_ev(e)
        sub = f"<div class='sub'><b>ha preso:</b> {esc(e['risultato'])}</div>" if e.get("risultato") else ""
        righe.append(f"<li><span class='ora'>{_t.strftime('%H:%M:%S', _t.localtime(e['ts']))}</span>"
                     f"<span class='tag {classe}'>{etichetta}</span>{esc(testo)}{sub}</li>")
    eventi = f"<ol class='eventi'>{''.join(righe)}</ol>" if righe else "<p class='g-piccolo'>Nessun evento registrato.</p>"
    files = "".join(f"<li><code>{esc(f)}</code></li>" for f in c["file"]) or "<li class='g-piccolo'>Nessun file prodotto.</li>"
    dur = _p.durata_testo(c.get("inizio"), c.get("ultimo_agg"))
    return (f"<section class='g-det' aria-label='Dettagli agente {esc(c['nome'])}'>"
            f"<dl><dt>Ruolo</dt><dd>{esc(c['nome'])}</dd><dt>Stato</dt><dd>{esc(c['stato'].upper())} · {esc(fa(c['ultimo_agg']))}</dd>"
            f"<dt>Durata</dt><dd>{esc(dur)}</dd><dt>Strumento</dt><dd>{esc(c['strumento'] or '—')}</dd>"
            f"<dt>Progetto</dt><dd>{esc(c['progetto'])}</dd><dt>Compito</dt><dd>{esc(c['compito'] or '—')}</dd></dl>"
            f"<h4>Eventi ({len(c['eventi'])})</h4>{eventi}<h4>File prodotti ({len(c['file'])})</h4><ul class='files'>{files}</ul></section>")


# Livello visivo della plancia (ui-ux-pro-max: vetro scuro, un accento, colori di stato con testo, densità alta).
CSS_PLANCIA = """
<style>
:root { --p-bg:#070b16; --p-glass:rgba(15,23,42,.72); --p-glass2:rgba(15,23,42,.9); --p-line:rgba(148,163,184,.16);
  --p-line2:rgba(148,163,184,.28); --p-ink:#f8fafc; --p-ink2:#cbd5e1; --p-mute:#94a3b8; --p-acc:#22d3ee;
  --p-ok:#22c55e; --p-warn:#f59e0b; --p-crit:#ef4444; --r-sm:14px; --r-md:20px; --r-lg:26px; --p-r:var(--r-md); --p-ease:cubic-bezier(.2,.7,.2,1); }
.block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; max-width: 1680px; }
/* pannelli in vetro: Guardian e utilizzo */
[class*="st-key-plancia_guardian"], [class*="st-key-plancia_utilizzo"] { background:var(--p-glass); border:1px solid var(--p-line);
  border-radius:var(--p-r); padding:.75rem .9rem .6rem; }
[class*="st-key-plancia_guardian"]::before { content:"GUARDIAN · MANAGER"; display:block; font:600 .66rem/1 var(--mono);
  letter-spacing:.22em; color:var(--p-acc); margin-bottom:.55rem; }
[class*="st-key-plancia_utilizzo"]::before { content:"UTILIZZO DEL PIANO"; display:block; font:600 .66rem/1 var(--mono);
  letter-spacing:.22em; color:var(--p-acc); margin-bottom:.55rem; }
[class*="st-key-chat_storico"] { height: 19vh !important; min-height: 120px; border-color: var(--p-line) !important;
  background: rgba(2,6,23,.45); border-radius: 8px; }
[class*="st-key-plancia_guardian"] [data-testid="stChatInput"] { border:1px solid var(--p-line2); border-radius:8px; }
[class*="st-key-plancia_guardian"] button { min-height: 40px; transition: border-color .15s var(--p-ease), background .15s; }
/* barre utilizzo */
.g-uso { padding:.5rem .1rem .65rem; border-bottom:1px solid var(--p-line); }
.g-uso:last-of-type { border-bottom:0; }
.g-uso .testa { display:flex; justify-content:space-between; align-items:center; font:600 .7rem/1 var(--mono); letter-spacing:.12em;
  color:var(--p-mute); text-transform:uppercase; }
.g-uso .stato { padding:.18rem .45rem; border-radius:999px; border:1px solid currentColor; font-size:.66rem; }
.g-uso.ok .stato { color:var(--p-ok); } .g-uso.warn .stato { color:var(--p-warn); } .g-uso.crit .stato { color:var(--p-crit); }
.g-uso .num { font:700 2.1rem/1.05 var(--mono); color:var(--p-ink); margin:.35rem 0 .35rem; font-variant-numeric: tabular-nums; }
.g-uso .num small { font-size:1rem; color:var(--p-mute); margin-left:.1rem; }
.g-uso .pista { height:6px; border-radius:999px; background:rgba(148,163,184,.14); overflow:hidden; }
.g-uso .riempi { height:100%; border-radius:999px; transition: width .6s var(--p-ease); }
.g-uso.ok .riempi { background:linear-gradient(90deg,#16a34a,var(--p-ok)); } .g-uso.warn .riempi { background:linear-gradient(90deg,#d97706,var(--p-warn)); }
.g-uso.crit .riempi { background:var(--p-crit); }
.g-uso .reset { font-size:.72rem; color:var(--p-mute); margin-top:.35rem; }
/* barra degli spazi: navigazione principale, voce attiva evidente */
[data-testid="stButtonGroup"] { position: sticky; top: .25rem; z-index: 20; background: var(--bg);
  padding:.45rem .5rem; border:1px solid var(--p-line); border-radius:var(--p-r); margin:.7rem 0 .6rem; }
button[data-variant="segmented_control"] { border-radius:8px !important; min-height:40px; font-size:.72rem !important;
  border-color:transparent !important; background:transparent !important; cursor:pointer; }
button[data-variant="segmented_control"]:hover { background:rgba(148,163,184,.08) !important; }
button[data-variant="segmented_control"][data-selected="true"] { background:rgba(34,211,238,.12) !important; color:var(--p-ink) !important;
  border-color:rgba(34,211,238,.6) !important; box-shadow: inset 0 -2px 0 var(--p-acc); }
/* lo spazio scelto occupa il resto dello schermo (~3/4) */
[class*="st-key-sez_"] { min-height: 62vh; }
/* schede agente: alte uguali, scorrimento interno, linea del tempo */
.g-agente { display:flex; flex-direction:column; height: 60vh; min-height: 320px; overflow:hidden; border-radius:var(--p-r);
  border:1px solid var(--p-line); background:var(--p-glass2); padding:.8rem .85rem .7rem; margin:0;
  transition: border-color .15s; }
.g-agente:hover { border-color: var(--p-acc); }
.g-agente.on { border-color: var(--p-ok); }
.g-agente .testa { display:flex; justify-content:space-between; align-items:center; margin-bottom:.45rem; }
.g-agente .stato { display:inline-flex; align-items:center; gap:.4rem; font:600 .62rem/1 var(--mono); letter-spacing:.14em;
  padding:.22rem .5rem; border-radius:999px; border:1px solid var(--p-line2); color:var(--p-mute); }
.g-agente .stato i { width:7px; height:7px; border-radius:50%; background:currentColor; }
.g-agente .stato.on { color:var(--p-ok); border-color:rgba(34,197,94,.5); } .g-agente .stato.on i { animation: g-pulsa 2s ease-in-out infinite; }
.g-agente .stato.fine { color:var(--p-acc); border-color:rgba(34,211,238,.45); }
@keyframes g-pulsa { 50% { opacity:.4; } }
.g-agente .quando { font:500 .7rem/1 var(--mono); color:var(--p-mute); font-variant-numeric: tabular-nums; }
.g-agente .nome { font-weight:700; font-size:.95rem; color:var(--p-ink); overflow-wrap:anywhere; }
.g-agente .compito { font-size:.78rem; color:var(--p-ink2); margin-top:.1rem; overflow-wrap:anywhere; }
.g-agente .chips { display:flex; flex-wrap:wrap; gap:.3rem; margin:.5rem 0 .55rem; }
.g-agente .chips span { font-size:.66rem; color:var(--p-mute); border:1px solid var(--p-line); border-radius:6px; padding:.15rem .4rem; }
.g-agente .chips b { color:var(--p-ink2); font-weight:600; }
.g-agente .linea { flex:1; overflow-y:auto; border-left:1px solid var(--p-line2); padding-left:.65rem; margin-left:.2rem; }
.g-agente .ev { position:relative; border-top:0; padding:.32rem 0 .4rem; font-size:.76rem; color:var(--p-ink); overflow-wrap:anywhere; }
.g-agente .ev::before { content:""; position:absolute; left:calc(-.65rem - 4px); top:.6rem; width:7px; height:7px; border-radius:50%;
  background:var(--p-bg); border:1.5px solid var(--p-acc); }
.g-agente .file { font-size:.7rem; color:var(--p-warn); margin-top:.5rem; padding-top:.45rem; border-top:1px solid var(--p-line);
  overflow-wrap:anywhere; max-height:4.6em; overflow-y:auto; flex-shrink:0; }
@media (max-width: 900px) { .g-agente { height:auto; max-height:70vh; } [class*="st-key-chat_storico"] { height: 45vh !important; } }
@media (max-width: 900px) {
  [class*="st-key-mic_pop"], [class*="st-key-mic_pop"] [data-testid="stTooltipHoverTarget"] { width:100% !important; }
  [class*="st-key-mic_pop"] button { width:100% !important; min-height:52px !important; font-size:1.05rem !important; }
  [class*="st-key-mic_pop"] button p { font-size:0 !important; }
  [class*="st-key-mic_pop"] button p::after { content:"Parla con Guardian"; font-size:1.05rem; font-weight:700; }
  [data-testid="stAudioInput"] { min-height:72px; }
  [data-testid="stAudioInput"] button { min-width:52px; min-height:52px; }
  [data-testid="stChatMessage"] audio, [data-testid="stAudio"] audio { width:100% !important; }
}
@media (prefers-reduced-motion: reduce) { .g-agente, .g-uso .riempi { transition:none; } .g-agente .stato.on i { animation:none; }
  .g-agente:hover { transform:none; } }
/* ---- Cyan Ops: token (contrasto AA su #0B1118) ---- */
:root { --p-bg:#0B1118; --p-glass:rgba(18,26,36,.78); --p-glass2:rgba(18,26,36,.92); --p-line:rgba(143,163,181,.18);
  --p-line2:#2A3A4D; --p-ink:#E6EDF3; --p-ink2:#C3CFDA; --p-mute:#8FA3B5; --p-acc:#22D3EE;
  --p-ok:#4ADE80; --p-warn:#FBBF24; --p-crit:#FF6B6B; }
.stApp { background: var(--p-bg) !important; }
/* sfondo fisso: griglia + vignettatura + poche particelle (solo transform, nessun JS) */
.stApp::before, .stApp::after { content:none !important; display:none !important; }
[data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: transparent !important; }
/* l'intestazione trasparente non deve rubare i clic alla barra degli spazi quando si scorre */
[data-testid="stHeader"] { pointer-events: none; }
/* griglie a righe: la scheda riempie l'altezza della colonna, pulsanti allineati in fondo */
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(> [data-testid="stLayoutWrapper"] > [class*="st-key-skc_"]),
div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"]:has(> [data-testid="stLayoutWrapper"] > [class*="st-key-scp_"]) { height: 100%; }
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-skc_"]), [data-testid="stLayoutWrapper"]:has(> [class*="st-key-scp_"]) { flex: 1 1 auto; }
[class*="st-key-skc_"], [class*="st-key-scp_"] { height: 100%; }
/* Scoperte: la scheda (bordo su .g-card) deve riempire tutta la catena di contenitori del markdown */
[class*="st-key-scp_"] > [data-testid="stElementContainer"], [class*="st-key-scp_"] [data-testid="stMarkdown"],
[class*="st-key-scp_"] [data-testid="stMarkdown"] > div, [class*="st-key-scp_"] [data-testid="stMarkdownContainer"],
[class*="st-key-scp_"] .g-card { height: 100%; box-sizing: border-box; }
/* tessere di una stessa riga alte uguali anche se il sottotitolo va su due righe */
.g-tile { min-height: 9.5rem; box-sizing: border-box; }
/* tabella Clienti: dominio e categoria mai spezzati a metà parola */
.g-table td a.url { white-space: nowrap; word-break: normal; overflow-wrap: normal; }
.g-table td:nth-child(3) { white-space: nowrap; }
@media (max-width: 900px) { [data-testid="stHorizontalBlock"] { row-gap: .55rem !important; } .g-tile { min-height: 0; margin-bottom: .5rem; padding-top: .6rem !important; padding-bottom: .6rem !important; } }
.g-tile .s { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
[data-testid="stHeader"] button, [data-testid="stHeader"] a, [data-testid="stHeader"] [role="button"] { pointer-events: auto; }
[data-testid="stMain"], .block-container { position: relative; z-index: 1; }
/* reattore */
.reattore { display:flex; align-items:center; gap:.7rem; margin:0 0 .5rem; }
.reattore svg { flex:none; overflow:visible; }
.reattore .rx-o, .reattore .rx-m { stroke:var(--p-acc); transform-origin:32px 32px; }
.reattore .rx-c { fill:var(--p-acc); transform-origin:32px 32px; }
.reattore .rx-t { display:flex; flex-direction:column; gap:.2rem; }
.reattore .rx-k { font:600 .62rem/1 var(--mono); letter-spacing:.2em; color:var(--p-mute); }
.reattore .rx-l { font:700 .9rem/1.1 var(--mono); color:var(--p-ink); }
/* indicatore senza testo: la FORMA cambia con lo stato (cerchio, anello, rombo, quadrato) */
.reattore .rx-l::before { content:""; display:inline-block; width:.62em; height:.62em; margin-right:.5em; vertical-align:.06em; border-radius:50%; background:var(--p-acc); }
.rx-pensiero .rx-m { stroke:var(--p-warn); }
.rx-pensiero .rx-c { fill:var(--p-warn); } .rx-pensiero .rx-l::before { border-radius:2px; transform:rotate(45deg) scale(.85); background:var(--p-warn); }
.rx-voce .rx-m { stroke:var(--p-ok); } .rx-voce .rx-c { fill:var(--p-ok); }
.rx-voce .rx-l::before { border-radius:3px; background:var(--p-ok); }
.rx-ascolto .rx-l::before { background:transparent; border:2px solid var(--p-acc); box-sizing:border-box; }
@media (prefers-reduced-motion: reduce) { .reattore * { animation:none !important; } }
/* logo animato (.g-logomark): stato sul contenitore riposo/ascolto/pensa/parla; solo transform e opacity; niente blur né glow */
.g-logomark { display:inline-block; flex:none; line-height:0; }
.g-logomark svg { display:block; width:100%; height:100%; overflow:visible; }
.g-logomark .lg-a, .g-logomark .lg-b, .g-logomark .lg-d, .g-logomark .lg-t, .g-logomark .lg-i, .g-logomark .lg-c { transform-origin:64px 64px; }
.g-logomark.riposo .lg-a { animation:lg-r 20s linear infinite; }
.g-logomark.riposo .lg-b { animation:lg-r 34s linear infinite reverse; }
.g-logomark.riposo .lg-c { animation:lg-resp 5s ease-in-out infinite; }
.g-logomark.ascolto .lg-a { animation:lg-r 5s linear infinite; }
.g-logomark.ascolto .lg-b { animation:lg-r 6s linear infinite reverse; }
.g-logomark.ascolto .lg-t { animation:lg-tacche .9s ease-in-out infinite; }
.g-logomark.ascolto .lg-c { animation:lg-ritmo 1.1s ease-in-out infinite; }
.g-logomark.pensa .lg-a { animation:lg-r 1.2s steps(8) infinite; }
.g-logomark.pensa .lg-b { animation:lg-r 2.4s steps(8) infinite reverse; }
.g-logomark.pensa .lg-c { animation:lg-resp 1.6s ease-in-out infinite; }
body.g-parla .g-logomark .lg-a { animation:lg-r 14s linear infinite; }
body.g-parla .g-logomark .lg-c { animation:lg-voce 1.7s ease-in-out infinite; }
body.g-parla .g-logomark .lg-i { animation:lg-voce2 1.3s ease-in-out infinite; stroke:#F472B6; }
body.g-parla[data-gb="0"] .g-logomark .lg-c { animation:lg-parola0 .28s ease-out 1, lg-voce 1.7s ease-in-out .28s infinite; }
body.g-parla[data-gb="1"] .g-logomark .lg-c { animation:lg-parola1 .28s ease-out 1, lg-voce 1.7s ease-in-out .28s infinite; }
@keyframes lg-r { to { transform:rotate(360deg); } }
@keyframes lg-resp { 50% { transform:scale(.88); opacity:.8; } }
@keyframes lg-tacche { 50% { opacity:.25; } }
@keyframes lg-ritmo { 0%,100% { transform:scale(.8); } 50% { transform:scale(1.3); } }
@keyframes lg-voce { 0%{transform:scale(.9)} 12%{transform:scale(1.35)} 25%{transform:scale(.85)} 41%{transform:scale(1.15)} 55%{transform:scale(.8)} 70%{transform:scale(1.4)} 85%{transform:scale(1)} 100%{transform:scale(.9)} }
@keyframes lg-voce2 { 0%,100%{transform:scale(1)} 20%{transform:scale(1.1)} 45%{transform:scale(.93)} 70%{transform:scale(1.07)} }
@keyframes lg-parola0 { from { transform:scale(1.5); } to { transform:scale(1); } }
@keyframes lg-parola1 { from { transform:scale(1.5); } to { transform:scale(1); } }
@media (prefers-reduced-motion: reduce) {
  .g-logomark *, body.g-parla .g-logomark * { animation:none !important; }
  .g-logomark.ascolto .lg-a, .g-logomark.ascolto .lg-b { opacity:.55; }
  .g-logomark.pensa .lg-a, .g-logomark.pensa .lg-b { opacity:.35; }
  body.g-parla .g-logomark .lg-i { stroke:#F472B6; }
}
.g-head-logo { display:flex; align-items:center; gap:.9rem; }
/* ---- Spazi secondari: stessa lingua visiva degli Agenti (vetro, bordo, raggio, hover, focus) ---- */
.g-card, .g-tile, .g-wrap, [data-testid="stForm"], [data-testid="stExpander"] { background:var(--p-glass2) !important;
  border:1px solid var(--p-line) !important; border-radius:var(--p-r) !important; box-shadow:none;
  transition: border-color .2s var(--p-ease), transform .2s var(--p-ease); }
.g-card::before, .g-card::after, .g-tile::before { display:none; }
.g-card:hover, .g-tile:hover { border-color:var(--p-line2) !important; transform:translateY(-2px); box-shadow:none; }
.g-card:focus-within, .g-wrap:focus-within { border-color:var(--p-acc) !important; }
.g-card { padding:.85rem .95rem; }
.g-skill .g-name, .g-card .g-name { color:var(--p-ink); font-weight:700; overflow-wrap:anywhere; }
.g-card .g-desc { color:var(--p-ink2); } .g-card .g-sub, .g-tile .s, .g-label { color:var(--p-mute); }
.g-value, .g-tile .v { color:var(--p-ink); text-shadow:none; }
[class*="st-key-sez_"] h3 { font:600 .8rem/1.2 var(--mono) !important; letter-spacing:.18em; color:var(--p-ink2) !important;
  border-left:3px solid var(--p-acc); padding-left:.6rem; margin:.6rem 0 .5rem; }
[class*="st-key-sez_"] h3::before, [class*="st-key-sez_"] h4::before { content:""; }
[class*="st-key-sez_"] h4 { color:var(--p-ink2) !important; }
.g-wrap { overflow-x:auto; }
.g-table th { color:var(--p-mute); padding:.7rem .8rem; background:rgba(18,26,36,.6); }
.g-table td { padding:.8rem .8rem; line-height:1.4; border-bottom:1px solid var(--p-line); color:var(--p-ink); }
.g-table tbody tr:nth-child(even) td { background:rgba(143,163,181,.045); }
.g-table tr:hover td { background:rgba(34,211,238,.07); }
.g-table td.msg { white-space:normal; max-width:420px; color:var(--p-ink2); }
.pill { border-radius:999px; }
/* pulsanti, campi e controlli: bersaglio >= 40px, focus sempre visibile */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { min-height:40px; border-radius:var(--p-r);
  border:1px solid rgba(34,211,238,.45); color:var(--p-acc); background:transparent; letter-spacing:.14em; text-transform:uppercase; font-size:.72rem; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover { border-color:var(--p-acc);
  background:rgba(34,211,238,.1); box-shadow:none; color:var(--p-ink); }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible, .stFormSubmitButton > button:focus-visible,
[data-baseweb="select"] *:focus-visible, input:focus-visible, textarea:focus-visible, summary:focus-visible, [role="tab"]:focus-visible {
  outline:2px solid var(--p-acc) !important; outline-offset:2px !important; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div { min-height:40px; border-radius:var(--p-r) !important; }
[data-testid="stExpander"] summary { min-height:40px; }
[data-testid="stChatMessage"], [data-testid="stChatInput"] { border-radius:var(--p-r); }
/* dettaglio agente (dialog) */
div[role="dialog"] { background:var(--p-glass2) !important; border:1px solid var(--p-line2); border-radius:var(--p-r) !important; }
.g-det dl { display:grid; grid-template-columns:7rem 1fr; gap:.35rem .8rem; margin:0 0 .6rem; font-size:.8rem; }
.g-det dt { color:var(--p-mute); text-transform:uppercase; letter-spacing:.12em; font-size:.66rem; padding-top:.15rem; }
.g-det dd { margin:0; color:var(--p-ink); overflow-wrap:anywhere; }
.g-det h4 { margin:.9rem 0 .3rem; }
.g-det ol.eventi, .g-det ul.files { list-style:none; margin:0; padding:0; border-left:1px solid var(--p-line2); }
.g-det li { padding:.35rem 0 .35rem .7rem; font-size:.78rem; color:var(--p-ink); overflow-wrap:anywhere; }
.g-det li .ora { color:var(--p-mute); margin-right:.5rem; font-variant-numeric:tabular-nums; }
.g-det li .tag { margin-right:.4rem; padding:.02rem .35rem; font-size:.64rem; letter-spacing:.1em; border:1px solid; }
.g-det li .sub { color:var(--p-ink2); font-size:.74rem; margin-top:.15rem; } .g-det li .sub b { color:var(--p-acc); }
.g-det code { color:var(--p-warn); background:transparent; }
@media (prefers-reduced-motion: reduce) { .g-card, .g-tile, .g-wrap { transition:none; } .g-card:hover, .g-tile:hover { transform:none; } }
/* ==== Stile basic: token unici, una sola regola per le superfici, niente blur ==== */
:root { --bg:#0B1118; --surface:#121A24; --surface2:#17212D; --line:#2A3A4D;
  --ink:#E6EDF3; --ink2:#C3CFDA; --mute:#8FA3B5; --acc:#22D3EE; --acc-ink:#06222A; --pink:#F472B6;
  --ok:#4ADE80; --warn:#FBBF24; --crit:#FF6B6B; --r:12px; --bd:1px solid var(--line); --gap:1rem; --pad:1.1rem;
  --sans:Inter,"Space Grotesk",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,"Cascadia Code",Consolas,Menlo,monospace;
  --p-bg:var(--bg); --p-acc:var(--acc); --p-line:var(--line); --p-line2:var(--line); --p-ink:var(--ink); --p-ink2:var(--ink2); --p-mute:var(--mute);
  --p-ok:var(--ok); --p-warn:var(--warn); --p-crit:var(--crit); --cy:var(--acc); --cy2:var(--acc); --mg:var(--pink); --pk:var(--pink); --pk2:var(--pink);
  --p-r:var(--r); --r-sm:8px; --r-md:var(--r); --r-lg:var(--r);
  --glass-solid:var(--surface); --glass-border:var(--line); --glass-hi:var(--line); --sp:.9rem; }
.stApp { background: var(--bg) !important; }
.g-card, .g-tile, .g-wrap, .g-agente, .g-feed, [data-testid="stForm"], [data-testid="stExpander"],
[class*="st-key-plancia_guardian"], [class*="st-key-plancia_utilizzo"], div[role="dialog"], [data-testid="stChatMessage"] {
  background:var(--surface) !important; border:var(--bd) !important; border-radius:var(--r) !important; box-shadow:none !important;
  transition: border-color .15s; }
[data-baseweb="popover"] > div { background:var(--surface) !important; border:var(--bd) !important; border-radius:var(--r) !important; box-shadow:none !important; }
.g-card, .g-tile { padding:var(--pad); }
.g-card:hover, .g-tile:hover, .g-agente:hover { transform:none; border-color:var(--acc) !important; }
.g-agente.on { border-color:var(--ok) !important; }
/* scheda + Dettagli = un solo blocco di vetro */
[class*="st-key-agc_"], [class*="st-key-skc_"] { gap:0 !important; }
[class*="st-key-skc_"] .g-card { height:100%; border-bottom-left-radius:0 !important; border-bottom-right-radius:0 !important; border-bottom-color:transparent !important; }
[class*="st-key-skc_"] .g-card:hover { transform:none !important; }
[class*="st-key-skc_"] .stButton, [class*="st-key-skc_"] .stButton button, [class*="st-key-skc_"] [data-testid="stTooltipHoverTarget"] { width:100% !important; }
[class*="st-key-skc_"] .stButton button { background:var(--surface) !important; border:var(--bd) !important;
  border-radius:0 0 var(--r) var(--r) !important; margin-top:-1px; box-shadow:none !important; }
[class*="st-key-skc_"] .stButton button:hover { transform:none !important; border-color:var(--acc) !important; }
[class*="st-key-skc_"] a.url, .g-table a.url { color:var(--p-acc); text-decoration:underline; }
.g-desc, .g-more > summary { display:-webkit-box; -webkit-line-clamp:3; line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }
.g-more > summary { cursor:pointer; list-style:none; } .g-more > summary::-webkit-details-marker { display:none; }
.g-more > summary::after { content:"mostra tutto"; display:block; color:var(--p-acc); font-size:.7rem; margin-top:.2rem; }
.g-more[open] > summary { display:block; -webkit-line-clamp:unset; overflow:visible; } .g-more[open] > summary::after { content:"riduci"; }
.g-sez { margin:1.1rem 0 .5rem; color:var(--p-ink); font-weight:700; letter-spacing:.04em; }
/* griglie a 3 colonne: schede di pari altezza, pulsante allineato in fondo; badge in alto a destra */
[data-testid="stHorizontalBlock"]:has([class*="st-key-skc_"], [class*="st-key-scp_"]) { align-items:stretch; }
[data-testid="stColumn"]:has([class*="st-key-skc_"], [class*="st-key-scp_"]) { display:flex; flex-direction:column; }
[data-testid="stColumn"]:has([class*="st-key-skc_"], [class*="st-key-scp_"]) > [data-testid="stVerticalBlock"] { flex:1 1 auto; }
[class*="st-key-skc_"], [class*="st-key-scp_"] { display:flex; flex-direction:column; height:100%; }
[class*="st-key-skc_"] > [data-testid="stElementContainer"]:first-child, [class*="st-key-scp_"] > [data-testid="stElementContainer"]:first-child { flex:1 1 auto; }
[class*="st-key-skc_"] > [data-testid="stElementContainer"]:first-child :is([data-testid="stMarkdown"], [data-testid="stMarkdownContainer"]),
[class*="st-key-scp_"] > [data-testid="stElementContainer"]:first-child :is([data-testid="stMarkdown"], [data-testid="stMarkdownContainer"]) { height:100%; }
[class*="st-key-scp_"] .g-card { height:100%; box-sizing:border-box; }
.g-skill .g-name { overflow-wrap:break-word; }
.g-cmd { margin-top:.45rem; overflow-x:auto; white-space:nowrap; font-size:.68rem; }
.g-cmd code { white-space:nowrap; font-size:.68rem; }
.g-skill { display:flex; flex-direction:column; }
.g-skill .g-desc, .g-skill .g-more { flex:1 1 auto; }
.g-skill .g-name:has(.pill) { padding-right:6.5rem; }
.g-skill .g-name .pill { position:absolute; top:.7rem; right:.8rem; }
[class*="st-key-agc_"] { gap:.45rem !important; }
[class*="st-key-agc_"] .g-agente { padding-bottom:1.1rem !important; margin-bottom:0 !important; }
[class*="st-key-agc_"] .g-agente .linea { min-height:0; }
[class*="st-key-agc_"] .g-agente .file { padding-bottom:.15rem; }
[class*="st-key-agc_"] .stButton, [class*="st-key-agc_"] .stButton button, [class*="st-key-agc_"] [data-testid="stTooltipHoverTarget"] { width:100% !important; }
[class*="st-key-skc_"] .stButton > button { background:var(--surface) !important; border:var(--bd) !important;
  border-radius:0 0 var(--r) var(--r) !important; margin-top:-1px; box-shadow:none !important; }
[class*="st-key-agc_"] .stButton button { background:var(--surface) !important; border:var(--bd) !important;
  border-radius:var(--r) !important; box-shadow:none !important; }
[class*="st-key-agc_"] .stButton button:hover, [class*="st-key-skc_"] .stButton > button:hover { transform:none !important; border-color:var(--acc) !important; }
.g-fin-riga { display:flex; gap:.7rem; align-items:baseline; font-size:.8rem; color:var(--p-ink2); overflow-wrap:anywhere; }
.g-fin-riga b { color:var(--p-ink); } .g-fin-riga .q { color:var(--p-mute); font:500 .7rem var(--mono); white-space:nowrap; }
.g-wrap, .g-feed { overflow-y:auto; }
[data-baseweb="menu"], [data-baseweb="popover"] ul { background:transparent !important; border-radius:var(--r-md) !important; }
[data-baseweb="menu"] li { border-radius:var(--r-sm); margin:2px 6px; }
[data-testid="stChatMessage"] { border-radius:var(--r-md) !important; }
[data-testid^="stChatMessageAvatar"] { border-radius:50% !important; }
[data-testid="stChatInput"], [data-testid="stChatInput"] > div { border-radius:var(--r) !important; }
[data-testid="stChatInput"] { background:var(--surface) !important; border:var(--bd) !important; box-shadow:none; }
[data-testid="stChatInput"]:focus-within { border-color:var(--acc) !important; box-shadow:none; }
[class*="st-key-chat_storico"] { border-radius:var(--r) !important; background:var(--bg) !important; }
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div { border-radius:var(--r-sm) !important;
  background-color:var(--surface) !important; border:var(--bd) !important; transition:border-color .15s; }
[data-baseweb="base-input"], [data-baseweb="base-input"] input, [data-baseweb="base-input"] textarea { background-color:transparent !important; border-radius:var(--r-sm) !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"]:focus-within > div {
  border-color:var(--acc) !important; box-shadow:none !important; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button { border-radius:var(--r) !important; padding:.4rem 1.2rem;
  background:var(--surface) !important; border:var(--bd) !important; box-shadow:none; transition:border-color .15s; }
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover { transform:none; box-shadow:none; border-color:var(--acc) !important; }
.stButton > button:active, .stFormSubmitButton > button:active { transform:none; }
button[kind="primary"], button[kind="primaryFormSubmit"] { background:var(--pink) !important;
  color:var(--acc-ink) !important; border-color:var(--pink) !important; box-shadow:none !important; }
button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover { box-shadow:none !important; border-color:var(--ink) !important; }
[data-testid="stButtonGroup"] { border-radius:var(--r) !important; padding:.4rem .55rem; }
button[data-variant="segmented_control"] { border-radius:8px !important; background:transparent !important; color:var(--p-ink2) !important;
  border:1px solid transparent !important; transition:border-color .15s; }
button[data-variant="segmented_control"]:hover { background:var(--surface2) !important; transform:none; color:var(--ink) !important; }
button[data-variant="segmented_control"][data-selected="true"] { color:var(--ink) !important; border-color:var(--acc) !important;
  background:var(--surface2) !important; box-shadow:none !important; }
.pill, .tag, .g-uso .stato, .g-agente .stato, .g-agente .chips span, .g-chip { border-radius:var(--r-sm) !important; }
code { border-radius:8px; }
.g-agente .ev::before { border-color:var(--acc); }
[class*="st-key-sez_"] h3 { border-left:0; padding-left:0; }
[class*="st-key-plancia_guardian"]::before, [class*="st-key-plancia_utilizzo"]::before { color:var(--pk2); }
.rx-voce .rx-m { stroke:var(--pk); } .rx-voce .rx-c { fill:var(--pk); } .rx-voce .rx-l::before { background:var(--pk2); }
/* ==== Giro 11: audit accessibilita ==== */
::placeholder { color:var(--p-mute) !important; opacity:1 !important; }
.g-wrap:focus-visible, .g-feed:focus-visible, button[data-variant="segmented_control"]:focus-visible { outline:2px solid var(--pk) !important; outline-offset:2px; }
.g-table td { overflow-wrap:anywhere; }
.g-table td.nw, .g-table th { white-space:nowrap; overflow-wrap:normal; }
.g-wrap { overflow-x:auto; }
/* contrasto forzato: il testo trasparente dei titoli sparirebbe, si torna al colore di sistema */
@media (forced-colors: active) { h1, h2, [class*="st-key-sez_"] h3 { background:none !important; -webkit-text-fill-color:CanvasText !important; color:CanvasText !important; } }
/* ==== Giro 10: chat, suggerimenti, barra, siti demo ==== */
[class*="st-key-g_barra"] { margin-bottom:.45rem; }
[class*="st-key-g_barra"] button, [class*="st-key-g_barra"] [data-testid="stPopover"] > div > button { height:40px; min-height:40px !important; border-radius:var(--r) !important;
  white-space:nowrap; padding:0 .9rem; }
[class*="st-key-g_barra"] [data-testid="stToggle"], [class*="st-key-g_barra"] label { min-height:40px; align-items:center; display:flex; justify-content:center;
  border:var(--bd); border-radius:var(--r); background:var(--surface); padding:0 .6rem; }
[class*="st-key-g_barra"] [data-testid="stColumn"] { min-width:0; }
[class*="st-key-g_barra"] [data-testid="stColumn"]:last-child { overflow:hidden; display:flex; justify-content:flex-end; }
[class*="st-key-g_sugg"] [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.5rem; }
[class*="st-key-g_sugg"] [data-testid="stColumn"] { flex:1 1 auto !important; min-width:max-content !important; width:auto !important; }
[class*="st-key-g_sugg"] button { border-radius:var(--r) !important; min-height:38px; white-space:nowrap;
  background:var(--surface) !important; border:var(--bd) !important; }
[class*="st-key-g_sugg"] button:hover { border-color:var(--acc) !important; box-shadow:none; }
/* storico ancorato in fondo: DOM in ordine inverso + column-reverse = parte dall'ultimo messaggio, senza JS */
[class*="st-key-chat_storico"] { padding:.35rem; }
/* in Streamlit 1.67 la classe st-key-chat_storico sta SUL blocco verticale scorrevole: va invertito lui (non i blocchi dentro i messaggi) */
[class*="st-key-chat_storico"][data-testid="stVerticalBlock"], [class*="st-key-chat_storico"] > [data-testid="stVerticalBlock"] { display:flex !important; flex-direction:column-reverse !important; justify-content:flex-start !important; gap:.6rem; }
[class*="st-key-chat_storico"][data-testid="stVerticalBlock"] > * { flex-shrink:0; }
[class*="st-key-chat_storico"] [data-testid="stChatMessage"] { max-width:86%; width:fit-content; min-width:0; padding:.55rem .9rem !important; border-radius:var(--r-md) !important;
  overflow-wrap:anywhere; word-break:break-word; }
[class*="st-key-chat_storico"] [data-testid="stChatMessage"] * { max-width:100%; overflow-wrap:anywhere; }
[class*="st-key-chat_storico"] pre { white-space:pre-wrap !important; overflow-x:auto; }
[class*="st-key-chat_storico"] [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { align-self:flex-end; flex-direction:row-reverse;
  border-right:3px solid var(--pink) !important; background:var(--surface2) !important; }
[class*="st-key-chat_storico"] [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) { align-self:flex-start;
  border-left:3px solid var(--acc) !important; background:var(--surface2) !important; }
/* siti demo: cornice attorno all'anteprima */
[class*="st-key-siti_cornice"] { border:var(--bd); border-radius:var(--r); padding:.5rem; overflow:hidden;
  background:var(--surface); margin:.4rem 0 .6rem; }
[class*="st-key-siti_cornice"] iframe { border-radius:var(--r-md); border:0; width:100%; max-height:70vh; background:#fff; }
/* barra laterale: catalogo agenti e skill */
section[data-testid="stSidebar"] { background:var(--bg) !important; border-right:var(--bd); z-index:2; }
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] { min-height:2.2rem; }
.g-side-titolo { font-weight:700; letter-spacing:.06em; text-transform:uppercase; font-size:.8rem; color:#9be9f7; margin:.2rem 0 .4rem; }
.g-side-gruppo { display:flex; justify-content:space-between; align-items:center; margin:.9rem 0 .35rem; font-weight:700; font-size:1rem; color:#e8f1ff; }
.g-side-gruppo span { min-width:1.7rem; text-align:center; padding:.05rem .5rem; border-radius:999px; font-size:.78rem; color:#08131a;
  background:var(--acc); }
section[data-testid="stSidebar"] [data-testid="stExpander"] details { border:var(--bd); border-radius:var(--r); background:var(--surface); margin-bottom:.4rem; }
section[data-testid="stSidebar"] [data-testid="stExpander"] summary { min-height:36px; border-radius:var(--r-md); }
section[data-testid="stSidebar"] .stButton button { min-height:38px; height:38px; justify-content:flex-start; text-align:left; border-radius:var(--r-sm); font-size:.88rem;
  text-transform:none !important; letter-spacing:0 !important; font-weight:500; padding:.25rem .7rem; background:var(--surface) !important; border:var(--bd) !important; color:#e8f1ff; }
section[data-testid="stSidebar"] .stButton button:hover { border-color:var(--acc) !important; background:var(--surface2) !important; }
section[data-testid="stSidebar"] .stButton button:focus-visible, section[data-testid="stSidebar"] summary:focus-visible, section[data-testid="stSidebar"] input:focus-visible {
  outline:2px solid #22d3ee !important; outline-offset:2px; }
@media (min-width:901px) { section[data-testid="stSidebar"] { width:300px !important; min-width:300px !important; } }
section[data-testid="stSidebar"] [data-testid="stExpander"] details > div { padding-left:.4rem; padding-right:.4rem; }
section[data-testid="stSidebar"] .stButton button, section[data-testid="stSidebar"] .stButton button > div, section[data-testid="stSidebar"] .stButton button > div > span, section[data-testid="stSidebar"] .stButton button [data-testid="stMarkdownContainer"] { display:flex; justify-content:flex-start !important; text-align:left !important; width:100%; }
section[data-testid="stSidebar"] .stButton button p { text-transform:none !important; letter-spacing:0 !important; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:left; margin:0; min-width:0; }
/* pop-up: stessa superficie delle card, X grande e con focus */
div[role="dialog"] button[aria-label="Close"] { min-width:36px; min-height:36px; width:36px; height:36px; border-radius:999px; display:inline-flex; align-items:center; justify-content:center; }
div[role="dialog"] button[aria-label="Close"]:hover { background:var(--surface2); }
div[role="dialog"] button[aria-label="Close"]:focus-visible { outline:2px solid #22d3ee !important; outline-offset:2px; }
/* barra Guardian: a capo invece di troncare le etichette */
[class*="st-key-g_barra"] [data-testid="stHorizontalBlock"] { flex-wrap:wrap; gap:.4rem; }
[class*="st-key-g_barra"] [data-testid="stColumn"] { flex:1 1 auto; width:auto; min-width:max-content; }
[class*="st-key-g_barra"] button { padding:0 .7rem; }
/* telefono: niente scroll orizzontale, colonne impilate, tocco >= 40px, testo >= 15px */
@media (max-width:900px) {
  .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .block-container { overflow-x:hidden !important; max-width:100vw; }
  section[data-testid="stSidebar"] { width:auto; min-width:0; }
  [data-testid="stMain"] [data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; gap:.5rem; }
  [data-testid="stMain"] [data-testid="stColumn"] { flex:1 1 100% !important; width:100% !important; min-width:0 !important; }
  [class*="st-key-g_barra"] [data-testid="stColumn"] { flex:1 1 auto !important; width:auto !important; min-width:max-content !important; }
  [data-testid="stSegmentedControl"], [data-testid="stSegmentedControl"] > div { overflow-x:auto; -webkit-overflow-scrolling:touch; max-width:100%; scrollbar-width:thin; }
  [data-testid="stSegmentedControl"] [role="group"], [data-testid="stSegmentedControl"] div[role="radiogroup"] { flex-wrap:nowrap; width:max-content; }
  .stButton > button, button[data-variant="segmented_control"], [data-testid="stSegmentedControl"] button { min-height:40px; }
  .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button { font-size:max(15px, 1em); }
}
@media (prefers-reduced-motion: reduce) {
  .g-card, .g-tile, .g-agente, .stButton > button, button[data-variant="segmented_control"] { transition:none !important; }
  .g-card:hover, .g-tile:hover, .g-agente:hover, .stButton > button:hover, button[data-variant="segmented_control"]:hover, .stButton > button:active { transform:none !important; } }
</style>
"""


STATI_REATTORE = {"riposo": "In attesa", "ascolto": "In ascolto", "pensiero": "Sto pensando", "voce": "Sto parlando"}


def reattore(stato: str = "riposo") -> str:
    """Anello SVG del Guardian: 4 stati (riposo/ascolto/pensiero/voce), etichetta testuale in aria-live. Solo stringhe fisse."""
    if stato not in STATI_REATTORE:
        stato = "riposo"
    svg = logo_svg({"riposo": "riposo", "ascolto": "ascolto", "pensiero": "pensa", "voce": "parla"}[stato], 56)
    return (f"<div class='reattore rx-{stato}'>{svg}<div class='rx-t'><span class='rx-k'>STATO</span>"
            f"<span class='rx-l' role='status' aria-live='polite'>{STATI_REATTORE[stato]}</span></div></div>")

