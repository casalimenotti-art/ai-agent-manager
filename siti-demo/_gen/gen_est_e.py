# -*- coding: utf-8 -*-
import os, html, urllib.parse
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALT = "foto da inserire (con permesso del titolare)"

def ph(c1, c2, label):
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 400 300'><rect width='400' height='300' fill='%s'/>"
           "<circle cx='200' cy='125' r='38' fill='%s' opacity='.55'/><rect x='120' y='185' width='160' height='14' rx='7' fill='%s' opacity='.55'/>"
           "<text x='200' y='260' font-family='sans-serif' font-size='18' text-anchor='middle' fill='%s'>%s</text></svg>") % (c1, c2, c2, c2, label)
    return "data:image/svg+xml," + urllib.parse.quote(svg)

DAYS = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]

SITES = [
 dict(file="beauty-center-valentino.html", name="Beauty Center Valentino", kind="est", city="Cagliari",
  addr="Via Palestrina 17 A, 09129 Cagliari", tel="070 400629", telh="+39070400629", wa=None,
  email="info@beautycentervalentino.it",
  hours=[("Lunedì","14:00 – 20:00"),("Martedì – Venerdì","9:00 – 20:00"),("Sabato","9:00 – 13:00")],
  hnote="Orari da scheda pubblica (directory), da confermare con il titolare.",
  tag="Centro estetico a Cagliari", lead="Prenota il tuo appuntamento in pochi passi, quando vuoi.",
  c=dict(bg="#fbf3f1", ink="#3b2327", mut="#6e4f54", acc="#8e3b4e", acc2="#f1d6da", card="#ffffff", line="#e6cfd2", ph1="#f1d6da", ph2="#8e3b4e"),
  font="Georgia,'Times New Roman',serif", sans="system-ui,-apple-system,'Segoe UI',Roboto,sans-serif", radius="999px 999px 18px 18px", theme="arch",
  improved=False),
 dict(file="clelsy-centro-estetico.html", name="Clelsy Centro Estetico", kind="est", city="Quartu Sant'Elena",
  addr="Via Catalani 18, Quartu Sant'Elena", tel="+39 329 849 8524", telh="+393298498524", wa="393298498524",
  email="info@centroesteticoclelsy.it",
  hours=None, hnote="Orari di apertura: da inserire.",
  tag="Centro estetico a Quartu Sant'Elena", lead="Versione migliorata: prenotazione online e orari ben visibili, per chi ha già un sito.",
  c=dict(bg="#f2f7f3", ink="#1f3328", mut="#4a6355", acc="#2f6b4c", acc2="#d5e8dc", card="#ffffff", line="#c9ddd0", ph1="#d5e8dc", ph2="#2f6b4c"),
  font="'Trebuchet MS',system-ui,sans-serif", sans="'Trebuchet MS',system-ui,sans-serif", radius="28px", theme="split", improved=True),
 dict(file="clinical-beauty-farm-srl.html", name="Clinical Beauty Farm srl", kind="est", city="Cagliari",
  addr="Viale Isonzo 12, 09122 Cagliari", tel="342 351 4707", telh="+393423514707", wa=None, email=None,
  hours=[("Lunedì – Venerdì","9:00 – 20:00"),("Sabato","9:00 – 13:00")],
  hnote="Orari da scheda pubblica (directory), da confermare con il titolare.",
  tag="Centro estetico a Cagliari", lead="Prenota online il tuo appuntamento: scegli servizio, giorno e fascia.",
  c=dict(bg="#f4f7fa", ink="#12263a", mut="#46596b", acc="#0b5c7a", acc2="#d9e9f1", card="#ffffff", line="#c5d5e0", ph1="#d9e9f1", ph2="#0b5c7a"),
  font="system-ui,-apple-system,'Segoe UI',Roboto,sans-serif", sans="system-ui,-apple-system,'Segoe UI',Roboto,sans-serif", radius="4px", theme="clinic", improved=False),
 dict(file="coccole-centro-estetico.html", name="Coccole Centro Estetico", kind="est", city="Cagliari",
  addr="Via Donizetti 64/B, 09128 Cagliari", tel="+39 329 355 9946", telh="+393293559946", wa=None,
  email="beautycoccole@gmail.com",
  hours=[("Lunedì","15:00 – 20:00"),("Martedì – Venerdì","10:00 – 20:00"),("Sabato","10:00 – 15:00")],
  hnote="Orari da scheda pubblica (directory), possibili aggiornamenti: da confermare con il titolare.",
  tag="Centro estetico a Cagliari", lead="Un momento tutto per te: scegli quando, al resto pensiamo dopo.",
  c=dict(bg="#fff4ea", ink="#3d2616", mut="#6b4a36", acc="#a8431f", acc2="#ffd9bf", card="#ffffff", line="#f0cfb5", ph1="#ffd9bf", ph2="#a8431f"),
  font="'Segoe UI',system-ui,sans-serif", sans="'Segoe UI',system-ui,sans-serif", radius="40% 60% 55% 45% / 50% 45% 55% 50%", theme="blob", improved=False),
 dict(file="chiarovista-di-mario-orru.html", name="ChiaroVista di Mario Orru'", kind="ott", city="Assemini",
  addr="Via Sardegna 18, 09032 Assemini", tel="347 357 3635", telh="+393473573635", wa=None, email=None,
  hours=None, hnote="Orari di apertura: da inserire.",
  tag="Ottica ad Assemini", lead="Versione migliorata: prenota il controllo della vista e consulta il catalogo montature.",
  c=dict(bg="#0f1b2d", ink="#eef3fa", mut="#b9c6d9", acc="#ffc247", acc2="#1b2d4a", card="#16253d", line="#2e4468", ph1="#1b2d4a", ph2="#ffc247"),
  font="'Gill Sans','Trebuchet MS',system-ui,sans-serif", sans="'Gill Sans','Trebuchet MS',system-ui,sans-serif", radius="12px", theme="optic", improved=True),
]

