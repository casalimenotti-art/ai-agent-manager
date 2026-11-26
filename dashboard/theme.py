"""Tema cyberpunk-minimal di Guardian: CSS, componenti HTML e grafico CPU.

Colori dei DATI (grafico) validati con validate_palette.js (dark, superficie #080a12):
ciano #00aed1 + arancio #ff5f45 -> lightness, chroma, CVD ΔE 20.5, contrasto: tutti PASS.
I neon più accesi (#00f0ff, #ff2bd6) sono usati solo per decorazioni, mai per codificare dati.
Nessun font/risorsa esterna: tutto è locale.
"""
from __future__ import annotations

import html
import re

import altair as alt
import pandas as pd

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
html, body, .stApp {{ background:var(--bg) !important; color:var(--ink); font-family:var(--mono); }}
.stApp {{
  background-image:
    radial-gradient(900px 420px at 12% -8%, rgba(0,240,255,.10), transparent 60%),
    radial-gradient(800px 420px at 100% 0%, rgba(255,43,214,.08), transparent 60%),
    linear-gradient(rgba(0,240,255,.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,240,255,.035) 1px, transparent 1px);
  background-size:auto, auto, 44px 44px, 44px 44px;
  background-attachment: fixed;
}}
.stApp::after {{ content:""; position:fixed; inset:0; pointer-events:none; z-index:9999;
  background:repeating-linear-gradient(0deg, rgba(255,255,255,.012) 0 1px, transparent 1px 3px); }}
[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stToolbar"], #MainMenu, footer {{ visibility:hidden; }}
.block-container {{ padding-top:1.6rem; max-width:1380px; }}
h1,h2,h3,h4,p,span,label,div {{ font-family:var(--mono); }}
h3, h4 {{ text-transform:uppercase; letter-spacing:.18em; font-size:.78rem !important; color:var(--ink2);
  font-weight:600 !important; margin-top:.4rem; }}
h3::before, h4::before {{ content:"// "; color:var(--cy); }}
hr {{ border-color:var(--line) !important; }}
a {{ color:var(--cy); }}

/* header */
.g-head {{ display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; flex-wrap:wrap;
  border-bottom:1px solid var(--line); padding-bottom:.9rem; margin-bottom:.4rem; }}
.g-logo {{ font-size:2.1rem; font-weight:800; letter-spacing:.32em; line-height:1; color:var(--ink);
  text-shadow:-2px 0 rgba(255,43,214,.55), 2px 0 rgba(0,240,255,.55), 0 0 24px rgba(0,240,255,.35); }}
.g-logo b {{ color:var(--cy); }}
.g-tag {{ color:var(--ink2); font-size:.72rem; letter-spacing:.28em; margin-top:.55rem; text-transform:uppercase; }}
.g-chips {{ display:flex; gap:.5rem; flex-wrap:wrap; }}
.g-chip {{ border:1px solid var(--line); color:var(--ink2); padding:.28rem .65rem; font-size:.7rem;
  letter-spacing:.14em; text-transform:uppercase; background:rgba(13,16,32,.7); }}
.g-chip i, .pill i {{ display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--ok);
  margin-right:.45rem; box-shadow:0 0 8px var(--ok); vertical-align:middle; }}

/* tabs */
[data-baseweb="tab-list"] {{ gap:.4rem; border-bottom:1px solid var(--line); }}
button[data-baseweb="tab"] {{ background:transparent; color:var(--ink2); letter-spacing:.16em; text-transform:uppercase;
  font-size:.75rem; padding:.7rem 1rem; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color:var(--cy); text-shadow:0 0 12px rgba(0,240,255,.55); }}
[data-baseweb="tab-highlight"] {{ background:var(--cy) !important; box-shadow:0 0 12px var(--cy); height:2px; }}
[data-baseweb="tab-border"] {{ background:transparent; }}

/* cards */
.g-card {{ position:relative; background:linear-gradient(180deg, rgba(18,23,46,.85), rgba(10,12,26,.9));
  border:1px solid var(--line); padding:.95rem 1.05rem; margin-bottom:.7rem; min-height:6.1rem;
  box-shadow:0 0 0 1px rgba(0,0,0,.4) inset, 0 8px 28px rgba(0,0,0,.35); }}
