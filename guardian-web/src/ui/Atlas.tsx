// Sfondo "Atlas": il cervello di Guardian come costellazione (nucleo > stanze > agenti > task). Canvas 2D.
// Strato fermo disegnato una volta (su canvas fuori schermo) + strato vivo a max 30 fps: impulsi sulle linee degli agenti attivi,
// respiro del nucleo, anelli lampeggianti per i bloccati, puntino rosa per "serve OK". Pausa con scheda nascosta,
// solo immagine ferma con prefers-reduced-motion. Niente blur né filter: cerchi e linee con globalAlpha.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { angoloAuto, COLORI_ATLAS, conProfondita, costruisciGrafo, hash01, polvere, proietta, type Grafo3, devoDisegnare, DURATA_ZOOM_MS, disponi, faseImpulso, FILTRO_TUTTI, filtraGrafo, interpolaVista, lampeggio, nodoInPunto, possoAnimare,
  puntoSulPercorso, respiro, riepilogoAtlas, schedaNodo, stileStato, VISTA_COMPLETA, vistaStanza, zonaLibera, type FiltroAtlas, type Grafo, type Nodo, type Pt, type Rett, type Scheda, type Vista } from '../logic/atlas';
import { useG } from '../state';
import { statoNucleo } from '../logic/guardian';
import { ThreeBrain } from './ThreeBrain';

const FONDO = '#000000';
const TELEFONO = 600;

/** Etichetta in maiuscolo spaziato, centrata (spaziatura a mano: letterSpacing non c'è in tutti i browser). */
function etichetta(c: CanvasRenderingContext2D, t: string, x: number, y: number, spazio: number) {
  const lettere = [...t.toUpperCase()]; const larg = lettere.map((l) => c.measureText(l).width);
  let px = x - (larg.reduce((a, b) => a + b, 0) + spazio * (lettere.length - 1)) / 2;
  c.textAlign = 'left';
  lettere.forEach((l, i) => { c.fillText(l, px, y); px += larg[i] + spazio; });
}

// sprite di luce precalcolati (uno per colore): niente shadowBlur né filter a ogni fotogramma
const SPRITE = new Map<string, HTMLCanvasElement>();
function sprite(colore: string): HTMLCanvasElement {
  let sp = SPRITE.get(colore); if (sp) return sp;
  sp = document.createElement('canvas'); sp.width = sp.height = 64; const c = sp.getContext('2d');
  if (c) { const g = c.createRadialGradient(32, 32, 0, 32, 32, 32); g.addColorStop(0, colore); g.addColorStop(0.18, colore + 'aa'); g.addColorStop(0.45, colore + '33'); g.addColorStop(1, colore + '00'); c.fillStyle = g; c.fillRect(0, 0, 64, 64); }
  SPRITE.set(colore, sp); return sp;
}
function punto(c: CanvasRenderingContext2D, x: number, y: number, r: number, colore: string, alpha: number) {
  const al = r * 4.2; c.globalAlpha = alpha * 0.55; c.drawImage(sprite(colore), x - al, y - al, al * 2, al * 2); // alone
  c.globalAlpha = alpha; c.fillStyle = colore; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill();
}

/** Inclinazione di base della camera (radianti): si guarda il cervello un po' dall'alto. */
export const INCLINAZIONE = 0.22;
/** Da coordinate normalizzate 3D a pixel, dentro la zona libera, con rotazione (ay, ax), prospettiva e zoom della vista. */
export function geometria(zona: Rett, v: Vista = VISTA_COMPLETA, ay = 0, ax = INCLINAZIONE) {
  const pad = 34; const cx = zona.x + zona.w / 2; const cy = zona.y + zona.h / 2;
  const sx = Math.max(20, zona.w / 2 - pad) * 0.86; const sy = Math.max(20, zona.h / 2 - pad) * 0.86;
  const k = Math.max(0.55, Math.min(1, Math.min(zona.w, zona.h) / 600)); // scala di nucleo e caratteri
  const Q = (n: { x: number; y: number; z?: number }) => { const q = proietta({ x: n.x - v.fx, y: n.y - v.fy, z: n.z ?? 0 }, ay, ax); return { ...q, px: cx + q.x * sx * v.z, py: cy + q.y * sy * v.z }; };
  const P = (n: { x: number; y: number; z?: number }) => { const q = Q(n); return [q.px, q.py] as const; };
  return { cx, cy, sx, sy, k, P, Q, ay, ax, v };
}
type Geo = ReturnType<typeof geometria>;
type Polvere = ReturnType<typeof polvere>;
const luce = (p: number) => 0.3 + 0.7 * p; // i nodi dietro sono più tenui

