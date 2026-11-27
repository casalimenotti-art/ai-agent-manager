# -*- coding: utf-8 -*-
import os, urllib.parse
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ph(bg, fg):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"><rect width="400" height="300" fill="%s"/>'
           '<path d="M0 240 L110 130 L190 205 L270 110 L400 240 Z" fill="%s" opacity=".35"/><circle cx="310" cy="70" r="28" fill="%s" opacity=".5"/></svg>') % (bg, fg, fg)
    return "data:image/svg+xml," + urllib.parse.quote(svg)

BASE_CSS = """
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);font:1.0625rem/1.65 var(--ff);-webkit-text-size-adjust:100%}
img{max-width:100%;display:block;height:auto}
a{color:var(--ac)}
:focus-visible{outline:3px solid var(--fc);outline-offset:3px}
.skip{position:absolute;left:-999px;top:0;background:var(--ac);color:var(--on);padding:.6rem 1rem;z-index:20}
.skip:focus{left:0}
.wrap{max-width:68rem;margin:0 auto;padding:0 1.25rem}
header.top{display:flex;gap:1rem;align-items:center;justify-content:space-between;padding:.9rem 1.25rem;max-width:68rem;margin:0 auto;flex-wrap:wrap}
.brand{font-family:var(--fh);font-weight:700;font-size:1.25rem;text-decoration:none;color:var(--tx)}
.lang button{font:inherit;background:transparent;color:var(--tx);border:2px solid var(--ac);padding:.35rem .8rem;border-radius:var(--r);cursor:pointer;min-height:44px}
.lang button[aria-pressed=true]{background:var(--ac);color:var(--on)}
h1,h2,h3{font-family:var(--fh);line-height:1.2;margin:0 0 .6em}
h1{font-size:clamp(2rem,7vw,3.6rem)}h2{font-size:clamp(1.5rem,4.5vw,2.2rem)}
section{padding:3rem 0}
.hero{padding:2.5rem 0 3rem}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:.7rem 1.4rem;border-radius:var(--r);background:var(--ac);color:var(--on);font:inherit;font-weight:700;text-decoration:none;border:2px solid var(--ac);cursor:pointer;transition:transform .25s ease,box-shadow .25s ease}
.btn:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(0,0,0,.2)}
.btn.alt{background:transparent;color:var(--ac)}
.actions{display:flex;gap:.8rem;flex-wrap:wrap;margin-top:1.4rem}
.ph{border-radius:var(--r);width:100%;aspect-ratio:4/3;object-fit:cover;background:var(--card)}
.cards{display:grid;gap:1.25rem;grid-template-columns:1fr}
.card{background:var(--card);border-radius:var(--r);padding:1rem;border:1px solid var(--bd);transition:transform .3s ease,box-shadow .3s ease}
.card:hover{transform:translateY(-4px);box-shadow:0 10px 24px rgba(0,0,0,.14)}
.card h3{margin:.8rem 0 .3rem;font-size:1.2rem}
form.req{background:var(--card);border:1px solid var(--bd);border-radius:var(--r);padding:1.25rem;display:grid;gap:1rem;max-width:36rem}
form.req label{display:grid;gap:.3rem;font-weight:600}
form.req input{font:inherit;padding:.65rem;min-height:48px;border:2px solid var(--ib);border-radius:calc(var(--r)/2);background:var(--bg);color:var(--tx)}
.status{min-height:1.5em;font-weight:700;margin:0}
.note{font-size:.95rem}
.reviews{border:2px dashed var(--ac);border-radius:var(--r);padding:1.5rem;background:var(--card)}
ul.zone{padding-left:1.2rem}
footer{padding:2rem 1.25rem 4rem;text-align:center;border-top:1px solid var(--bd);font-size:.95rem}
.rv{opacity:0;transform:translateY(18px);animation:rv .8s ease forwards}
.rv.d1{animation-delay:.15s}.rv.d2{animation-delay:.3s}
@keyframes rv{to{opacity:1;transform:none}}
@media(min-width:44rem){.cards{grid-template-columns:repeat(3,1fr)}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important;scroll-behavior:auto!important}.rv{opacity:1;transform:none}}
"""

