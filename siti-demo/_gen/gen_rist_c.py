# -*- coding: utf-8 -*-
import os
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_CSS = """
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);font:1.0625rem/1.6 var(--body);-webkit-text-size-adjust:100%}
h1,h2,h3{font-family:var(--head);line-height:1.15;margin:0 0 .5em}
h1{font-size:clamp(2.2rem,9vw,4rem)}
h2{font-size:clamp(1.6rem,6vw,2.4rem)}
h3{font-size:1.15rem}
a{color:var(--link)}
:focus-visible{outline:3px solid var(--focus);outline-offset:3px;border-radius:4px}
.wrap{max-width:60rem;margin:0 auto;padding:0 16px}
.skip{position:absolute;left:-999px;top:8px;background:var(--btn);color:var(--btntx);padding:8px 12px;z-index:9}
.skip:focus{left:8px}
header.top{background:var(--hbg);color:var(--htx);padding:14px 0}
header.top .wrap{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.brand{font-family:var(--head);font-size:1.25rem;font-weight:700}
nav a{color:var(--htx);margin-right:14px;display:inline-block;padding:8px 0}
.hero{background:var(--hero);color:var(--herotx);padding:48px 0 56px}
.hero p{max-width:34rem;font-size:1.15rem}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:12px 22px;margin:0 8px 8px 0;background:var(--btn);color:var(--btntx);border:2px solid var(--btn);border-radius:var(--rad);font:700 1rem var(--body);text-decoration:none;cursor:pointer;transition:transform .25s ease,box-shadow .25s ease}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 18px rgba(0,0,0,.25)}
section{padding:48px 0}
section.alt{background:var(--bg2)}
.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:.8rem;font-weight:700;color:var(--accent);margin:0 0 .6em}
.hero .eyebrow{color:inherit}
.photo{display:block;width:100%;height:auto;border-radius:var(--rad);margin:0 0 20px;border:1px solid var(--line)}
.grid{display:grid;gap:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--rad);padding:20px}
.menu{list-style:none;margin:0;padding:0}
.menu li{display:flex;justify-content:space-between;gap:16px;padding:12px 0;border-bottom:1px dashed var(--line)}
.menu .pr{white-space:nowrap;font-weight:700}
.todo{font-style:italic;color:var(--mut)}
form{display:grid;gap:16px}
label{display:block;font-weight:700;margin-bottom:4px}
input,textarea{width:100%;min-height:48px;padding:10px 12px;font:1rem var(--body);color:var(--tx);background:var(--inbg);border:2px solid var(--inbd);border-radius:var(--rad)}
textarea{min-height:90px}
.row2{display:grid;gap:16px}
#esito{margin:0;padding:14px;border-radius:var(--rad);background:var(--card);border:2px solid var(--accent);font-weight:700}
#esito[hidden]{display:none}
footer{background:var(--hbg);color:var(--htx);padding:32px 0;text-align:center}
.rise{animation:rise .8s cubic-bezier(.2,.7,.2,1) both}
.rise.d2{animation-delay:.15s}.rise.d3{animation-delay:.3s}
@keyframes rise{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@media(min-width:42rem){.grid.c2{grid-template-columns:1fr 1fr}.row2{grid-template-columns:1fr 1fr}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{animation:none!important;transition:none!important}}
"""