export function disegna(c: CanvasRenderingContext2D, g: Grafo3, w: number, h: number, vuoto: boolean, geo: Geo, dust: Polvere | null) {
  const { k, Q, cx, cy, sx, sy, v } = geo; const piccolo = k < 0.8;
  c.globalAlpha = 1; c.fillStyle = FONDO; c.fillRect(0, 0, w, h);
  // polvere neurale decorativa: linee in due fasce (dietro, davanti) e puntini come quadratini
  if (dust) {
    const pr = dust.punti.map((q) => { const r = proietta(q, geo.ay, geo.ax); return [cx + r.x * sx * 1.12 * v.z, cy + r.y * sy * 1.12 * v.z, r.p] as const; });
    c.lineWidth = 0.6;
    for (const [dietro, al] of [[true, 0.05], [false, 0.11]] as const) {
      c.strokeStyle = '#8fa6ff'; c.globalAlpha = al; c.beginPath();
      for (const [i, j] of dust.linee) { const a = pr[i]; const b = pr[j]; if ((a[2] + b[2] < 1) !== dietro) continue; c.moveTo(a[0], a[1]); c.lineTo(b[0], b[1]); }
      c.stroke();
    }
    c.fillStyle = '#cdd6ff';
    for (const [x, y, p] of pr) { c.globalAlpha = 0.18 + 0.6 * p * p; const r = 0.7 + 1.2 * p; c.fillRect(x - r / 2, y - r / 2, r, r); }
  }

  const per = new Map(g.nodi.map((n) => [n.id, n]));
  const pos = new Map(g.nodi.map((n) => [n.id, Q(n)]));
  const colStanza = (id: string | null) => (id ? per.get(`s:${id}`)?.colore : undefined) ?? COLORI_ATLAS.nucleo;

  // nervi: nucleo > stanze > agenti > task, più visibili davanti
  c.lineWidth = 1;
  for (const l of g.link) {
    const a = per.get(l.da); const b = per.get(l.a); const qa = pos.get(l.da); const qb = pos.get(l.a); if (!a || !b || !qa || !qb) continue;
    c.strokeStyle = l.stato === 'fermo' ? (a.tipo === 'nucleo' ? colStanza(l.stanza) : COLORI_ATLAS.fermo) : stileStato(l.stato, colStanza(l.stanza)).colore;
    const base = a.escluso || b.escluso ? 0.03 : l.stato === 'fermo' ? (a.tipo === 'nucleo' ? 0.16 : 0.09) : 0.26;
    c.globalAlpha = base * luce((qa.p + qb.p) / 2);
    c.beginPath(); c.moveTo(qa.px, qa.py); c.lineTo(qb.px, qb.py); c.stroke();
  }

  // nodi ordinati per profondità: prima quelli dietro
  const ordine = [...g.nodi].sort((x, y) => (pos.get(x.id)!.p - pos.get(y.id)!.p));
  for (const n of ordine) {
    const q = pos.get(n.id)!; const x = q.px; const y = q.py; const L = luce(q.p); const r = n.raggio * q.s;
    if (n.tipo === 'nucleo') {
      // anelli di puntini su tre piani diversi, come un atomo
      for (const [rag, num, al, rd, inc] of [[0.2, 64, 0.22, 1.1, 0.0], [0.15, 48, 0.32, 1.3, 1.1], [0.11, 36, 0.45, 1.5, -1.0]] as const) {
        c.fillStyle = COLORI_ATLAS.nucleo; const ca = Math.cos(inc); const sa = Math.sin(inc);
        for (let i = 0; i < num; i++) {
          const t = (i / num) * Math.PI * 2;
          const qq = Q({ x: n.x + Math.cos(t) * rag, y: n.y + Math.sin(t) * rag * ca, z: n.z + Math.sin(t) * rag * sa });
          c.globalAlpha = al * (0.35 + qq.p); c.beginPath(); c.arc(qq.px, qq.py, rd * qq.s, 0, Math.PI * 2); c.fill();
        }
      }
      punto(c, x, y, 15 * k * q.s, COLORI_ATLAS.nucleo, 0.7);
      c.globalAlpha = 1; c.fillStyle = '#ffffff'; c.beginPath(); c.arc(x, y, 6 * k * q.s, 0, Math.PI * 2); c.fill();
      c.globalAlpha = 0.85; c.fillStyle = '#dbe8ff'; c.font = `600 ${piccolo ? 11 : 13}px system-ui, sans-serif`;
      etichetta(c, 'Guardian', x, y + 60 * k * q.s, piccolo ? 2 : 3);
      if (vuoto) { c.globalAlpha = 0.7; c.fillStyle = '#cfe6fb'; c.font = `500 ${piccolo ? 11 : 12}px system-ui, sans-serif`; etichetta(c, 'Nessun agente collegato', x, y + 82 * k, 2); }
      continue;
    }
    if (n.tipo === 'task' || n.tipo === 'evento') { punto(c, x, y, Math.max(0.8, r), n.colore, n.alpha * L); continue; }
    if (n.escluso) { punto(c, x, y, r, n.colore, 0.08); continue; }
    if (n.tipo === 'agente') {
      const stile = stileStato(n.stato, n.colore);
      if (stile.fiore) { // fiore di puntini attorno a chi lavora
        c.fillStyle = stile.colore; c.globalAlpha = 0.7 * L;
        for (let i = 0; i < 10; i++) { const t = (i / 10) * Math.PI * 2; c.beginPath(); c.arc(x + Math.cos(t) * r * 2.4, y + Math.sin(t) * r * 2.4, 1.3 * q.s, 0, Math.PI * 2); c.fill(); }
      }
      if (stile.anello) { c.strokeStyle = stile.colore; c.globalAlpha = 0.7 * L; c.lineWidth = 1.2; c.beginPath(); c.arc(x, y, r * 2.2, 0, Math.PI * 2); c.stroke(); }
      punto(c, x, y, r, n.colore, n.alpha * L);
      if (q.p > 0.35 || n.stato === 'attivo') { // etichette solo davanti, per non affollare
        c.globalAlpha = (n.alpha < 0.6 ? 0.5 : 0.85) * L; c.fillStyle = '#d6deea'; c.font = `${n.stato === 'attivo' ? 600 : 400} 11px system-ui, sans-serif`; c.textAlign = 'center';
        c.fillText(n.etichetta, x, y + r * 2.4 + 13);
        if (n.attivita) { c.globalAlpha = 0.7 * L; c.fillStyle = stile.colore; c.font = '10px system-ui, sans-serif'; c.fillText(n.attivita, x, y + r * 2.4 + 26); }
      }
      continue;
    }
    // stanza: cluster di puntini e nome in maiuscolo spaziato
    c.fillStyle = n.colore;
    for (let i = 0; i < 14; i++) { const t = (i / 14) * Math.PI * 2 + hash01(n.id + i) * 0.4; const rr = (9 + 7 * hash01(n.id + 'r' + i)) * q.s; c.globalAlpha = 0.6 * L; c.beginPath(); c.arc(x + Math.cos(t) * rr, y + Math.sin(t) * rr, 1.4 * q.s, 0, Math.PI * 2); c.fill(); }
    punto(c, x, y, r * 1.1, n.colore, L);
    c.globalAlpha = 0.95 * L; c.fillStyle = n.colore; c.font = `700 ${piccolo ? 11 : 13}px system-ui, sans-serif`;
    etichetta(c, n.etichetta, x, y - 26 * q.s, piccolo ? 2 : 3.2);
  }
  c.globalAlpha = 1;
}

