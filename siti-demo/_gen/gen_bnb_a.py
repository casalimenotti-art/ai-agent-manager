# -*- coding: utf-8 -*-
import os

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def b(it, en):
    return f'<span lang="it">{it}</span><span lang="en">{en}</span>'


BASE = """
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);font-family:var(--ff);line-height:1.6;font-size:1.0625rem}
html[data-lang="it"] [lang="en"]{display:none}
html[data-lang="en"] [lang="it"]{display:none}
img{max-width:100%;display:block}
a{color:var(--ac)}
:focus-visible{outline:3px solid var(--fo);outline-offset:3px}
.skip{position:absolute;left:-999px;top:0;background:#fff;color:#000;padding:.6rem 1rem;z-index:99}
.skip:focus{left:8px;top:8px}
.wrap{width:min(1080px,100% - 2rem);margin-inline:auto}
header.top{background:var(--hb);color:var(--ht)}
header.top .wrap{display:flex;flex-wrap:wrap;gap:.75rem;align-items:center;justify-content:space-between;padding:.8rem 0}
.brand{font-family:var(--fh);font-weight:700;font-size:1.25rem;color:inherit;text-decoration:none}
nav ul{display:flex;flex-wrap:wrap;gap:.2rem 1rem;list-style:none;margin:0;padding:0}
nav a{color:inherit;text-decoration:none;padding:.3rem .1rem;border-bottom:2px solid transparent;transition:border-color .25s}
nav a:hover{border-color:currentColor}
.lang{display:flex;gap:.25rem}
.lang button{font:inherit;font-size:.9rem;min-width:2.75rem;min-height:2.5rem;border:2px solid currentColor;background:transparent;color:inherit;border-radius:.4rem;cursor:pointer;transition:background .25s,color .25s}
.lang button[aria-pressed="true"]{background:var(--ht);color:var(--hb)}
h1,h2,h3{font-family:var(--fh);line-height:1.15;margin:0 0 .6rem}
h1{font-size:clamp(2rem,6.5vw,3.6rem)}
h2{font-size:clamp(1.55rem,4.5vw,2.3rem)}
section{padding:3.2rem 0}
.hero .wrap{display:grid;gap:2rem;align-items:center}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:2.9rem;padding:.6rem 1.3rem;border-radius:var(--r);font:inherit;font-weight:700;text-decoration:none;border:2px solid var(--ac);background:var(--ac);color:var(--on);cursor:pointer;transition:transform .25s,box-shadow .25s,background .25s}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 18px rgba(0,0,0,.18)}
.btn.alt{background:transparent;color:var(--ac)}
.btn[aria-disabled="true"]{background:transparent;border-style:dashed;color:var(--tx);border-color:var(--tx);cursor:not-allowed}
.btn[aria-disabled="true"]:hover{transform:none;box-shadow:none}
.cta{display:flex;flex-wrap:wrap;gap:.7rem;margin-top:1.3rem}
.ph{border-radius:var(--r);width:100%;height:auto;aspect-ratio:4/3;object-fit:cover;background:var(--card)}
form.av{display:grid;gap:1rem;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));background:var(--card);border:var(--bd);border-radius:var(--r);padding:1.4rem}
form.av .full{grid-column:1/-1}
label{display:block;font-weight:700;margin-bottom:.3rem}
input,textarea{width:100%;font:inherit;padding:.65rem .7rem;border:2px solid var(--ln);border-radius:calc(var(--r)/2);background:#fff;color:#111;min-height:2.9rem}
.status{margin:0;font-weight:700;min-height:1.6em}
.note{font-size:.95rem}
.grid3{display:grid;gap:1.2rem;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.card{background:var(--card);border:var(--bd);border-radius:var(--r);padding:1rem;transition:transform .3s,box-shadow .3s}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 24px rgba(0,0,0,.12)}
.card h3{font-size:1.25rem;margin-top:.8rem}
.card p{margin:.3rem 0}
.rev{border:2px dashed var(--ln);border-radius:var(--r);padding:1.4rem;background:var(--card)}
address{font-style:normal}
footer{background:var(--hb);color:var(--ht);padding:1.6rem 0;text-align:center;font-size:.95rem}
.rise{opacity:0;transform:translateY(18px);animation:rise .8s cubic-bezier(.2,.7,.2,1) forwards}
.d1{animation-delay:.1s}.d2{animation-delay:.25s}.d3{animation-delay:.4s}
@keyframes rise{to{opacity:1;transform:none}}
@media(min-width:820px){.hero .wrap{grid-template-columns:1.1fr .9fr}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}.rise{opacity:1;transform:none}}
"""