def e(s): return html.escape(s, quote=True)

def build(s):
    c = s["c"]; est = s["kind"] == "est"; dark = s["theme"] == "optic"
    btn_ink = "#0f1b2d" if dark else "#ffffff"
    title = "%s – %s | Bozza dimostrativa" % (s["name"], s["tag"])
    desc = "Bozza dimostrativa del sito di %s (%s): prenotazione %s dimostrativa, non pubblicata." % (s["name"], s["city"], "del controllo vista" if not est else "dell'appuntamento")
    if s["hours"]:
        rows = "".join("<tr><th scope='row'>%s</th><td>%s</td></tr>" % (e(a), e(b)) for a, b in s["hours"])
    else:
        rows = "<tr><th scope='row'>Orari</th><td>da inserire</td></tr>"
    cta = "<a class='btn' href='tel:%s'>Chiama %s</a>" % (s["telh"], e(s["tel"]))
    if s["wa"]:
        cta += "<a class='btn ghost' href='https://wa.me/%s'>Scrivi su WhatsApp</a>" % s["wa"]
    contacts = "<li><span>Indirizzo</span> %s</li><li><span>Telefono</span> <a href='tel:%s'>%s</a></li>" % (e(s["addr"]), s["telh"], e(s["tel"]))
    if s["wa"]: contacts += "<li><span>WhatsApp</span> <a href='https://wa.me/%s'>%s</a></li>" % (s["wa"], e(s["tel"]))
    if s["email"]: contacts += "<li><span>Email</span> <a href='mailto:%s'>%s</a></li>" % (s["email"], e(s["email"]))
    days = "".join("<option>%s</option>" % d for d in DAYS)
    if est:
        opts = "".join("<option>Servizio da inserire %d</option>" % i for i in (1, 2, 3))
        svc_label = "Servizio"; form_h = "Prenota il tuo appuntamento"
        main_sec = "<section id='servizi' aria-labelledby='h-serv'><div class='wrap'><h2 id='h-serv'>Servizi</h2><p class='sub'>Elenco dei trattamenti da inserire insieme al titolare.</p><div class='grid3'>" + "".join(
            "<article class='card rv' style='--d:%dms'><div class='ico' aria-hidden='true'>%d</div><h3>Servizio da inserire</h3><p>Descrizione e durata da inserire. Prezzo: da inserire.</p></article>" % (i * 90, i) for i in (1, 2, 3)) + "</div></div></section>"
        gal = "<section id='galleria' aria-labelledby='h-gal'><div class='wrap'><h2 id='h-gal'>Prima e dopo</h2><p class='sub'>Spazio per le foto dei risultati, da pubblicare solo con il permesso del titolare e dei clienti.</p><div class='grid2'>" + "".join(
            "<figure class='rv' style='--d:%dms'><div class='pair'><div><img src='%s' alt='%s' width='400' height='300' loading='lazy'><figcaption>Prima</figcaption></div><div><img src='%s' alt='%s' width='400' height='300' loading='lazy'><figcaption>Dopo</figcaption></div></div></figure>" % (i * 100, ph(c["ph1"], c["ph2"], "Prima"), ALT, ph(c["ph1"], c["ph2"], "Dopo"), ALT) for i in (1, 2)) + "</div></div></section>"
        extra = ""
        if s["improved"]:
            extra = "<aside class='note' aria-label='Novità'><strong>Cosa cambia rispetto al sito attuale</strong><ul><li>Prenotazione online dell'appuntamento</li><li>Orari in evidenza (da inserire)</li><li>Chiamata e WhatsApp a portata di pollice</li></ul></aside>"
    else:
        opts = "<option>Controllo della vista</option>"
        svc_label = "Tipo di visita"; form_h = "Prenota il controllo della vista"
        main_sec = "<section id='catalogo' aria-labelledby='h-cat'><div class='wrap'><h2 id='h-cat'>Catalogo montature</h2><p class='sub'>Modelli, marchi e prezzi da inserire con il titolare.</p><div class='grid3'>" + "".join(
            "<article class='card rv' style='--d:%dms'><img src='%s' alt='%s' width='400' height='300' loading='lazy'><h3>Montatura da inserire</h3><p>Marchio, materiale e prezzo: da inserire.</p></article>" % (i * 90, ph(c["ph1"], c["ph2"], "Montatura"), ALT) for i in (1, 2, 3)) + "</div></div></section>"
        gal = ""
        extra = "<aside class='note' aria-label='Novità'><strong>Cosa cambia rispetto al sito attuale</strong><ul><li>Prenotazione del controllo della vista</li><li>Orari in evidenza (da inserire)</li><li>Chiamata sempre visibile</li><li>Catalogo montature</li></ul></aside>"
    th = s["theme"]
    hero_img = "<img class='heroimg rv' src='%s' alt='%s' width='400' height='300'>" % (ph(c["ph1"], c["ph2"], "Foto"), ALT)
    css = """
:root{--bg:%(bg)s;--ink:%(ink)s;--mut:%(mut)s;--acc:%(acc)s;--acc2:%(acc2)s;--card:%(card)s;--line:%(line)s;--font:%(font)s;--sans:%(sans)s}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:1rem/1.6 var(--sans);-webkit-text-size-adjust:100%%}
h1,h2,h3{font-family:var(--font);line-height:1.15;margin:0 0 .5em}
h1{font-size:clamp(2rem,8vw,3.4rem)}h2{font-size:clamp(1.5rem,5vw,2.2rem)}h3{font-size:1.15rem}
a{color:var(--acc)}a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid var(--acc);outline-offset:3px}
.skip{position:absolute;left:-999px;top:0;background:#000;color:#fff;padding:.6rem 1rem;z-index:9}.skip:focus{left:8px;top:8px}
.wrap{width:min(1080px,100%% - 32px);margin:0 auto}
header.top{padding:14px 0;border-bottom:1px solid var(--line)}header.top .wrap{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.brand{font-family:var(--font);font-weight:700;font-size:1.1rem;color:var(--ink);text-decoration:none}
nav a{margin-left:14px;color:var(--ink);text-decoration:none;font-weight:600;font-size:.95rem}nav a:hover{text-decoration:underline}
.hero{padding:48px 0 40px}.hero .wrap{display:grid;gap:28px;align-items:center}
.eyebrow{display:inline-block;font-weight:700;font-size:.85rem;letter-spacing:.08em;text-transform:uppercase;color:var(--acc);margin-bottom:.6rem}
.hero p.lead{font-size:1.15rem;color:var(--mut);max-width:34em}
.ctas{display:flex;flex-wrap:wrap;gap:12px;margin-top:20px}
.btn{display:inline-block;background:var(--acc);color:%(bi)s;padding:.8rem 1.4rem;border-radius:999px;font-weight:700;text-decoration:none;border:2px solid var(--acc);min-height:44px;transition:transform .25s ease,box-shadow .25s ease}
.btn:hover{transform:translateY(-2px);box-shadow:0 8px 18px rgba(0,0,0,.18)}.btn.ghost{background:transparent;color:var(--ink);border-color:var(--ink)}
.heroimg{width:100%%;height:auto;display:block;background:var(--acc2)}
section{padding:40px 0}.sub{color:var(--mut);margin-top:-.2em}
.grid3{display:grid;gap:16px}.grid2{display:grid;gap:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;transition:transform .3s ease,box-shadow .3s ease}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 26px rgba(0,0,0,.1)}.card img{width:100%%;height:auto;border-radius:10px;margin-bottom:10px}
.ico{width:40px;height:40px;border-radius:50%%;background:var(--acc2);color:var(--acc);display:grid;place-items:center;font-weight:800;margin-bottom:10px}
figure{margin:0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pair img{width:100%%;height:auto;border-radius:12px;display:block}
figcaption{text-align:center;font-weight:700;font-size:.9rem;color:var(--mut);margin-top:6px}
.note{background:var(--acc2);color:var(--ink);border-radius:14px;padding:16px 20px;margin-top:20px;max-width:34em}.note ul{margin:.4em 0 0;padding-left:1.2em}
form{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px;display:grid;gap:14px;max-width:560px}
label{font-weight:700;display:block;margin-bottom:4px}
input,select{width:100%%;font:inherit;padding:.7rem .8rem;border:2px solid var(--mut);border-radius:10px;background:#fff;color:#1b1b1b;min-height:44px}
button.btn{cursor:pointer;font:inherit;font-weight:700;color:%(bi)s}
#esito{margin:0;font-weight:700;min-height:1.5em}
table{border-collapse:collapse;width:100%%;max-width:520px}th,td{text-align:left;padding:.55rem .4rem;border-bottom:1px solid var(--line)}caption{text-align:left;color:var(--mut);padding-bottom:.4rem}
.info{display:grid;gap:24px}ul.contacts{list-style:none;padding:0;margin:0}ul.contacts li{padding:.35rem 0}ul.contacts span{display:inline-block;min-width:6.2em;font-weight:700;color:var(--mut)}
footer{padding:28px 0 90px;border-top:1px solid var(--line);color:var(--mut);font-size:.92rem}
.mobilebar{position:fixed;left:0;right:0;bottom:0;display:flex;gap:8px;padding:8px 12px;background:var(--bg);border-top:1px solid var(--line);z-index:5}.mobilebar .btn{flex:1;text-align:center;padding:.6rem}
.rv{animation:up .7s cubic-bezier(.2,.7,.2,1) both;animation-delay:var(--d,0ms)}
@keyframes up{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}
@media(min-width:760px){.grid3{grid-template-columns:repeat(3,1fr)}.grid2{grid-template-columns:repeat(2,1fr)}.info{grid-template-columns:1fr 1fr}.hero .wrap{grid-template-columns:1.1fr .9fr}.mobilebar{display:none}footer{padding-bottom:28px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{animation:none!important;transition:none!important}}
""" % dict(c, font=s["font"], sans=s["sans"], bi=btn_ink)
    if th == "arch":
        css += ".heroimg{border-radius:999px 999px 18px 18px;max-width:340px;margin:auto}.hero{text-align:center}.hero .wrap{grid-template-columns:1fr!important}.hero p.lead,.note{margin-left:auto;margin-right:auto}.note{text-align:left}.ctas{justify-content:center}h2,.sub{text-align:center}.card{text-align:center}.ico{margin-inline:auto}.pair img{border-radius:999px 999px 10px 10px}"
    elif th == "split":
        css += "body{background:linear-gradient(180deg,#e4f0e8 0,var(--bg) 380px)}.hero .wrap{background:var(--card);border:1px solid var(--line);border-radius:28px;padding:28px}.heroimg{border-radius:22px}h1{letter-spacing:-.02em}.card{border-radius:24px}.eyebrow{background:var(--acc2);padding:.3rem .8rem;border-radius:99px}"
    elif th == "clinic":
        css += ".btn,.card,form,.note,input,select,.pair img,.heroimg{border-radius:4px}.hero{background:var(--ink);color:#fff}.hero .eyebrow,.hero p.lead{color:#cfe3ee}.hero .btn{background:#fff;color:#12263a;border-color:#fff}.hero .btn.ghost{background:transparent;color:#fff;border-color:#fff}.card{border-left:6px solid var(--acc)}h2{border-bottom:3px solid var(--acc);display:inline-block;padding-bottom:.15em}.ico{border-radius:4px}"
    elif th == "blob":
        css += ".heroimg{border-radius:%s;animation:float 7s ease-in-out infinite}@keyframes float{50%%{transform:translateY(-8px)}}.card{border-radius:30px 30px 30px 8px}.hero{background:radial-gradient(circle at 85%% 10%%,var(--acc2) 0,transparent 55%%)}h1{color:var(--acc)}form{border-radius:30px}.btn{border-radius:30px 30px 30px 8px}" % s["radius"]
    else:
        css += ".hero{background:linear-gradient(135deg,#16253d,#0f1b2d)}.heroimg{border-radius:12px;border:2px solid var(--acc)}.card{border-radius:10px}h1,h2{letter-spacing:.01em}h2::before{content:'';display:inline-block;width:.8em;height:.8em;border:3px solid var(--acc);border-radius:50%;margin-right:.4em;vertical-align:-.05em}input,select{border-color:#8aa0c0}"
    if th == "clinic":
        pass
    first = ("servizi", "Servizi") if est else ("catalogo", "Catalogo")
    nav = "<a href='#prenota'>Prenota</a><a href='#%s'>%s</a><a href='#contatti'>Contatti</a>" % (first[0], first[1])
    wa_btn = "<a class='btn ghost' href='https://wa.me/%s'>WhatsApp</a>" % s["wa"] if s["wa"] else ""
    mobile = "<div class='mobilebar'><a class='btn' href='tel:%s'>Chiama</a>%s<a class='btn ghost' href='#prenota'>Prenota</a></div>" % (s["telh"], wa_btn)
    page = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="noindex,nofollow">