/** Strato vivo, sopra l'immagine ferma. t = millisecondi; rispondendo = il cervello sta rispondendo. Solo cerchi con globalAlpha. */
export function disegnaVita(c: CanvasRenderingContext2D, g: Grafo, geo: Geo, t: number, rispondendo: boolean) {
  const { P, k } = geo; const per = new Map(g.nodi.map((n) => [n.id, n]));
  const nu = per.get('nucleo');
  if (nu) { // respiro: alone che cresce e cala
    const [x, y] = P(nu); const r = respiro(t, rispondendo);
    punto(c, x, y, 17 * k * (1 + r.ampiezza * r.fase), COLORI_ATLAS.nucleo, 0.12 + (rispondendo ? 0.3 : 0.14) * r.fase);
    c.strokeStyle = COLORI_ATLAS.nucleo; c.lineWidth = 1; c.globalAlpha = 0.1 + 0.25 * r.fase * (rispondendo ? 1.6 : 1);
    c.beginPath(); c.arc(x, y, (30 + 34 * r.fase * (rispondendo ? 1 : 0.5)) * k, 0, Math.PI * 2); c.stroke();
  }
  let i = 0;
  for (const n of g.nodi) {
    if (n.tipo !== 'agente' || n.escluso) continue;
    const [x, y] = P(n); const padre = per.get(g.link.find((l) => l.a === n.id)?.da ?? 'nucleo');
    if (n.stato === 'attivo') { // impulsi nucleo > stanza > agente
      const pts: Pt[] = [P(nu ?? n)]; if (padre && padre.tipo === 'stanza') pts.push(P(padre)); pts.push([x, y]);
      for (let j = 0; j < 2; j++) {
        const u = faseImpulso(t, i, 2600) - j * 0.045; if (u < 0) continue;
        const [px, py] = puntoSulPercorso(pts, u);
        punto(c, px, py, j === 0 ? 2.3 : 1.5, n.colore, j === 0 ? 0.95 : 0.45);
      }
      i++;
    }
    if (n.stato === 'bloccato') { // anello che lampeggia ambra/rosso
      const f = lampeggio(t, 1100);
      c.strokeStyle = f > 0.5 ? COLORI_ATLAS.bloccato : COLORI_ATLAS.vendite; c.lineWidth = 1.8; c.globalAlpha = 0.25 + 0.7 * f;
      c.beginPath(); c.arc(x, y, n.raggio * (2.2 + 0.5 * f), 0, Math.PI * 2); c.stroke();
    }
    if (n.okInAttesa) { // puntino rosa che pulsa
      const f = lampeggio(t, 1500); const px = x + n.raggio * 1.9; const py = y - n.raggio * 1.9;
      c.strokeStyle = COLORI_ATLAS.ok; c.lineWidth = 1; c.globalAlpha = 0.5 * (1 - f); c.beginPath(); c.arc(px, py, 3 + 6 * f, 0, Math.PI * 2); c.stroke();
      punto(c, px, py, 2.4 + 0.9 * f, COLORI_ATLAS.ok, 0.7 + 0.3 * f);
    }
  }
  c.globalAlpha = 1;
}

