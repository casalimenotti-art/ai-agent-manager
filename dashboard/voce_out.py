"""Guardian parla: sintesi vocale italiana femminile nel browser (Web Speech API), frase per frase mentre la risposta arriva.

Nessuna installazione e nessun invio: si usano le voci del sistema (su Windows, ad esempio, «Microsoft Elsa» italiana è locale).
Alcune voci (es. «Google italiano» in Chrome, voci «Online» di Edge) mandano il testo a un servizio: il pannello Voce le segnala e
preferisce sempre una voce locale. La coda di riproduzione vive nella finestra principale: sopravvive agli aggiornamenti di Streamlit.
"""
from __future__ import annotations

import json
import re

_URL = re.compile(r"https?://\S+")
_LINK_MD = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_FENCE = re.compile(r"```.*?```", re.S)
_CONFINE = re.compile(r"[.!?…:;](?=\s)|\n")


def pulisci_per_voce(testo: str) -> str:
    """Toglie ciò che non va letto: codice, tabelle, URL, simboli markdown. Un blocco di codice non chiuso viene tagliato."""
    t = _FENCE.sub(" ", testo or "")
    if "```" in t:                      # fence aperta (risposta ancora in arrivo): ignora il resto
        t = t.split("```", 1)[0]
    righe = []
    for r in t.splitlines():
        s = r.strip()
        if not s or s.startswith("|") or re.fullmatch(r"[-=_*\s]{3,}", s):
            continue
        s = re.sub(r"^(#{1,6}\s*|>\s*|[-*+]\s+)", "", s)
        s = _LINK_MD.sub(r"\1", s)
        s = _URL.sub("il link", s)
        s = s.replace("`", "").replace("**", "").replace("__", "").replace("*", "").replace("_", " ").replace("#", "")
        s = " ".join(s.split())
        s = re.sub(r"(il link[ ,]*){2,}", "i link ", s).strip()
        if s:
            righe.append(s if s[-1] in ".!?…:;" else s + ".")
    return "\n".join(righe)


def spezza(testo: str, max_len: int = 220) -> list[str]:
    """Frasi per la sintesi: per punteggiatura; quelle troppo lunghe si dividono alle virgole o agli spazi."""
    frasi = []
    for blocco in re.split(r"(?<=[.!?…])\s+|\n+", testo.strip()):
        b = blocco.strip()
        while len(b) > max_len:
            taglio = max(b.rfind(",", 0, max_len), b.rfind(";", 0, max_len), b.rfind(" ", 0, max_len))
            taglio = taglio if taglio > 40 else max_len
            frasi.append(b[:taglio + 1].strip())
            b = b[taglio + 1:].strip()
        if b:
            frasi.append(b)
    return frasi


def prossimo_pezzo(pulito: str, parlato: str, finale: bool = False, min_len: int = 28) -> tuple[list[str], str]:
    """Dato il testo pulito finora e ciò che è già stato detto, restituisce (frasi nuove complete, nuovo «parlato»)."""
    resto = pulito[len(parlato):] if pulito.startswith(parlato) else pulito
    if not resto.strip():
        return [], parlato
    if finale:
        return spezza(resto), pulito
    ultimo = None
    for m in _CONFINE.finditer(resto):
        ultimo = m
    if ultimo is None or ultimo.end() < min_len:
        return [], parlato
    return spezza(resto[:ultimo.end()]), parlato + resto[:ultimo.end()]


_SCEGLI = r"""
function scegliVoce(S, prefs) {
  const it = S.getVoices().filter(v => /^it([-_]|$)/i.test(v.lang));
  if (!it.length) return null;
  if (prefs.nome) { const m = it.find(v => v.name === prefs.nome); if (m) return m; }
  const donna = /elsa|isabella|alice|federica|paola|francesca|lucia|chiara|elisa|google italiano|female|donna/i;
  const uomo = /diego|cosimo|luca|giorgio|riccardo|marco|male|uomo|paolo|lorenzo/i;
  const f = it.filter(v => donna.test(v.name) && !uomo.test(v.name));
  return f.find(v => v.localService) || f[0] || it.find(v => v.localService) || it[0];
}
"""