SITES = [
 dict(file="pani-e-casu.html", nome="Pani e Casu", tel="+39 070 858 66 29", telh="+390708586629",
  ind="Via Santa Croce 51, Cagliari", tag="Ristorante a Cagliari",
  intro="Menu, prenotazione del tavolo e come arrivare, in una pagina leggibile da telefono.",
  ph="%23e9d8bd", ph2="%23a4452c",
  css="""
:root{--bg:#fbf5e8;--bg2:#f1e6cf;--tx:#2e2118;--mut:#5c4a3b;--head:Georgia,'Times New Roman',serif;--body:Georgia,'Times New Roman',serif;
--hbg:#3b2a1d;--htx:#fbf5e8;--hero:#a4452c;--herotx:#ffffff;--btn:#3b2a1d;--btntx:#ffffff;--accent:#8a3320;--link:#8a3320;--focus:#1b5e8a;--card:#fffaf0;--line:#cdb994;--rad:6px;--inbg:#ffffff;--inbd:#6b563f}
.hero{background-image:repeating-linear-gradient(45deg,rgba(255,255,255,.07) 0 14px,transparent 14px 28px)}
.hero .btn{background:#fbf5e8;color:#3b2a1d;border-color:#fbf5e8}
.hero .btn+.btn{background:transparent;color:#fff;border-color:#fff}
h2{border-bottom:3px double var(--accent);padding-bottom:.3em}
"""),
 dict(file="ristorante-51.html", nome="Ristorante 51", tel="+39 070 7339061", telh="+390707339061",
  ind="Via Pola 51, 09123 Cagliari", tag="Ristorante a Cagliari",
  intro="Menu, prenotazione del tavolo e come arrivare: tutto in una pagina essenziale.",
  ph="%23202b3f", ph2="%23d4b46a",
  css="""
:root{--bg:#10192a;--bg2:#17233a;--tx:#eef0f4;--mut:#b6bfd0;--head:'Palatino Linotype',Palatino,'Book Antiqua',serif;--body:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
--hbg:#0a101c;--htx:#eef0f4;--hero:linear-gradient(160deg,#17233a,#0a101c);--herotx:#eef0f4;--btn:#d4b46a;--btntx:#10192a;--accent:#d4b46a;--link:#e6c887;--focus:#ffd86b;--card:#1b2943;--line:#35466a;--rad:2px;--inbg:#0e1626;--inbd:#8c9ab8}
h1,h2{font-weight:400;letter-spacing:.04em}
h1{text-transform:uppercase}
.hero{text-align:center;border-bottom:1px solid var(--accent)}
.hero p{margin-left:auto;margin-right:auto}
.hero .btn+.btn{background:transparent;color:#eef0f4;border-color:#d4b46a}
h2::after{content:"";display:block;width:60px;height:1px;background:var(--accent);margin-top:.5em}
"""),
 dict(file="el-carnicero-assemini.html", nome="El Carnicero Assemini", tel="070 7344038", telh="0707344038",
  ind="Via Pio IX 44, 09032 Assemini", tag="Carne alla brace",
  intro="Menu, prenotazione del tavolo e come arrivare, pensati per il telefono.",
  ph="%23241a17", ph2="%23e8541e",
  css="""
:root{--bg:#1c1514;--bg2:#271c1a;--tx:#f6ece6;--mut:#cdb9ae;--head:Impact,'Arial Narrow Bold','Franklin Gothic Medium',Haettenschweiler,sans-serif;--body:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
--hbg:#0f0a09;--htx:#f6ece6;--hero:#1c1514;--herotx:#f6ece6;--btn:#ff6a2b;--btntx:#1a0e0a;--accent:#ff8a4d;--link:#ffa574;--focus:#ffe14d;--card:#2f2220;--line:#5a403a;--rad:0;--inbg:#140e0d;--inbd:#b99d92}
h1,h2,h3{text-transform:uppercase;letter-spacing:.03em;font-weight:400}
h1{font-size:clamp(2.6rem,12vw,5.5rem)}
.hero{position:relative;overflow:hidden;border-bottom:6px solid #ff6a2b}
.hero::before{content:"";position:absolute;inset:auto 0 0 0;height:70%;background:linear-gradient(to top,rgba(255,106,43,.45),rgba(255,106,43,0));transform-origin:bottom;animation:brace 3.5s ease-in-out infinite alternate}
.hero .wrap{position:relative}
@keyframes brace{from{opacity:.55;transform:scaleY(.9)}to{opacity:1;transform:scaleY(1.05)}}
.hero .btn+.btn{background:transparent;color:#f6ece6;border-color:#ff8a4d}
h2{border-left:8px solid #ff6a2b;padding-left:12px}
"""),
]

CATS = ["Antipasti", "Primi", "Secondi", "Dolci", "Bevande"]