/** Rettangolo del pannello iniziale del Centro letto dal DOM (coordinate di pagina), oppure una costante ragionevole. */
function leggiPannello(w: number): Rett | null {
  const el = document.querySelector('.drawer, .dettagli-centro');
  if (el) { const r = el.getBoundingClientRect(); if (r.width > 0 && r.height > 0) return { x: r.x + window.scrollX, y: r.y + window.scrollY, w: r.width, h: r.height }; }
  return w >= TELEFONO ? { x: 96, y: 100, w: 440, h: 470 } : null; // costante: colonna del Centro a sinistra
}
const CHIAVI: (keyof Rett)[] = ['x', 'y', 'w', 'h'];
const rettUguali = (a: Rett | null, b: Rett | null) => a === b || (!!a && !!b && CHIAVI.every((k) => Math.abs(a[k] - b[k]) < 2));

/** Il puntatore è su un punto "libero" della pagina (sfondo), non su pannelli, bottoni o schede. */
const OCCUPATO = 'button, a, input, select, textarea, label, [role="dialog"], .card, .drawer, .header, .rail, .dock, .palette, .modal, .toasts, .kpi, .item, .hero > div:last-child, .atlas-controlli, .demo-banner';
const libero = (t: EventTarget | null) => t instanceof Element && !t.closest(OCCUPATO);
const dentro = (z: Rett, x: number, y: number) => x >= z.x - 20 && x <= z.x + z.w + 20 && y >= z.y - 20 && y <= z.y + z.h + 20;