JS = """
(function(){
var L='it';
function set(l){L=l;document.documentElement.lang=l;
document.querySelectorAll('[data-it]').forEach(function(e){e.textContent=e.getAttribute('data-'+l)});
document.querySelectorAll('.lang button').forEach(function(b){b.setAttribute('aria-pressed',b.dataset.l===l)});}
document.querySelectorAll('.lang button').forEach(function(b){b.addEventListener('click',function(){set(b.dataset.l)})});
var f=document.getElementById('req'),s=document.getElementById('status');
f.addEventListener('submit',function(e){e.preventDefault();
var a=f.arrivo.value,p=f.partenza.value;
if(a&&p&&p<=a){s.textContent=L==='it'?'La partenza deve essere dopo l\\u2019arrivo.':'Departure must be after arrival.';return;}
s.textContent='demo: nessun dato inviato';});
})();
"""

def t(it, en, tag="span"):
    return '<%s data-it="%s" data-en="%s">%s</%s>' % (tag, it.replace('"', '&quot;'), en.replace('"', '&quot;'), it, tag)

def build(s):
    img = ph(s['pbg'], s['pfg'])
    alt = "foto da inserire (con permesso del titolare)"
    name = s['name']
    acts = ""
    if s.get('tel'):
        acts += '<a class="btn" href="tel:%s">%s</a>' % (s['tel'], t("Chiama %s" % s['telshow'], "Call %s" % s['telshow']))
    if s.get('wa'):
        acts += '<a class="btn alt" href="https://wa.me/%s">%s</a>' % (s['wa'], t("Scrivi su WhatsApp", "Message on WhatsApp"))
    if s.get('email'):
        acts += '<a class="btn alt" href="mailto:%s">%s</a>' % (s['email'], t("Scrivi una email", "Send an email"))
    rooms = ""
    for i in range(1, 4):
        rooms += ('<article class="card"><img class="ph" src="%s" alt="%s" width="400" height="300" loading="lazy">'
                  '<h3>%s</h3><p class="note">%s</p></article>') % (
            img, alt, t("Camera %d [nome da inserire]" % i, "Room %d [name to be added]" % i),
            t("Descrizione, letti e servizi: da inserire a cura del titolare.", "Description, beds and amenities: to be added by the owner."))
    contact = "<p>%s</p>" % s['addr']
    if s.get('tel'):
        contact += '<p>%s <a href="tel:%s">%s</a></p>' % (t("Telefono:", "Phone:"), s['tel'], s['telshow'])
    if s.get('wa'):
        contact += '<p>WhatsApp: <a href="https://wa.me/%s">%s</a></p>' % (s['wa'], s['washow'])
    if s.get('email'):
        contact += '<p>Email: <a href="mailto:%s">%s</a></p>' % (s['email'], s['email'])
    zone = "".join("<li>%s</li>" % t(a, b) for a, b in s['zone'])
    html = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="noindex,nofollow">