.g-card::before, .g-card::after {{ content:""; position:absolute; width:12px; height:12px; pointer-events:none; }}
.g-card::before {{ top:-1px; left:-1px; border-top:2px solid var(--cy); border-left:2px solid var(--cy); }}
.g-card::after {{ bottom:-1px; right:-1px; border-bottom:2px solid var(--mg); border-right:2px solid var(--mg); }}
.g-label {{ font-size:.72rem; letter-spacing:.22em; text-transform:uppercase; color:var(--ink2); }}
.g-value {{ font-size:2rem; font-weight:700; color:var(--ink); margin-top:.3rem; line-height:1.1;
  text-shadow:0 0 18px rgba(0,240,255,.28); font-variant-numeric:tabular-nums; }}
.g-value small {{ font-size:.85rem; color:var(--ink2); margin-left:.25rem; font-weight:500; text-shadow:none; }}
.g-sub {{ font-size:.7rem; color:var(--ink2); margin-top:.35rem; }}
.g-gauge {{ height:3px; background:#151b34; margin-top:.55rem; }}
.g-gauge i {{ display:block; height:100%; background:linear-gradient(90deg,var(--cy),var(--mg)); box-shadow:0 0 10px var(--cy); }}
.g-skill {{ min-height:8.2rem; }}
.g-skill .g-name {{ color:var(--cy); font-weight:700; letter-spacing:.06em; }}
.g-skill .g-desc {{ color:var(--ink2); font-size:.78rem; margin-top:.45rem; line-height:1.45; }}
.g-skill:hover {{ border-color:rgba(0,240,255,.55); box-shadow:0 0 22px rgba(0,240,255,.14); }}

/* tabella agenti */
.g-table {{ width:100%; border-collapse:collapse; font-size:.78rem; }}
.g-table th {{ text-align:left; color:var(--ink2); font-weight:500; font-size:.65rem; letter-spacing:.2em;
  text-transform:uppercase; padding:.55rem .7rem; border-bottom:1px solid var(--line); }}
.g-table td {{ padding:.65rem .7rem; border-bottom:1px solid rgba(28,35,64,.6); color:var(--ink); vertical-align:middle; }}
.g-table tr:hover td {{ background:rgba(0,240,255,.04); }}
.g-table td.msg {{ max-width:420px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:var(--ink2); }}
.g-table td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
.g-wrap {{ border:1px solid var(--line); background:rgba(10,12,26,.72); overflow-x:auto; }}
.pill {{ display:inline-block; padding:.18rem .6rem; font-size:.66rem; letter-spacing:.16em; border:1px solid; white-space:nowrap; }}
.pill.on {{ color:var(--ok); border-color:rgba(61,255,160,.5); background:rgba(61,255,160,.07); }}
.pill.off {{ color:var(--ink2); border-color:var(--line); }}
.pill.off i {{ background:#4a5578; box-shadow:none; }}
.tool {{ color:var(--warn); }}

/* widget */
.stButton > button, .stFormSubmitButton > button {{ background:transparent; color:var(--cy); border:1px solid rgba(0,240,255,.45);
  border-radius:0; letter-spacing:.14em; text-transform:uppercase; font-size:.72rem; font-family:var(--mono);
  transition:all .15s; }}
.stButton > button:hover, .stFormSubmitButton > button:hover {{ background:rgba(0,240,255,.12); border-color:var(--cy);
  color:#fff; box-shadow:0 0 16px rgba(0,240,255,.35); }}
button[kind="primaryFormSubmit"], button[kind="primary"] {{ background:rgba(255,43,214,.12) !important; color:#ffd6f7 !important;
  border-color:rgba(255,43,214,.6) !important; }}
button[kind="primaryFormSubmit"]:hover, button[kind="primary"]:hover {{ box-shadow:0 0 18px rgba(255,43,214,.45) !important;
  background:rgba(255,43,214,.22) !important; }}
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {{ background:rgba(13,16,32,.9) !important;
  border-radius:0 !important; border:1px solid var(--line) !important; }}
[data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within, [data-baseweb="select"]:focus-within > div {{
  border-color:var(--cy) !important; box-shadow:0 0 14px rgba(0,240,255,.22) !important; }}
input, textarea {{ color:var(--ink) !important; font-family:var(--mono) !important; }}
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
.g-logo {{ animation:g-boot .9s steps(1,end) 1; }}
@keyframes g-boot {{ 0%{{opacity:0; transform:translateX(-3px)}} 15%{{opacity:1; transform:translateX(2px)}} 30%{{opacity:.2}} 45%{{opacity:1; transform:none}} 60%{{opacity:.5}} 100%{{opacity:1}} }}
:focus-visible {{ outline:2px solid var(--cy) !important; outline-offset:2px; }}
.g-dot {{ animation:g-pulse 1.8s ease-in-out infinite; }}
@keyframes g-pulse {{ 50% {{ opacity:.45; }} }}
@media (prefers-reduced-motion: reduce) {{ .g-dot, .pill.on i, .g-logo {{ animation:none; }} }}
@media (max-width: 700px) {{ .g-logo {{ font-size:1.5rem; letter-spacing:.2em; }} .g-value {{ font-size:1.5rem; }} }}
</style>
"""


def esc(x) -> str:
    return html.escape(str(x), quote=True)


def intestazione(sorgente: str, permessi: str, ogni_s: int) -> str:
    return (
        "<div class='g-head'><div><div class='g-logo'>GUARD<b>I</b>AN</div>"
        "<div class='g-tag'>claude code // control room</div></div>"
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


def card_skill(nome: str, descrizione: str, origine: str = "installata") -> str:
    d = descrizione if len(descrizione) < 170 else descrizione[:167] + "…"
    return (f"<div class='g-card g-skill'><div class='g-name'>{esc(nome)}</div><div class='g-desc'>{esc(d)}</div>"
            f"<div class='g-sub'>{esc(ETICHETTA_ORIGINE.get(origine, origine))}</div></div>")


def tabella_agenti(righe: list[dict], fa) -> str:
    if not righe:
        return ""
    corpo = []
    for r in righe:
        on = r["stato"] == "al lavoro"
        pill = (f"<span class='pill {'on' if on else 'off'}'><i class='{'g-dot' if on else ''}'></i>"
                f"{'AL LAVORO' if on else 'FERMO'}</span>")
        tipo = r["tipo"] + (f" · {r['agente'][:7]}" if r["agente"] else "")
        msg = r["messaggio"]
        corpo.append(
            f"<tr><td>{pill}</td><td>{esc(r['progetto'])}</td><td>{esc(tipo)}</td>"
            f"<td class='tool'>{esc(r['strumento'] or '—')}</td>"
            f"<td class='msg' title='{esc(msg)}'>{esc(msg[:200])}</td>"
            f"<td class='num'>{esc(fa(r['ultimo_agg']))}</td><td class='num'>${r['costo']:.2f}</td></tr>"
        )
    testa = "".join(f"<th>{h}</th>" for h in ("Stato", "Progetto", "Tipo", "Strumento", "Ultimo messaggio", "Agg.", "Costo ≈"))
    return f"<div class='g-wrap'><table class='g-table'><thead><tr>{testa}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"


def tabella_processi(lista: list[dict]) -> str:
    corpo = "".join(
        f"<tr><td class='num'>{p['pid']}</td><td>{esc(p['nome'])}</td><td class='num'>{p['cpu']:.1f}</td>"
        f"<td class='num'>{p['ram_mb']:.1f}</td><td class='msg' title='{esc(p.get('cmd', ''))}'>{esc(p.get('cmd', ''))}</td></tr>"
        for p in lista
    )
    testa = "".join(f"<th>{h}</th>" for h in ("PID", "Nome", "CPU %", "RAM MB", "Comando"))
    return f"<div class='g-wrap'><table class='g-table'><thead><tr>{testa}</tr></thead><tbody>{corpo}</tbody></table></div>"


def grafico_cpu(storico: list[list[float]], n_core: int) -> alt.Chart:
    """Area+linea 2px, fascia al 10%, punto finale con anello, crosshair+tooltip al passaggio.

    storico: righe [secondi_relativi, cpu_totale_pct, cpu_claude_pct_della_macchina].
    """
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
            f"<div class='g-desc'>{esc(voce['descrizione'])}</div>"
            f"<div class='g-sub'>rischio: <b class='risk {classe}'>{esc(rischio)}</b> · {esc(voce['repo'])}</div></div>")


def tabella_clienti(righe: list[dict]) -> str:
    """Lead con punteggio, stato visita e prova. Tutto il testo viene da file scritti da agenti: sempre escapato."""
    if not righe:
        return ""
    import clienti as _c
    corpo = []
    for r in righe:
        fonte = _c.url_sicuro(r.get("fonte", ""))
        link = f"<a href='{esc(fonte)}' target='_blank' rel='noopener noreferrer'>fonte</a>" if fonte else "—"
        on = r["stato"] == "interessato"
        corpo.append(
            f"<tr><td class='num'><b>{r['adattamento']}</b>/5</td><td>{esc(r['azienda'])}</td><td>{esc(r.get('categoria', '—'))}</td>"
            f"<td>{esc(r.get('zona', '—'))}</td><td><span class='pill {'on' if on else 'off'}'><i></i>{esc(r['stato'].upper())}</span></td>"
            f"<td class='msg' title='{esc(r.get('prova', ''))}'>{esc((r.get('opportunita') or r.get('prova') or r.get('motivo') or '—')[:160])}</td>"
            f"<td>{link}</td></tr>")
    testa = "".join(f"<th>{h}</th>" for h in ("Fit", "Attività", "Categoria", "Zona", "Visita", "Opportunità / prova", "Fonte"))
    return f"<div class='g-wrap'><table class='g-table'><thead><tr>{testa}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"


# ---------------------------------------------------------------- navigazione, transizioni, feed agenti
CSS_EXTRA = """
<style>
/* Transizione tra spazi: ogni sezione vive in un contenitore con chiave diversa, quindi al cambio il DOM nasce nuovo
   e l'animazione parte una volta sola (i fragment che si aggiornano dentro non la rifanno). */
[class*="st-key-sez_"] { animation: g-entra .34s cubic-bezier(.2,.7,.2,1) both; }
@keyframes g-entra { from { opacity:0; transform:translateY(16px) scale(.992); filter:blur(3px); }
                     to   { opacity:1; transform:none; filter:none; } }
@media (prefers-reduced-motion: reduce) { [class*="st-key-sez_"] { animation:none; } }

/* barra di navigazione */
[data-testid="stButtonGroup"] [role="radiogroup"] { gap:.35rem; flex-wrap:wrap; }
button[data-variant="segmented_control"] { background:rgba(13,16,32,.85) !important; color:#8b97b3 !important;
  border:1px solid #1c2340 !important; border-radius:0 !important; letter-spacing:.14em; text-transform:uppercase;
  font-size:.7rem !important; padding:.5rem .9rem !important; transition:color .18s, border-color .18s, box-shadow .18s, background .18s; }
button[data-variant="segmented_control"]:hover { color:#e8f1ff !important; border-color:rgba(0,240,255,.5) !important; }
button[data-variant="segmented_control"][data-selected="true"] { color:#00f0ff !important; border-color:#00f0ff !important;
  background:rgba(0,240,255,.10) !important; box-shadow:0 0 16px rgba(0,240,255,.28), inset 0 -2px 0 #00f0ff; }

/* tessere del Centro */
.g-tile { position:relative; background:linear-gradient(180deg, rgba(18,23,46,.9), rgba(10,12,26,.92)); border:1px solid #1c2340;
  padding:1.05rem 1.1rem; min-height:8.2rem; margin-bottom:.4rem; transition:border-color .2s, box-shadow .2s; }
.g-tile::before { content:""; position:absolute; top:-1px; left:-1px; width:14px; height:14px; border-top:2px solid #00f0ff; border-left:2px solid #00f0ff; }
.g-tile:hover { border-color:rgba(0,240,255,.5); box-shadow:0 0 24px rgba(0,240,255,.12); }
.g-tile .t { font-size:.72rem; letter-spacing:.2em; text-transform:uppercase; color:#8b97b3; }
.g-tile .v { font-size:2rem; font-weight:700; margin-top:.3rem; font-variant-numeric:tabular-nums; color:#e8f1ff; }
.g-tile .s { font-size:.78rem; color:#a3aecb; margin-top:.3rem; }

/* feed degli agenti */
.g-feed { border:1px solid #1c2340; background:rgba(10,12,26,.72); max-height:560px; overflow-y:auto; }
.g-ev { display:grid; grid-template-columns:62px 1fr; gap:.2rem .8rem; padding:.7rem .9rem; border-bottom:1px solid rgba(28,35,64,.6); font-size:.8rem; }
.g-ev:hover { background:rgba(0,240,255,.035); }
.g-ev .ora { color:#8b97b3; font-variant-numeric:tabular-nums; }
.g-ev .chi { color:#8b97b3; font-size:.7rem; }
.g-ev .tag { display:inline-block; padding:.05rem .5rem; margin-right:.55rem; font-size:.62rem; letter-spacing:.14em; border:1px solid; text-transform:uppercase; }
.tag.delega { color:#ff6ee7; border-color:rgba(255,43,214,.55); } .tag.web { color:#00d4f2; border-color:rgba(0,212,242,.55); }
.tag.file { color:#fcee0a; border-color:rgba(252,238,10,.5); } .tag.comando { color:#ff8a6b; border-color:rgba(255,95,69,.55); }
.tag.dice, .tag.altro { color:#a3aecb; border-color:#2a3566; }
.g-ev .corpo { color:#e8f1ff; word-break:break-word; } .g-ev .sub { grid-column:2; color:#a3aecb; font-size:.76rem; }
.g-ev .sub b { color:#00d4f2; font-weight:600; } .g-ev a { color:#00d4f2; }
.g-ev.nuovo { animation:g-nuovo 1.2s ease-out; }
@keyframes g-nuovo { from { background:rgba(0,240,255,.18); } to { background:transparent; } }
@media (prefers-reduced-motion: reduce) { .g-ev.nuovo { animation:none; } }
</style>
"""

_TAG = {"delega": ("delega", "DELEGA"), "web-ricerca": ("web", "CERCA"), "web-apri": ("web", "APRE"), "browser": ("web", "BROWSER"),
        "file": ("file", "FILE"), "comando": ("comando", "CMD"), "dice": ("dice", "DICE"), "lettura": ("altro", "LEGGE"),
        "strumento": ("altro", "USA")}


def tessera(titolo: str, valore: str, sub: str = "") -> str:
    return f"<div class='g-tile'><div class='t'>{esc(titolo)}</div><div class='v'>{esc(valore)}</div><div class='s'>{esc(sub)}</div></div>"


def feed_attivita(righe: list[dict], fa, ora: float, nuovi_da: float = 0.0) -> str:
    """Feed live: chi fa cosa, quali pagine apre, cosa ne ricava. Tutto il testo viene da agenti: sempre escapato."""
    import time as _t
    import clienti as _c
    if not righe:
        return "<div class='g-feed'><div class='g-ev'><div></div><div class='corpo'>Nessuna attività recente.</div></div></div>"
    out = []
    for e in righe:
        classe, etichetta = _TAG.get(e["tipo"], ("altro", "USA"))
        url = _c.url_sicuro(e.get("url", ""))
        if url:
            dominio = re.sub(r"^https?://", "", url).split("/")[0]
            corpo = f"<a href='{esc(url)}' target='_blank' rel='noopener noreferrer'>{esc(dominio)}</a> {esc(e.get('testo', ''))}"
        else:
            corpo = esc(e.get("testo") or e.get("strumento") or "")
        sub = ""
        if e.get("brief"):
            sub += f"<div class='sub'>Brief: {esc(e['brief'][:320])}</div>"
        if e.get("risultato"):
            sub += f"<div class='sub'><b>ha preso:</b> {esc(e['risultato'][:300])}</div>"
        nuovo = " nuovo" if e["ts"] > nuovi_da > 0 else ""
        out.append(f"<div class='g-ev{nuovo}'><div class='ora'>{_t.strftime('%H:%M:%S', _t.localtime(e['ts']))}</div>"
                   f"<div><span class='tag {classe}'>{etichetta}</span><span class='corpo'>{corpo}</span> "
                   f"<span class='chi'>· {esc(e.get('chi', ''))}</span></div>{sub}</div>")
    return f"<div class='g-feed'>{''.join(out)}</div>"