def build(s):
    item = '<li><span class="todo">Voce da inserire</span><span class="pr todo">&euro; da inserire</span></li>'
    menu = "".join(
        f'<div class="card rise"><h3>{c}</h3><ul class="menu">{item}{item}</ul></div>' for c in CATS)
    svg = ("data:image/svg+xml;utf8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 400'%3E"
           f"%3Crect width='800' height='400' fill='{s['ph']}'/%3E%3Ccircle cx='400' cy='200' r='70' fill='none' stroke='{s['ph2']}' stroke-width='8'/%3E"
           f"%3Cpath d='M360 200h80M400 160v80' stroke='{s['ph2']}' stroke-width='8'/%3E%3C/svg%3E")
    img = f'<img class="photo" src="{svg}" alt="foto da inserire (con permesso del titolare)" width="800" height="400">'
    n = s["nome"]
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{n} - bozza dimostrativa</title>
<meta name="description" content="Bozza dimostrativa del sito di {n}: menu, prenotazione del tavolo, orari e come arrivare. Non pubblicata.">
<meta name="robots" content="noindex, nofollow">
<style>{BASE_CSS}{s['css']}</style>
</head>
<body>
<a class="skip" href="#main">Vai al contenuto</a>
<header class="top"><div class="wrap">
<span class="brand">{n}</span>
<nav aria-label="Sezioni"><a href="#menu">Menu</a><a href="#prenota">Prenota</a><a href="#orari">Orari</a><a href="#dove">Dove siamo</a></nav>
</div></header>
<main id="main">
<div class="hero"><div class="wrap">
<p class="eyebrow rise">{s['tag']}</p>
<h1 class="rise d2">{n}</h1>
<p class="rise d3">{s['intro']}</p>
<p class="rise d3"><a class="btn" href="tel:{s['telh']}">Chiama {s['tel']}</a><a class="btn" href="#prenota">Prenota un tavolo</a></p>
</div></div>
<section id="menu"><div class="wrap">
<p class="eyebrow">Menu</p><h2>Il menu</h2>
{img}
<p class="todo">Piatti e prezzi da inserire: i contenuti verranno forniti dal titolare.</p>
<div class="grid c2">{menu}</div>
</div></section>
<section id="prenota" class="alt"><div class="wrap">
<p class="eyebrow">Prenotazione</p><h2>Prenota il tavolo</h2>
<p>Modulo dimostrativo: non invia nulla. Per prenotare davvero, chiama il <a href="tel:{s['telh']}">{s['tel']}</a>.</p>
<form id="f">
<div><label for="nome">Nome</label><input id="nome" name="nome" autocomplete="name"></div>
<div class="row2">
<div><label for="data">Data</label><input id="data" name="data" type="date"></div>
<div><label for="ora">Ora</label><input id="ora" name="ora" type="time"></div>
</div>
<div><label for="pers">Numero di persone</label><input id="pers" name="pers" type="number" min="1" max="20" inputmode="numeric"></div>
<div><label for="note">Note</label><textarea id="note" name="note"></textarea></div>
<button class="btn" type="submit">Richiedi prenotazione (demo)</button>
<p id="esito" role="status" tabindex="-1" hidden>demo: nessun dato inviato</p>
</form>
</div></section>
<section id="orari"><div class="wrap">
<p class="eyebrow">Orari</p><h2>Orari di apertura</h2>
<p class="todo">Orari da inserire (da confermare con il titolare).</p>
<p><a class="btn" href="tel:{s['telh']}">Chiama {s['tel']}</a></p>
</div></section>
<section id="dove" class="alt"><div class="wrap">
<p class="eyebrow">Come arrivare</p><h2>Dove siamo</h2>
<address style="font-style:normal;font-size:1.2rem">{n}<br>{s['ind']}</address>
</div></section>
</main>
<footer><div class="wrap"><p>Bozza dimostrativa preparata per {n} &mdash; non pubblicata</p></div></footer>
<script>
document.getElementById('f').addEventListener('submit',function(e){{e.preventDefault();var o=document.getElementById('esito');o.hidden=false;o.focus();}});
</script>
</body>
</html>
"""


for s in SITES:
    with open(os.path.join(OUT, s["file"]), "w", encoding="utf-8", newline="\n") as f:
        f.write(build(s))
    print("ok", s["file"])