interface Tip { id: string; x: number; y: number }

export default function Atlas() {
  const { snap, pensa, pingOk, voce, apri, pannello, paletteAperta, parete } = useG();
  const canvas = useRef<HTMLCanvasElement>(null);
  const radice = useRef<HTMLDivElement>(null);
  const rispondendo = useRef(false); rispondendo.current = pensa;
  const [dim, setDim] = useState(() => ({ w: window.innerWidth, h: window.innerHeight }));
  const [pannelloRett, setPannello] = useState<Rett | null>(() => leggiPannello(window.innerWidth));
  const [ridotto, setRidotto] = useState(() => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false);
  const [filtro, setFiltro] = useState<FiltroAtlas>(FILTRO_TUTTI);
  const [stanzaZoom, setStanzaZoom] = useState<string | null>(null);
  const [tip, setTip] = useState<Tip | null>(null);
  const [threeReady, setThreeReady] = useState(false);
  const stato = statoNucleo(snap, { pingOk, ascolta: voce === 'ascolto', pensa, parla: voce === 'parla' });
  const trePronto = useCallback(() => setThreeReady(true), []);
  const treFallback = useCallback(() => setThreeReady(false), []);
  const apriDispositivi = useCallback(() => apri({ p: 'dispositivi' }), [apri]);
  const apriAgente = useCallback((id: string) => apri({ p: 'agente', id }), [apri]);
  useEffect(() => {
    const misura = () => {
      setDim((d) => (d.w === window.innerWidth && d.h === window.innerHeight ? d : { w: window.innerWidth, h: window.innerHeight }));
      setPannello((p) => { const n = leggiPannello(window.innerWidth); return rettUguali(p, n) ? p : n; });
    };
    window.addEventListener('resize', misura);
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(misura) : null; ro?.observe(document.body);
    const t = window.setTimeout(misura, 300); // il Centro può montarsi dopo l'Atlas
    return () => { window.removeEventListener('resize', misura); ro?.disconnect(); window.clearTimeout(t); };
  }, []);
  useEffect(() => {
    const m = window.matchMedia?.('(prefers-reduced-motion: reduce)'); if (!m) return;
    const f = () => setRidotto(m.matches); m.addEventListener('change', f); return () => m.removeEventListener('change', f);
  }, []);
  const telefono = dim.w < TELEFONO;
  const base = useMemo(() => (snap ? conProfondita(disponi(costruisciGrafo(snap, { telefono }))) : null), [snap, telefono]);
  const grafo = useMemo(() => (base ? (filtraGrafo(base, filtro) as Grafo3) : null), [base, filtro]);
  const testo = snap ? riepilogoAtlas(snap, Date.now(), filtro) : 'Caricamento dei dati.';
  const zona = useMemo(() => {
    const sinistra = dim.w >= 721 ? 72 : 0; // rail del Centro
    const tutta = { x: sinistra, y: 64, w: dim.w - sinistra, h: Math.max(120, dim.h * (telefono ? 0.9 : 0.86) - 64) };
    const z = zonaLibera(tutta, pannelloRett);
    // se la zona libera è troppo stretta, il cervello usa tutto lo sfondo e il pannello di vetro gli sta davanti
    if (z.w * z.h >= tutta.w * tutta.h * 0.45) return z;
    if (!pannelloRett) return tutta;
    const x0 = pannelloRett.x + pannelloRett.w / 2; // dalla metà del pannello in poi: il nucleo resta visibile
    return { x: x0, y: tutta.y, w: Math.max(z.w, tutta.x + tutta.w - x0), h: tutta.h };
  }, [dim, pannelloRett, telefono]);

  // vista (zoom e pan): la corrente sta in un ref, l'animazione la sposta e chiede il ridisegno dello strato fermo
  const vistaRef = useRef<Vista>(VISTA_COMPLETA);
  const ridisegna = useRef<(() => void) | null>(null);
  const anim = useRef(0);
  const grafoRef = useRef<Grafo3 | null>(null); grafoRef.current = grafo;
  const geoRef = useRef<Geo>(geometria(zona));
  // rotazione: y = offset dato dal trascinamento (si somma alla rotazione automatica), x = inclinazione
  const rot = useRef({ y: 0.5, x: INCLINAZIONE });
  const trascina = useRef<{ x: number; y: number; mosso: boolean } | null>(null);
  const zonaRef = useRef(zona); zonaRef.current = zona;
  const vaiA = useCallback((target: Vista) => {
    cancelAnimationFrame(anim.current);
    const da = vistaRef.current; const rid = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
    if (rid) { vistaRef.current = target; ridisegna.current?.(); return; } // niente animazione: salto diretto
    const t0 = performance.now();
    const passo = (ora: number) => {
      const u = Math.min(1, (ora - t0) / DURATA_ZOOM_MS);
      vistaRef.current = interpolaVista(da, target, u); ridisegna.current?.();
      if (u < 1) anim.current = requestAnimationFrame(passo);
    };
    anim.current = requestAnimationFrame(passo);
  }, []);
  const zoomStanza = useCallback((id: string) => { const g = grafoRef.current; if (!g) return; setStanzaZoom(id); setTip(null); vaiA(vistaStanza(g, id)); }, [vaiA]);
  const vistaCompleta = useCallback(() => { setStanzaZoom(null); setTip(null); vaiA(VISTA_COMPLETA); }, [vaiA]);
  const cambiaFiltro = (f: FiltroAtlas) => { setFiltro(f); if (stanzaZoom) vistaCompleta(); };
  useEffect(() => () => cancelAnimationFrame(anim.current), []);

  // passaggio del mouse, clic e tocco: il canvas sta sotto la pagina, quindi si ascolta la finestra e si guarda se il punto è libero
  const azioni = useRef({ snap, apri, zoomStanza, vistaCompleta }); azioni.current = { snap, apri, zoomStanza, vistaCompleta };
  const toccato = useRef<string | null>(null);
  const trascinato = useRef(false);
  useEffect(() => {
    const trova = (e: MouseEvent, tocco: boolean): Nodo | null => {
      const g = grafoRef.current; if (!g || !libero(e.target) || !dentro(zonaRef.current, e.clientX, e.clientY)) return null;
      return nodoInPunto(g, geoRef.current.P, e.clientX, e.clientY, tocco);
    };
    const mossa = (e: PointerEvent) => {
      const tr = trascina.current;
      if (tr) {
        const dx = e.clientX - tr.x; const dy = e.clientY - tr.y;
        if (!tr.mosso && Math.hypot(dx, dy) < 5) return;
        tr.mosso = true; tr.x = e.clientX; tr.y = e.clientY; setTip(null);
        rot.current = { y: rot.current.y + dx * 0.006, x: Math.max(-0.7, Math.min(0.9, rot.current.x + dy * 0.004)) };
        document.documentElement.style.cursor = 'grabbing'; ridisegna.current?.(); return;
      }
      if (e.pointerType === 'touch') return;
      const n = trova(e, false);
      document.documentElement.style.cursor = n && n.tipo !== 'nucleo' ? 'pointer' : '';
      setTip((t) => (n ? { id: n.id, x: e.clientX, y: e.clientY } : t ? null : t));
    };
    const clic = (e: MouseEvent) => {
      if (trascinato.current) { trascinato.current = false; return; } // fine di un trascinamento, non un clic
      const pt = (e as PointerEvent).pointerType;
      const tocco = pt === 'touch' || (pt === undefined && !!window.matchMedia?.('(pointer: coarse)').matches);
      const n = trova(e, tocco);
      if (!n) { toccato.current = null; setTip(null); return; }
      if (tocco && toccato.current !== n.id) { toccato.current = n.id; setTip({ id: n.id, x: e.clientX, y: e.clientY }); return; } // primo tocco: tooltip
      toccato.current = null; setTip(null);
      const a = azioni.current; if (!a.snap) return; const az = schedaNodo(a.snap, n).apre;
      if (!az) return;
      if ('zoom' in az) a.zoomStanza(az.zoom); else a.apri({ p: az.p, id: az.id });
    };
    const tasto = (e: KeyboardEvent) => {
      if (e.key !== 'Escape') return;
      setTip(null); toccato.current = null;
      const v = vistaRef.current; if (v.z !== 1 || v.fx !== 0 || v.fy !== 0) azioni.current.vistaCompleta();
    };
    const giu = (e: PointerEvent) => { if (e.button === 0 && libero(e.target) && dentro(zonaRef.current, e.clientX, e.clientY)) trascina.current = { x: e.clientX, y: e.clientY, mosso: false }; };
    const su = () => { const tr = trascina.current; trascina.current = null; if (tr?.mosso) { trascinato.current = true; document.documentElement.style.cursor = ''; window.setTimeout(() => { trascinato.current = false; }, 0); } };
    const rotella = (e: WheelEvent) => {
      if (!libero(e.target) || !dentro(zonaRef.current, e.clientX, e.clientY)) return;
      e.preventDefault(); const v = vistaRef.current;
      vistaRef.current = { ...v, z: Math.max(0.6, Math.min(3, v.z * Math.exp(-e.deltaY * 0.0012))) }; ridisegna.current?.();
    };
    window.addEventListener('pointermove', mossa); window.addEventListener('click', clic); window.addEventListener('keydown', tasto);
    window.addEventListener('pointerdown', giu); window.addEventListener('pointerup', su); window.addEventListener('pointercancel', su); window.addEventListener('wheel', rotella, { passive: false });
    return () => {
      window.removeEventListener('pointermove', mossa); window.removeEventListener('click', clic); window.removeEventListener('keydown', tasto);
      window.removeEventListener('pointerdown', giu); window.removeEventListener('pointerup', su); window.removeEventListener('pointercancel', su); window.removeEventListener('wheel', rotella);
      document.documentElement.style.cursor = '';
    };
  }, []);

  useEffect(() => {
    if (threeReady) { radice.current?.setAttribute('data-atlas-fps', '0'); return; }
    const el = canvas.current; const c = el?.getContext('2d'); if (!el || !c) return;
    const dpr = Math.min(1.5, window.devicePixelRatio || 1);
    el.width = Math.round(dim.w * dpr); el.height = Math.round(dim.h * dpr);
    const g: Grafo3 = grafo ?? { nodi: [], link: [] };
    let dust = polvere(420, 7); const radiceEl = radice.current; const vuoto = !!snap && snap.agents.length === 0;
    let t0: number | null = null; let tUltimo = 0;
    // un fotogramma completo: tutto ruota, quindi niente strato fermo
    const disegnaTutto = (t: number) => {
      const geo = geometria(zona, vistaRef.current, rot.current.y + (ridotto ? 0 : angoloAuto(t)), rot.current.x); geoRef.current = geo;
      c.setTransform(dpr, 0, 0, dpr, 0, 0); disegna(c, g, dim.w, dim.h, vuoto, geo, dust);
      if (grafo) disegnaVita(c, grafo, geo, t, rispondendo.current);
    };
    disegnaTutto(0); ridisegna.current = () => disegnaTutto(tUltimo);
    if (!grafo || ridotto) { radiceEl?.setAttribute('data-atlas-fps', '0'); return () => { ridisegna.current = null; }; }

    let raf = 0; let ultimo: number | null = null; let conta = 0; let inizioFps = 0; let attivo = false; let lenti = 0;
    const frame = (ora: number) => {
      raf = requestAnimationFrame(frame);
      if (!devoDisegnare(ultimo, ora)) return;
      ultimo = ora; t0 ??= ora; inizioFps ||= ora; conta++; tUltimo = ora - t0;
      disegnaTutto(tUltimo);
      if (ora - inizioFps >= 1000) {
        const fps = Math.round((conta * 1000) / (ora - inizioFps)); radiceEl?.setAttribute('data-atlas-fps', String(fps));
        // qualità adattiva: se la grafica fatica, meno polvere decorativa
        lenti = fps < 22 ? lenti + 1 : 0; if (lenti >= 2 && dust.punti.length > 200) { dust = polvere(Math.round(dust.punti.length / 2), 7); lenti = 0; }
        radiceEl?.setAttribute('data-atlas-polvere', String(dust.punti.length)); conta = 0; inizioFps = ora;
      }
    };
    const aggiorna = () => {
      const vai = possoAnimare(document.hidden, ridotto);
      if (vai && !attivo) { attivo = true; ultimo = null; inizioFps = 0; conta = 0; raf = requestAnimationFrame(frame); }
      else if (!vai && attivo) { attivo = false; cancelAnimationFrame(raf); }
    };
    document.addEventListener('visibilitychange', aggiorna); aggiorna();
    return () => { document.removeEventListener('visibilitychange', aggiorna); cancelAnimationFrame(raf); ridisegna.current = null; };
  }, [grafo, dim, snap, zona, ridotto, telefono, threeReady]);

  const nodoTip = tip && grafo ? grafo.nodi.find((n) => n.id === tip.id) : undefined;
  const scheda: Scheda | null = nodoTip && snap ? schedaNodo(snap, nodoTip) : null;
  const stanze = (snap?.stanze ?? []).filter((st) => st.attiva).sort((a, b) => a.ordine - b.ordine);
  const nascondi = !!pannello || paletteAperta || parete;
  return (
    <div ref={radice} className="atlas-sfondo" data-atlas={grafo ? 'pronto' : 'attesa'} data-atlas-nodi={grafo?.nodi.length ?? 0} data-three-ready={threeReady}>
      <canvas ref={canvas} aria-hidden="true" />
      <ThreeBrain stato={stato} ridotto={ridotto} dispositivi={snap?.devices ?? []} agenti={snap?.agents ?? []}
        eventi={snap?.events ?? []} pannelloAperto={!!pannello} onReady={trePronto} onFallback={treFallback}
        onApriDispositivi={apriDispositivi} onApriAgente={apriAgente} />
      <p className="sr-only" role="status">{`Atlas di Guardian, in 3D. ${testo} I puntini tenui sullo sfondo sono solo decorativi.`}</p>
      {!nascondi && createPortal(
        <div className="atlas-controlli" role="group" aria-label="Filtri dell'Atlas">
          {telefono ? (
            <select aria-label="Filtra per stanza" value={filtro.stanza} onChange={(e) => cambiaFiltro({ ...filtro, stanza: e.target.value })}>
              <option value="tutti">Tutti</option>
              {stanze.map((st) => <option key={st.id} value={st.id}>{st.nome}</option>)}
            </select>
          ) : (
            <>
              <button type="button" aria-pressed={filtro.stanza === 'tutti'} aria-label="Mostra tutte le stanze" onClick={() => cambiaFiltro({ ...filtro, stanza: 'tutti' })}>Tutti</button>
              {stanze.map((st) => (
                <button key={st.id} type="button" aria-pressed={filtro.stanza === st.id} aria-label={`Mostra solo la stanza ${st.nome}`} onClick={() => cambiaFiltro({ ...filtro, stanza: st.id })}>{st.nome}</button>
              ))}
            </>
          )}
          <button type="button" role="switch" aria-checked={filtro.soloAttivi} aria-label="Solo attivi: mostra solo agenti e task al lavoro" onClick={() => cambiaFiltro({ ...filtro, soloAttivi: !filtro.soloAttivi })}>Solo attivi</button>
          {stanzaZoom && <button type="button" className="vista" aria-label="Vista completa: torna a tutto l'Atlas (tasto Esc)" onClick={vistaCompleta}>Vista completa</button>}
        </div>, document.body)}
      {scheda && tip && createPortal(
        <div className="atlas-tip" aria-hidden="true" style={{ left: Math.max(8, Math.min(tip.x + 14, dim.w - 260)), top: Math.max(8, Math.min(tip.y + 14, dim.h - 170)) }}>
          <strong>{scheda.titolo}</strong>
          <dl>{scheda.righe.map((r) => <div key={r.k}><dt>{r.k}</dt><dd>{r.v}</dd></div>)}</dl>
          {scheda.apre && <em>{'zoom' in scheda.apre ? 'Clic per ingrandire' : 'Clic per aprire'}</em>}
        </div>, document.body)}
    </div>
  );
}