<style>%(css)s</style>
</head>
<body>
<a class="skip" href="#main">Vai al contenuto</a>
<header class="top"><div class="wrap"><a class="brand" href="#top">%(name)s</a><nav aria-label="Principale">%(nav)s</nav></div></header>
<main id="main">
<section class="hero" id="top"><div class="wrap"><div class="rv"><span class="eyebrow">%(tag)s</span><h1>%(name)s</h1><p class="lead">%(lead)s</p><div class="ctas"><a class="btn" href="#prenota">Prenota ora</a>%(cta)s</div>%(extra)s</div>%(img)s</div></section>
%(main)s
%(gal)s
<section id="prenota" aria-labelledby="h-pre"><div class="wrap"><h2 id="h-pre">%(formh)s</h2><p class="sub">Modulo dimostrativo: non invia nulla.</p>
<form id="f" novalidate>
<div><label for="nome">Nome e cognome</label><input id="nome" name="nome" autocomplete="name" required></div>
<div><label for="svc">%(svcl)s</label><select id="svc" name="svc" required>%(opts)s</select></div>
<div><label for="giorno">Giorno preferito</label><select id="giorno" name="giorno" required>%(days)s</select></div>
<div><label for="fascia">Fascia oraria</label><select id="fascia" name="fascia" required><option>Mattina</option><option>Pomeriggio</option></select></div>
<button class="btn" type="submit">Richiedi appuntamento</button>
<p id="esito" role="status" aria-live="polite"></p>
</form></div></section>
<section id="contatti" aria-labelledby="h-con"><div class="wrap info"><div><h2 id="h-con">Contatti</h2><ul class="contacts">%(contacts)s</ul></div><div><h2>Orari</h2><table><caption>%(hnote)s</caption><tbody>%(rows)s</tbody></table></div></div></section>
</main>
<footer><div class="wrap"><p>Bozza dimostrativa preparata per %(name)s — non pubblicata</p></div></footer>
%(mobile)s
<script>
document.getElementById('f').addEventListener('submit',function(ev){ev.preventDefault();var o=document.getElementById('esito');if(!this.checkValidity()){this.reportValidity();return;}o.textContent='demo: nessun dato inviato';});
</script>
</body>
</html>
""" % dict(title=e(title), desc=e(desc), css=css, name=e(s["name"]), nav=nav, tag=e(s["tag"]), lead=e(s["lead"]), cta=cta, extra=extra,
           img=hero_img, main=main_sec, gal=gal, formh=form_h, svcl=svc_label, opts=opts, days=days, contacts=contacts, hnote=e(s["hnote"]), rows=rows, mobile=mobile)
    return page

for s in SITES:
    with open(os.path.join(OUT, s["file"]), "w", encoding="utf-8", newline="\n") as f:
        f.write(build(s))
    print("ok", s["file"])