def js_parla(frasi: list[str]) -> str:
    """Pagina minuscola (height 0) che accoda le frasi nella sintesi della finestra principale."""
    dati = json.dumps(frasi, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return ("<script>(function(){try{const P=window.parent,S=P.speechSynthesis;if(!S)return;const frasi=" + dati + ";"
            "let prefs={};try{prefs=JSON.parse(P.localStorage.getItem('guardian_voce')||'{}')}catch(e){}" + _SCEGLI +
            "let fatto=false;function parla(){if(fatto)return;fatto=true;const v=scegliVoce(S,prefs);"
            "frasi.forEach(t=>{const u=new P.SpeechSynthesisUtterance(t);u.lang='it-IT';if(v)u.voice=v;"
            "u.rate=prefs.rate||1.05;u.pitch=prefs.pitch||1.0;S.speak(u)})}"
            "if(S.getVoices().length)parla();else{S.onvoiceschanged=function(){S.onvoiceschanged=null;parla()};setTimeout(parla,900)}"
            "}catch(e){}})();</script>")


def js_ferma() -> str:
    return "<script>try{window.parent.speechSynthesis.cancel()}catch(e){}</script>"


def html_impostazioni() -> str:
    """Pannello Voce: elenca le voci italiane del browser (locale/online), permette di sceglierne una, regolare e provarla."""
    return ("<div id='box' style='font:14px system-ui;color:#e8f1ff'>"
            "<div id='stato' style='color:#a3aecb;margin-bottom:8px'>Cerco le voci italiane…</div>"
            "<select id='voce' style='width:100%;padding:8px;background:#0d1020;color:#e8f1ff;border:1px solid #1c2340'></select>"
            "<div style='display:flex;gap:16px;margin:10px 0'><label style='flex:1'>Velocità <input id='rate' type='range' min='0.7' max='1.4' step='0.05' style='width:100%'></label>"
            "<label style='flex:1'>Tono <input id='pitch' type='range' min='0.7' max='1.4' step='0.05' style='width:100%'></label></div>"
            "<button id='prova' style='padding:8px 14px;background:transparent;color:#00f0ff;border:1px solid #00f0ff;cursor:pointer'>Prova la voce</button> "
            "<button id='stop' style='padding:8px 14px;background:transparent;color:#ff8a6b;border:1px solid #ff8a6b;cursor:pointer'>Stop</button>"
            "<div id='avviso' style='color:#fcee0a;margin-top:8px;font-size:12px'></div></div>"
            "<script>" + _SCEGLI + "(function(){const P=window.parent,S=P.speechSynthesis;const $=i=>document.getElementById(i);"
            "if(!S){$('stato').textContent='Questo browser non ha la sintesi vocale.';return}"
            "let prefs={};try{prefs=JSON.parse(P.localStorage.getItem('guardian_voce')||'{}')}catch(e){}"
            "$('rate').value=prefs.rate||1.05;$('pitch').value=prefs.pitch||1.0;"
            "function salva(){prefs={nome:$('voce').value,rate:+$('rate').value,pitch:+$('pitch').value};try{P.localStorage.setItem('guardian_voce',JSON.stringify(prefs))}catch(e){};avviso()}"
            "function avviso(){const o=$('voce').selectedOptions[0];$('avviso').textContent=o&&o.dataset.locale==='0'?"
            "'Questa voce è online: il testo che legge viene inviato al servizio del browser. Preferisci una voce «locale».':''}"
            "function elenca(){const it=S.getVoices().filter(v=>/^it([-_]|$)/i.test(v.lang));const sel=$('voce');sel.innerHTML='';"
            "if(!it.length){$('stato').textContent='Nessuna voce italiana trovata nel browser. Su Windows: Impostazioni > Ora e lingua > Voce > Aggiungi voci (Italiano).';return}"
            "it.forEach(v=>{const o=document.createElement('option');o.value=v.name;o.dataset.locale=v.localService?'1':'0';"
            "o.textContent=v.name+' — '+(v.localService?'locale':'online');sel.appendChild(o)});"
            "const d=scegliVoce(S,prefs);if(d)sel.value=d.name;"
            "$('stato').textContent=it.length+' voci italiane. Se non scegli, uso una voce femminile locale.';avviso()}"
            "S.getVoices().length?elenca():(S.onvoiceschanged=elenca);"
            "$('voce').onchange=salva;$('rate').onchange=salva;$('pitch').onchange=salva;"
            "$('prova').onclick=function(){salva();S.cancel();const u=new P.SpeechSynthesisUtterance('Ciao, sono Guardian. Ti sento bene e sono pronta ad aiutarti.');"
            "u.lang='it-IT';const v=S.getVoices().find(x=>x.name===prefs.nome);if(v)u.voice=v;u.rate=prefs.rate||1.05;u.pitch=prefs.pitch||1;S.speak(u)};"
            "$('stop').onclick=function(){S.cancel()};})();</script>")


def js_lavora(si: bool) -> str:
    """Segna nella finestra principale se Guardian sta lavorando: il microfono a mani libere tace finché non ha finito di rispondere."""
    return "<script>try{window.parent.__guardianLavora=" + ("Date.now()" if si else "0") + "}catch(e){}</script>"