<style>
:root{%(vars)s}
%(base)s
%(css)s
</style>
</head>
<body class="%(cls)s">
<a class="skip" href="#main">%(skip)s</a>
<header class="top">
<a class="brand" href="#main">%(name)s</a>
<div class="lang" role="group" aria-label="Lingua / Language"><button type="button" data-l="it" aria-pressed="true">IT</button> <button type="button" data-l="en" aria-pressed="false">EN</button></div>
</header>
<main id="main">
<section class="hero"><div class="wrap">
<h1 class="rv">%(h1)s</h1>
<p class="rv d1">%(lead)s</p>
<div class="actions rv d2"><a class="btn" href="#disponibilita">%(cta)s</a>%(acts)s</div>
<div class="rv d2 heroimg" style="margin-top:2rem"><img class="ph" src="%(img)s" alt="%(alt)s" width="400" height="300"></div>
</div></section>
<section id="camere"><div class="wrap">
<h2>%(hcam)s</h2>
<div class="cards">%(rooms)s</div>
</div></section>
<section id="disponibilita"><div class="wrap">
<h2>%(hreq)s</h2>
<p>%(preq)s</p>
<form class="req" id="req" novalidate>
<label>%(la)s<input type="date" name="arrivo" required></label>
<label>%(lp)s<input type="date" name="partenza" required></label>
<label>%(lo)s<input type="number" name="ospiti" min="1" max="20" value="2" required></label>
<button class="btn" type="submit">%(sub)s</button>
<p class="status" id="status" role="status" aria-live="polite"></p>
<p class="note">%(demo)s</p>
</form>
</div></section>
<section id="zona"><div class="wrap">
<h2>%(hzone)s</h2>
<ul class="zone">%(zone)s</ul>
</div></section>
<section id="recensioni"><div class="wrap">
<h2>%(hrev)s</h2>
<div class="reviews"><p>%(prev)s</p></div>
</div></section>
<section id="contatti"><div class="wrap">
<h2>%(hcon)s</h2>
%(contact)s
</div></section>
</main>
<footer><p>Bozza dimostrativa preparata per %(name)s &mdash; non pubblicata</p></footer>
<script>%(js)s</script>
</body>
</html>
""" % dict(
        title=s['title'], desc=s['desc'], vars=s['vars'], base=BASE_CSS, css=s['css'], cls=s['cls'],
        skip=t("Vai al contenuto", "Skip to content"), name=name,
        h1=t(*s['h1']), lead=t(*s['lead']),
        cta=t("Richiedi disponibilità", "Check availability"), acts=acts, img=img, alt=alt,
        hcam=t("Le camere", "Rooms"), rooms=rooms,
        hreq=t("Richiesta di disponibilità diretta", "Direct availability request"),
        preq=t("Indica date e numero di ospiti: è un modulo dimostrativo.", "Choose your dates and number of guests: this is a demo form."),
        la=t("Arrivo", "Arrival"), lp=t("Partenza", "Departure"), lo=t("Ospiti", "Guests"),
        sub=t("Invia richiesta", "Send request"),
        demo=t("Modulo dimostrativo: non invia nulla.", "Demo form: it sends nothing."),
        hzone=t("La zona", "The area"), zone=zone,
        hrev=t("Recensioni", "Reviews"),
        prev=t("Spazio da collegare alle recensioni reali degli ospiti (ad esempio dai portali di prenotazione). Nessuna recensione è inserita in questa bozza.",
               "Space to be linked to real guest reviews (for example from booking portals). No reviews are included in this draft."),
        hcon=t("Contatti", "Contact"), contact=contact, js=JS)
    with open(os.path.join(OUT, s['file']), 'w', encoding='utf-8') as f:
        f.write(html)

SITES = [
 dict(file='gisella-b-b.html', name="Gisella B&amp;B", cls='gis',
  title="Gisella B&B, Selargius - bozza demo", desc="Bozza dimostrativa del sito di Gisella B&B a Selargius (CA). Non pubblicata.",
  vars="--bg:#fbf4ec;--tx:#2b2118;--ac:#9a3b1f;--on:#fff;--fc:#1a4f8b;--card:#fff;--bd:#e7d6c3;--ib:#7a5c44;--r:14px;--ff:Georgia,'Times New Roman',serif;--fh:Georgia,serif",
  css=".hero{text-align:center}.hero .actions{justify-content:center}.hero .ph{max-width:34rem;margin:0 auto;border-radius:200px 200px 14px 14px}form.req{margin:0 auto}section h2{text-align:center}.zone{max-width:36rem;margin:0 auto}#contatti .wrap{text-align:center}",
  pbg="#e9cfb5", pfg="#9a3b1f",
  h1=("Una pausa tranquilla a Selargius", "A quiet stay in Selargius"),
  lead=("Gisella B&amp;B: richiedi direttamente le date che ti interessano.", "Gisella B&amp;B: ask directly for the dates you need."),
  addr="Via Canova 11, Selargius (CA)", tel="+393464003577", telshow="346 4003577", wa="393464003577", washow="346 4003577",
  zone=[("Selargius si trova nell'area di Cagliari, in Sardegna.", "Selargius is in the Cagliari area, in Sardinia."),
        ("Indicazioni su Cagliari e sul mare: da aggiungere a cura del titolare.", "Directions to Cagliari and the sea: to be added by the owner.")]),
 dict(file='anania-guesthouse.html', name="Anania guesthouse", cls='ana',
  title="Anania guesthouse, Cagliari - bozza demo", desc="Bozza dimostrativa del sito di Anania guesthouse a Cagliari. Non pubblicata.",
  vars="--bg:#12202e;--tx:#eef2f5;--ac:#f2b84b;--on:#12202e;--fc:#8fd0ff;--card:#1b2f42;--bd:#33506b;--ib:#9fb6c9;--r:4px;--ff:system-ui,Segoe UI,Arial,sans-serif;--fh:system-ui,Segoe UI,Arial,sans-serif",
  css="h1,h2{letter-spacing:.02em;text-transform:uppercase}.card{border-left:4px solid var(--ac)}@media(min-width:44rem){.hero .wrap{display:grid;grid-template-columns:1.1fr .9fr;gap:2rem;align-items:center}.hero .wrap>*:not(.heroimg){grid-column:1}.heroimg{grid-column:2;grid-row:1/5;margin-top:0!important}}",
  pbg="#27425b", pfg="#f2b84b",
  h1=("Nel centro di Cagliari", "In the centre of Cagliari"),
  lead=("Guesthouse in via Sant'Anania. Scrivici su WhatsApp o richiedi le date: prenotazione diretta chiara.", "A guesthouse in via Sant'Anania. Message us on WhatsApp or request your dates: clear direct booking."),
  addr="Via Sant'Anania 13, Cagliari", wa="393284786217", washow="+39 328 478 6217",
  zone=[("La guesthouse è nel centro di Cagliari, capoluogo della Sardegna.", "The guesthouse is in the centre of Cagliari, the capital of Sardinia."),
        ("Percorsi e luoghi da consigliare agli ospiti: da aggiungere a cura del titolare.", "Routes and places to suggest to guests: to be added by the owner.")]),
 dict(file='b-b-casa-spano.html', name="B&amp;B Casa Spano", cls='spa',
  title="B&B Casa Spano, Selargius - versione migliorata (demo)", desc="Bozza dimostrativa migliorata del sito di B&B Casa Spano a Selargius: richiesta di disponibilità e WhatsApp. Non pubblicata.",
  vars="--bg:#f3f8f6;--tx:#16302b;--ac:#0f6b5c;--on:#fff;--fc:#b4410a;--card:#fff;--bd:#cfe3dd;--ib:#4d7a70;--r:22px;--ff:system-ui,Segoe UI,Arial,sans-serif;--fh:system-ui,Segoe UI,Arial,sans-serif",
  css="body{background:linear-gradient(180deg,#e4f2ed 0,var(--bg) 22rem)}.hero .wrap{max-width:46rem}h1{font-weight:800}.card{box-shadow:0 4px 14px rgba(15,107,92,.1)}.btn{border-radius:999px}form.req{box-shadow:0 8px 24px rgba(15,107,92,.12)}",
  pbg="#cfe6df", pfg="#0f6b5c",
  h1=("Richiedi le tue date, in due tocchi", "Request your dates in two taps"),
  lead=("B&amp;B Casa Spano a Selargius: modulo di richiesta di disponibilità e contatto diretto, pensato per il telefono.", "B&amp;B Casa Spano in Selargius: an availability request form and direct contact, designed for phones."),
  addr="Via Trieste 131, 09047 Selargius", tel="+393792533728", telshow="+39 379 2533728", wa="393792533728", washow="+39 379 2533728", email="info@bandbcasaspano.it",
  zone=[("Selargius fa parte dell'area di Cagliari, in Sardegna.", "Selargius is part of the Cagliari area, in Sardinia."),
        ("Suggerimenti su spiagge, borghi e ristoranti: da aggiungere a cura del titolare.", "Tips on beaches, villages and restaurants: to be added by the owner.")]),
 dict(file='fattoria-giaccu.html', name="Fattoria Giaccu", cls='fat',
  title="Fattoria Giaccu, Assemini - bozza demo", desc="Bozza dimostrativa del sito di Fattoria Giaccu ad Assemini (CA). Non pubblicata.",
  vars="--bg:#f6f1e3;--tx:#2e2a17;--ac:#4f5f17;--on:#fff;--fc:#8a2d00;--card:#fffdf5;--bd:#d9cfa8;--ib:#6b6430;--r:8px;--ff:Georgia,'Times New Roman',serif;--fh:Georgia,serif",
  css="header.top{border-bottom:3px double var(--ac)}h1,h2{font-style:italic}.hero{background:repeating-linear-gradient(135deg,transparent 0 22px,rgba(79,95,23,.06) 22px 44px)}.card{border:2px solid var(--ac)}.ph{aspect-ratio:3/2}",
  pbg="#e3dcb4", pfg="#4f5f17",
  h1=("In campagna, vicino a Cagliari", "In the countryside, near Cagliari"),
  lead=("Fattoria Giaccu, ad Assemini: scrivici su WhatsApp o richiedi le date.", "Fattoria Giaccu, in Assemini: message us on WhatsApp or request your dates."),
  addr="Loc. Giaccu Meloni, Strada dei Canadesi, Assemini", wa="393484000668", washow="+39 348 4000668",
  zone=[("Assemini è un comune dell'area di Cagliari, in Sardegna.", "Assemini is a municipality in the Cagliari area, in Sardinia."),
        ("Attività, prodotti e dintorni della fattoria: da descrivere a cura del titolare.", "Farm activities, products and surroundings: to be described by the owner.")]),
]
for s in SITES:
    build(s)