def svg(c1, c2):
    s = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'><rect width='400' height='300' fill='{c1}'/>"
         f"<rect x='150' y='100' width='100' height='80' rx='8' fill='none' stroke='{c2}' stroke-width='6'/>"
         f"<circle cx='180' cy='125' r='9' fill='{c2}'/><path d='M150 180l35-30 25 20 20-15 20 25z' fill='{c2}'/></svg>")
    return "data:image/svg+xml," + s.replace("<", "%3C").replace(">", "%3E").replace("#", "%23").replace("'", "%27").replace(" ", "%20")


ALT = "foto da inserire (con permesso del titolare)"

SITES = [
 dict(file="fenicottero-b-b.html", name="Fenicottero B&amp;B", plain="Fenicottero B&amp;B",
  addr="Via Missori 15, Elmas (CA)", wa="393494655946", wa_show="+39 349 465 5946", place=("Elmas", "Elmas"),
  tag=("B&amp;B a Elmas, alle porte di Cagliari", "B&amp;B in Elmas, next to Cagliari"),
  svgc=("#fbd5dc", "#8e1b42"),
  zona=("Elmas è un comune alle porte di Cagliari e ospita l'aeroporto di Cagliari-Elmas. Il territorio si affaccia sullo stagno di Santa Gilla, area lagunare nota per gli uccelli acquatici. Distanze e tempi verso Cagliari e il mare: da inserire con il titolare.",
        "Elmas is a town next to Cagliari and is home to Cagliari-Elmas airport. Its territory looks onto the Santa Gilla lagoon, an area known for water birds. Distances and travel times to Cagliari and the sea: to be added with the owner."),
  css="""
:root{--bg:#fff7f5;--tx:#2a1b2e;--ac:#b3224f;--on:#fff;--fo:#1b3a8a;--hb:#2a1b2e;--ht:#fff;--ff:"Trebuchet MS",Verdana,sans-serif;--fh:"Trebuchet MS",Verdana,sans-serif;--r:1.4rem;--card:#ffe9ee;--ln:#8a5565;--bd:0}
.hero{background:radial-gradient(circle at 85% 20%,#ffd0da 0,transparent 45%),var(--bg);overflow:hidden}
.hero .ph{border-radius:60% 40% 55% 45%/50% 55% 45% 50%;animation:float 7s ease-in-out infinite}
@keyframes float{50%{transform:translateY(-10px) rotate(-1.5deg)}}
h2::after{content:"";display:block;width:3.5rem;height:.4rem;border-radius:1rem;background:var(--ac);margin-top:.5rem}
#camere{background:#fff}
"""),
 dict(file="il-borgo-b-b-villanova.html", name="Il Borgo (B&amp;B Villanova)", plain="Il Borgo (B&amp;B Villanova)",
  addr="Via San Giovanni 194, Cagliari", wa=None, wa_show=None, place=("Villanova", "Villanova"),
  tag=("B&amp;B nel quartiere storico di Villanova, Cagliari", "B&amp;B in the historic Villanova district, Cagliari"),
  svgc=("#e6d3b8", "#7a3418"),
  zona=("Villanova è uno dei quartieri storici di Cagliari, fatto di strade strette e chiese antiche, all'interno della città. Distanze e tempi a piedi verso il centro e le altre zone: da inserire con il titolare.",
        "Villanova is one of Cagliari's historic districts, with narrow streets and old churches, inside the city. Walking distances and times to the centre and other areas: to be added with the owner."),
  css="""
:root{--bg:#f4ece0;--tx:#2b2118;--ac:#8a3b1e;--on:#fff;--fo:#0b3d91;--hb:#3a2517;--ht:#f7eddc;--ff:Georgia,"Times New Roman",serif;--fh:Georgia,"Times New Roman",serif;--r:.25rem;--card:#fbf6ec;--ln:#7a6246;--bd:1px solid #b79f7d}
.hero{border-bottom:6px double #8a3b1e}
.hero .wrap{text-align:center}
.hero .wrap>div{max-width:40rem;margin-inline:auto}
.hero .cta{justify-content:center}
.hero .ph{border:10px solid #fbf6ec;outline:1px solid #8a3b1e;box-shadow:0 10px 30px rgba(58,37,23,.25)}
@media(min-width:820px){.hero .wrap{grid-template-columns:1fr}.hero .ph{max-width:560px;margin-inline:auto}}
h2{text-align:center;font-variant:small-caps;letter-spacing:.06em}
h2::after{content:"\\2766";display:block;color:var(--ac);font-size:1.1rem;margin:.2rem auto 0}
#zona p,#recensioni .rev,#contatti address{max-width:42rem;margin-inline:auto}
#contatti address,#zona p{text-align:center}
"""),
 dict(file="le-tre-nasse-b-b.html", name="Le Tre Nasse B&amp;B", plain="Le Tre Nasse B&amp;B",
  addr="Via Eolie 4, Quartu Sant'Elena", wa="393517007584", wa_show="+39 351 700 7584", place=("Quartu Sant'Elena", "Quartu Sant'Elena"),
  tag=("B&amp;B a Quartu Sant'Elena, zona Margine Rosso", "B&amp;B in Quartu Sant'Elena, Margine Rosso area"),
  svgc=("#cfe7ee", "#0b4f5e"),
  zona=("Quartu Sant'Elena è un comune confinante con Cagliari. La scheda indica la zona di Margine Rosso, vicina al Poetto, la lunga spiaggia che si estende tra Cagliari e Quartu. Distanze e tempi dal B&amp;B: da inserire con il titolare.",
        "Quartu Sant'Elena is a town bordering Cagliari. The listing places the B&amp;B in the Margine Rosso area, near the Poetto, the long beach between Cagliari and Quartu. Distances and times from the B&amp;B: to be added with the owner."),
  css="""
:root{--bg:#f1f8fa;--tx:#0e2530;--ac:#0b6b7a;--on:#fff;--fo:#b45309;--hb:#0b2a3a;--ht:#fff;--ff:"Segoe UI",Roboto,Arial,sans-serif;--fh:"Segoe UI",Roboto,Arial,sans-serif;--r:.8rem;--card:#fff;--ln:#4b7482;--bd:1px solid #bcd7de}
.hero{background:linear-gradient(180deg,#0b2a3a 0,#0f4256 100%);color:#fff;padding-bottom:5rem;position:relative}
.hero .btn{background:#fff;color:#0b2a3a;border-color:#fff}
.hero .btn.alt{background:transparent;color:#fff}
.hero .btn[aria-disabled="true"]{color:#fff;border-color:#fff}
.hero::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:48px;background:var(--bg);-webkit-mask:radial-gradient(circle at 25px 0,transparent 24px,#000 25px) 0 0/50px 48px repeat-x;mask:radial-gradient(circle at 25px 0,transparent 24px,#000 25px) 0 0/50px 48px repeat-x;animation:wave 9s linear infinite}
@keyframes wave{to{-webkit-mask-position:50px 0;mask-position:50px 0}}
.hero .ph{transform:rotate(2deg);box-shadow:0 14px 30px rgba(0,0,0,.35)}
form.av{border-left:6px solid var(--ac)}
"""),
 dict(file="sa-mola-sarda.html", name="Sa Mola Sarda", plain="Sa Mola Sarda",
  addr="Via P. L. da Palestrina 84, Quartu Sant'Elena", wa="393312910504", wa_show="+39 331 291 0504", place=("Quartu Sant'Elena", "Quartu Sant'Elena"),
  tag=("B&amp;B a Quartu Sant'Elena", "B&amp;B in Quartu Sant'Elena"),
  svgc=("#f1dcb0", "#7d1013"),
  zona=("Quartu Sant'Elena è un comune confinante con Cagliari. Tra le due città si trovano il Poetto, lunga spiaggia, e il parco naturale di Molentargius, area umida dove vivono uccelli acquatici. Distanze e tempi dal B&amp;B: da inserire con il titolare.",
        "Quartu Sant'Elena is a town bordering Cagliari. Between the two cities lie the Poetto, a long beach, and the Molentargius nature park, a wetland home to water birds. Distances and times from the B&amp;B: to be added with the owner."),
  css="""
:root{--bg:#fbf1dc;--tx:#1f1410;--ac:#a4161a;--on:#fff;--fo:#003f9e;--hb:#1a1210;--ht:#f8e7c0;--ff:"Palatino Linotype",Palatino,Georgia,serif;--fh:Impact,"Arial Black",Haettenschweiler,sans-serif;--r:0;--card:#fff8e8;--ln:#5a4636;--bd:3px solid #1a1210}
header.top{border-bottom:10px solid transparent;border-image:repeating-linear-gradient(90deg,#a4161a 0 24px,#1a1210 24px 48px,#e0b04a 48px 72px) 10}
h1,h2,h3{text-transform:uppercase;letter-spacing:.04em;font-weight:400}
.hero .wrap>div{border-left:10px solid var(--ac);padding-left:1.2rem}
.hero .ph{border:var(--bd);box-shadow:10px 10px 0 var(--ac)}
.card{box-shadow:6px 6px 0 #1a1210}
.card:hover{transform:translate(-3px,-3px);box-shadow:9px 9px 0 var(--ac)}
.btn{box-shadow:4px 4px 0 #1a1210}
section:nth-of-type(even){background:repeating-linear-gradient(135deg,transparent 0 18px,rgba(164,22,26,.06) 18px 36px)}
"""),
 dict(file="stanze-centro-storico.html", name="Stanze Centro Storico", plain="Stanze Centro Storico",
  addr="Via Goffredo Mameli 22, Cagliari", wa="393462341445", wa_show="+39 346 234 1445", place=("Stampace", "Stampace"),
  tag=("Stanze nel quartiere storico di Stampace, Cagliari", "Rooms in the historic Stampace district, Cagliari"),
  svgc=("#dfe7df", "#3d5a47"),
  zona=("Stampace è uno dei quartieri storici di Cagliari. L'indirizzo è in via Goffredo Mameli, nel centro della città. Distanze e tempi a piedi verso i luoghi di interesse: da inserire con il titolare.",
        "Stampace is one of Cagliari's historic districts. The address is on Via Goffredo Mameli, in the city centre. Walking distances and times to points of interest: to be added with the owner."),
  css="""
:root{--bg:#fafaf7;--tx:#1d241f;--ac:#3d5a47;--on:#fff;--fo:#b3261e;--hb:#fafaf7;--ht:#1d241f;--ff:"Helvetica Neue",Arial,sans-serif;--fh:Georgia,"Times New Roman",serif;--r:0;--card:#f0f2ec;--ln:#55655a;--bd:1px solid #c9d0c6}
header.top{border-bottom:1px solid #1d241f}
h1{font-style:italic;font-weight:400;font-size:clamp(2.4rem,9vw,5.2rem);letter-spacing:-.02em}
h2{font-weight:400;border-top:1px solid #1d241f;padding-top:.8rem}
.hero .ph{filter:grayscale(.3)}
.card{background:transparent;border:0;border-top:1px solid #1d241f;padding-inline:0}
.card:hover{transform:none;box-shadow:none;border-top-width:4px}
footer{background:#1d241f;color:#fafaf7}
.btn{letter-spacing:.08em;text-transform:uppercase;font-size:.9rem}
"""),
]


