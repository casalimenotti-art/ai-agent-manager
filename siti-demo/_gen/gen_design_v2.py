import re,io,os
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
# slug: (bg, tx, btn, btnt, hero_tall, [(label,href,primary,en)])
S={
'ristorante-terra-e-mari':('#f4efe4','#14303b','#0a5c73','#fff',1,[('Chiama','tel:+393472501369',0,None),('Prenota un tavolo','#prenota',1,None)]),
'libarium-nostrum':('#1a1316','#f4eae4','#e6b86a','#1a1316',1,[('Chiama','tel:+393465220212',0,None),('Prenota un tavolo','#prenota',1,None)]),
'antica-trattoria-dar-mammozzaro':('#fbf4e8','#2b1d15','#8a3a1c','#fff',1,[('Chiama','tel:+393669552843',0,None),('Prenota un tavolo','#prenota',1,None)]),
'il-cagliarese-b-b':('#0e2638','#f4eee3','#e8c98e','#14212b',0,[('Contatti','#contatti',0,'Contacts'),('Richiedi disponibilità','#disponibilita',1,'Request availability')]),
'bellini-b-b':('#fbf6ee','#2a241f','#9a3b20','#fff',0,[('WhatsApp','https://wa.me/393471884960',0,'WhatsApp'),('Richiedi disponibilità','#disponibilita',1,'Request availability')]),
'ottica-borriello':('#f6f1e7','#14213d','#14213d','#f6f1e7',1,[('Chiama','tel:+390703056659',0,None),('Prenota il controllo','#prenota',1,None)]),
'bernardi-foto-ottica':('#fffaf5','#23343b','#b3412e','#fff',1,[('Chiama','tel:+39070663200',0,None),('Prenota il controllo','#prenota',1,None)]),
'ottica-ungari':('#0f1a14','#eef5ee','#9be564','#0f1a14',1,[('Chiama','tel:+393336912910',0,None),('Prenota il controllo','#prenota',1,None)]),
'comfort-beauty-estetica-maxia':('#fdf6f3','#35242a','#8c3a58','#fff',1,[('Chiama','tel:0702040267',0,None),('Prenota online','#prenota-sez',1,None)]),
'black-and-white-parrucchieri':('#ffffff','#0a0a0a','#0a0a0a','#fff',1,[('Chiama','tel:3429537817',0,None),('Prenota online','#prenota-sez',1,None)]),
}
CSS='''
/*dz2*/:root{--dz-bg:%s;--dz-tx:%s;--dz-b:%s;--dz-bt:%s}
html{scroll-padding-top:4.5rem}body{-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.skip{z-index:99!important}
header.top,.top{position:sticky;top:0;z-index:20}
main h1{text-wrap:balance;overflow-wrap:anywhere}main h2{text-wrap:balance}
main section h2::after{content:"";display:block;width:2.75rem;height:4px;background:var(--dz-b);margin-top:.55rem;border-radius:2px;transition:width .5s cubic-bezier(.2,.7,.2,1)}
main section:hover h2::after{width:4.5rem}
main section[id]{scroll-margin-top:4.5rem}
.btn{transition:transform .25s cubic-bezier(.2,.7,.2,1),box-shadow .25s ease,background-color .25s ease}.btn:active{transform:scale(.97)}
.hero .btn{min-height:52px;font-size:1.05rem;padding-inline:1.5rem}
li,dd,td{font-variant-numeric:tabular-nums}
.card,.menu-sec,.room,article{transition:transform .3s cubic-bezier(.2,.7,.2,1),box-shadow .3s ease}
.js .dz-r{opacity:0;transform:translateY(18px);transition:opacity .7s cubic-bezier(.2,.7,.2,1),transform .7s cubic-bezier(.2,.7,.2,1)}
.js .dz-r.dz-in{opacity:1;transform:none}
.dz-bar{display:none}
@media(max-width:44.99rem){
body{padding-bottom:calc(5rem + env(safe-area-inset-bottom))}
.dz-bar{display:flex;gap:.6rem;position:fixed;left:0;right:0;bottom:0;z-index:30;padding:.6rem .8rem calc(.6rem + env(safe-area-inset-bottom));background:var(--dz-bg);border-top:3px solid var(--dz-b);box-shadow:0 -8px 24px rgba(0,0,0,.18)}
.dz-bar a{flex:1 1 0;display:flex;align-items:center;justify-content:center;min-height:48px;padding:.4rem .6rem;border-radius:12px;border:2px solid var(--dz-tx);color:var(--dz-tx);background:transparent;font:700 1rem/1.15 system-ui,-apple-system,'Segoe UI',sans-serif;text-align:center;text-decoration:none;transition:transform .2s ease}
.dz-bar a.p{flex:1.5 1 0;background:var(--dz-b);border-color:var(--dz-b);color:var(--dz-bt)}
.dz-bar a:active{transform:scale(.96)}
.dz-bar a:focus-visible{outline:3px solid var(--dz-tx);outline-offset:2px}
}
@media(min-width:45rem){.hero .btn{min-height:54px}}
@media(prefers-reduced-motion:reduce){.js .dz-r{opacity:1;transform:none;transition:none}.btn,.dz-bar a{transition:none!important}}
'''
HERO='''.hero{min-height:min(82svh,44rem);display:flex;align-items:center}.hero>*{flex:1 1 auto}.hero h1{font-size:clamp(2.2rem,9vw,4.4rem);line-height:1.04}.hero p.lead,.hero .lead{font-size:clamp(1.1rem,3.4vw,1.3rem)}
.hero{padding-block:clamp(2.5rem,8vw,5rem)}
'''
JS='''<script>(function(){try{var d=document;if(!('IntersectionObserver' in window)||matchMedia('(prefers-reduced-motion:reduce)').matches)return;d.documentElement.classList.add('js');var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('dz-in');io.unobserve(e.target)}})},{rootMargin:'0px 0px -8%'});d.querySelectorAll('main section:not(.hero)').forEach(function(s){var c=s.children.length==1&&s.firstElementChild.tagName=='DIV'?s.firstElementChild:s;Array.prototype.forEach.call(c.children,function(k,i){if(k.tagName=='SCRIPT')return;k.classList.add('dz-r');k.style.transitionDelay=Math.min(i,4)*60+'ms';io.observe(k)})})}catch(x){}})();</script>'''
for slug,(bg,tx,b,bt,tall,items) in S.items():
    p=os.path.join(D,slug+'.html')
    h=io.open(p,encoding='utf-8').read()
    if '/*dz2*/' in h: print('skip',slug);continue
    css=CSS%(bg,tx,b,bt)+(HERO if tall else '')
    assert h.count('</style>')==1
    h=h.replace('</style>',css+'</style>',1)
    bar='<nav class="dz-bar" aria-label="Azioni rapide">'
    for lab,href,pr,en in items:
        bar+='<a%s href="%s"%s>%s</a>'%(' class="p"' if pr else '',href,' data-en="%s"'%en if en else '',lab)
    bar+='</nav>\n'
    assert h.count('</body>')==1
    h=h.replace('</body>',bar+JS+'\n</body>',1)
    io.open(p,'w',encoding='utf-8',newline='').write(h)
    print('ok',slug)