def page(s):
    n, plain = s["name"], s["plain"]
    img = svg(*s["svgc"])
    if s["wa"]:
        wa = f'<a class="btn alt" href="https://wa.me/{s["wa"]}">{b("Scrivici su WhatsApp", "Message us on WhatsApp")}</a>'
        wa_c = f'<p>WhatsApp: <a href="https://wa.me/{s["wa"]}">{s["wa_show"]}</a></p>'
    else:
        wa = f'<span class="btn alt" aria-disabled="true">{b("WhatsApp (numero da inserire)", "WhatsApp (number to be added)")}</span>'
        wa_c = f'<p>{b("WhatsApp (numero da inserire)", "WhatsApp (number to be added)")}</p>'
    rooms = "".join(
        f'<article class="card"><img class="ph" src="{img}" alt="{ALT}" width="400" height="300" loading="lazy">'
        f'<h3>{b(f"Camera {i} (nome da inserire)", f"Room {i} (name to be added)")}</h3>'
        f'<p>{b("Descrizione, posti letto e servizi: da inserire con il titolare.", "Description, beds and amenities: to be added with the owner.")}</p></article>'
        for i in (1, 2, 3))
    return f'''<!DOCTYPE html>
<html lang="it" data-lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{plain} – bozza dimostrativa del sito</title>
<meta name="description" content="Bozza dimostrativa di sito con richiesta di disponibilità diretta per {plain}, {s["addr"]}. Non pubblicata.">
<meta name="robots" content="noindex,nofollow">
<style>{BASE}{s["css"]}</style>
</head>
<body>
<a class="skip" href="#main">{b("Vai al contenuto", "Skip to content")}</a>
<header class="top"><div class="wrap">
<a class="brand" href="#top">{n}</a>
<nav aria-label="Menu"><ul>
<li><a href="#disponibilita">{b("Disponibilità", "Availability")}</a></li>
<li><a href="#camere">{b("Camere", "Rooms")}</a></li>
<li><a href="#zona">{b("La zona", "The area")}</a></li>
<li><a href="#recensioni">{b("Recensioni", "Reviews")}</a></li>
<li><a href="#contatti">{b("Contatti", "Contact")}</a></li>
</ul></nav>
<div class="lang" role="group" aria-label="Lingua / Language">
<button type="button" data-set="it" aria-pressed="true">IT</button>
<button type="button" data-set="en" aria-pressed="false">EN</button></div>
</div></header>
<main id="main">
<section class="hero" id="top"><div class="wrap">
<div>
<p class="rise">{b(s["tag"][0], s["tag"][1])}</p>
<h1 class="rise d1">{n}</h1>
<p class="rise d2">{b("Chiedi la disponibilità direttamente alla struttura, senza passare da un portale.", "Ask the property for availability directly, without going through a portal.")}</p>
<div class="cta rise d3"><a class="btn" href="#disponibilita">{b("Richiedi disponibilità", "Request availability")}</a>{wa}</div>
</div>
<img class="ph rise d2" src="{img}" alt="{ALT}" width="400" height="300">
</div></section>

<section id="disponibilita"><div class="wrap">
<h2>{b("Richiedi la disponibilità", "Request availability")}</h2>
<p class="note">{b("Modulo dimostrativo: in questa bozza non viene inviato nulla.", "Demo form: nothing is sent from this draft.")}</p>
<form class="av" id="f" novalidate>
<div><label for="arr">{b("Arrivo", "Check-in")}</label><input type="date" id="arr" name="arr"></div>
<div><label for="par">{b("Partenza", "Check-out")}</label><input type="date" id="par" name="par"></div>
<div><label for="osp">{b("Ospiti", "Guests")}</label><input type="number" id="osp" name="osp" min="1" max="20" value="2"></div>
<div class="full"><label for="msg">{b("Note (facoltative)", "Notes (optional)")}</label><textarea id="msg" name="msg" rows="3"></textarea></div>
<div class="full"><button class="btn" type="submit">{b("Invia richiesta", "Send request")}</button></div>
<p class="status full" id="st" role="status" aria-live="polite"></p>
</form>
</div></section>

<section id="camere"><div class="wrap">
<h2>{b("Camere", "Rooms")}</h2>
<div class="grid3">{rooms}</div>
</div></section>

<section id="zona"><div class="wrap">
<h2>{b("La zona: " + s["place"][0], "The area: " + s["place"][1])}</h2>
<p>{b(s["zona"][0], s["zona"][1])}</p>
</div></section>

<section id="recensioni"><div class="wrap">
<h2>{b("Recensioni", "Reviews")}</h2>
<div class="rev"><p>{b("Spazio da collegare: qui compariranno le recensioni degli ospiti, riprese dalle fonti originali e solo con il consenso del titolare.", "Space to be linked: guest reviews will appear here, taken from the original sources and only with the owner's consent.")}</p></div>
</div></section>

<section id="contatti"><div class="wrap">
<h2>{b("Contatti", "Contact")}</h2>
<address><p>{n}<br>{s["addr"]}</p>{wa_c}</address>
</div></section>
</main>
<footer><div class="wrap"><p>Bozza dimostrativa preparata per {n} — non pubblicata</p></div></footer>
<script>
(function(){{
var root=document.documentElement;
function msg(){{return root.getAttribute('data-lang')==='en'?'demo: no data sent':'demo: nessun dato inviato'}}
document.querySelectorAll('.lang button').forEach(function(bt){{bt.addEventListener('click',function(){{
var l=bt.getAttribute('data-set');root.setAttribute('data-lang',l);root.setAttribute('lang',l);
document.querySelectorAll('.lang button').forEach(function(x){{x.setAttribute('aria-pressed',String(x===bt))}});
var st=document.getElementById('st');if(st.textContent){{st.textContent=msg()}}
}})}});
document.getElementById('f').addEventListener('submit',function(e){{e.preventDefault();document.getElementById('st').textContent=msg()}});
}})();
</script>
</body>
</html>
'''


for s in SITES:
    with open(os.path.join(OUT, s["file"]), "w", encoding="utf-8") as f:
        f.write(page(s))
    print("ok", s["file"])
