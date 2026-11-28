// Sfondo "Atlas": il cervello di Guardian come costellazione (nucleo > stanze > agenti > task). Canvas 2D.
// Strato fermo disegnato una volta (su canvas fuori schermo) + strato vivo a max 30 fps: impulsi sulle linee degli agenti attivi,
// respiro del nucleo, anelli lampeggianti per i bloccati, puntino rosa per "serve OK". Pausa con scheda nascosta,
// solo immagine ferma con prefers-reduced-motion. Niente blur né filter: cerchi e linee con globalAlpha.
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { COLORI_ATLAS, costruisciGrafo, devoDisegnare, DURATA_ZOOM_MS, disponi, faseImpulso, FILTRO_TUTTI, filtraGrafo, interpolaVista, lampeggio, nodoInPunto, possoAnimare,
  puntoSulPercorso, respiro, riepilogoAtlas, schedaNodo, stileStato, VISTA_COMPLETA, vistaStanza, zonaLibera, type FiltroAtlas, type Grafo, type Nodo, type Pt, type Rett, type Scheda, type Vista } from '../logic/atlas';
import { useG } from '../state';

const FONDO = '#050912';
const TELEFONO = 600;

/** Etichetta in maiuscolo spaziato, centrata (spaziatura a mano: letterSpacing non c'è in tutti i browser). */
function etichetta(c: CanvasRenderingContext2D, t: string, x: number, y: number, spazio: number) {
  const lettere = [...t.toUpperCase()]; const larg = lettere.map((l) => c.measureText(l).width);
  let px = x - (larg.reduce((a, b) => a + b, 0) + spazio * (lettere.length - 1)) / 2;
  c.textAlign = 'left';
  lettere.forEach((l, i) => { c.fillText(l, px, y); px += larg[i] + spazio; });
}

function punto(c: CanvasRenderingContext2D, x: number, y: number, r: number, colore: string, alpha: number) {
  c.fillStyle = colore;
  c.globalAlpha = alpha * 0.1; c.beginPath(); c.arc(x, y, r * 3.2, 0, Math.PI * 2); c.fill(); // alone largo
  c.globalAlpha = alpha * 0.22; c.beginPath(); c.arc(x, y, r * 1.9, 0, Math.PI * 2); c.fill(); // alone vicino
  c.globalAlpha = alpha; c.beginPath(); c.arc(x, y, r, 0, Math.PI * 2); c.fill();
}

/** Da coordinate normalizzate [-1,1] a pixel, dentro la zona libera (fuori dal pannello del Centro). */
export function geometria(zona: Rett, v: Vista = VISTA_COMPLETA) {
  const pad = 34; const cx = zona.x + zona.w / 2; const cy = zona.y + zona.h / 2;
  const sx = Math.max(20, zona.w / 2 - pad); const sy = Math.max(20, zona.h / 2 - pad);
  const k = Math.max(0.55, Math.min(1, Math.min(zona.w, zona.h) / 600)); // scala di nucleo e caratteri
  const P = (n: { x: number; y: number }) => [cx + (n.x - v.fx) * sx * v.z, cy + (n.y - v.fy) * sy * v.z] as const;
  return { cx, cy, sx, sy, k, P };
}
type Geo = ReturnType<typeof geometria>;

export function disegna(c: CanvasRenderingContext2D, g: Grafo, w: number, h: number, vuoto: boolean, zona: Rett = { x: 0, y: 0, w, h }, vista: Vista = VISTA_COMPLETA) {
  const { k, P } = geometria(zona, vista); const piccolo = k < 0.8;
  c.clearRect(0, 0, w, h);
  c.fillStyle = FONDO; c.fillRect(0, 0, w, h);
  const per = new Map(g.nodi.map((n) => [n.id, n]));
  const colStanza = (id: string | null) => (id ? per.get(`s:${id}`)?.colore : undefined) ?? COLORI_ATLAS.nucleo;

  // linee sottili: 0.06 per i collegamenti fermi, fino a 0.15 per quelli di chi lavora
  c.lineWidth = 1;
  for (const l of g.link) {
    const a = per.get(l.da); const b = per.get(l.a); if (!a || !b) continue;
    const [x1, y1] = P(a); const [x2, y2] = P(b);
    c.strokeStyle = l.stato === 'fermo' ? (a.tipo === 'nucleo' ? colStanza(l.stanza) : COLORI_ATLAS.fermo) : stileStato(l.stato, colStanza(l.stanza)).colore;
    c.globalAlpha = a.escluso || b.escluso ? 0.03 : l.stato === 'fermo' ? (a.tipo === 'nucleo' ? 0.1 : 0.06) : 0.15;
    c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
  }

  // nucleo: disco ghiaccio, nucleo bianco e anelli di puntini
  const nu = per.get('nucleo');
  if (nu) {
    const [x, y] = P(nu);
    c.fillStyle = COLORI_ATLAS.nucleo;
    for (const [rg, n, al, rd] of [[64, 56, 0.16, 1.1], [48, 40, 0.28, 1.3], [34, 28, 0.42, 1.5]] as const) {
      c.globalAlpha = al;
      for (let i = 0; i < n; i++) { const t = (i / n) * Math.PI * 2; c.beginPath(); c.arc(x + Math.cos(t) * rg * k, y + Math.sin(t) * rg * k, rd, 0, Math.PI * 2); c.fill(); }
    }
    punto(c, x, y, 17 * k, COLORI_ATLAS.nucleo, 0.55);
    c.globalAlpha = 1; c.fillStyle = '#ffffff'; c.beginPath(); c.arc(x, y, 6 * k, 0, Math.PI * 2); c.fill();
    if (vuoto) {
      c.globalAlpha = 0.7; c.fillStyle = '#cfe6fb'; c.font = `500 ${piccolo ? 11 : 12}px system-ui, sans-serif`;
      etichetta(c, 'Nessun agente collegato', x, y + 92 * k, 2);
    }
  }

  // puntini piccoli (task ed eventi), poi agenti e stanze sopra
  for (const n of g.nodi) if (n.tipo === 'task' || n.tipo === 'evento') { const [x, y] = P(n); punto(c, x, y, n.raggio, n.colore, n.alpha); }
  for (const n of g.nodi) if (n.tipo === 'agente') {
    const [x, y] = P(n); const stile = stileStato(n.stato, n.colore);
    if (n.escluso) { punto(c, x, y, n.raggio, n.colore, 0.1); continue; }
    if (stile.fiore) { // "fiore" di puntini attorno a chi lavora
      c.fillStyle = stile.colore; c.globalAlpha = 0.7;
      for (let i = 0; i < 6; i++) { const t = (i / 6) * Math.PI * 2; c.beginPath(); c.arc(x + Math.cos(t) * n.raggio * 2.3, y + Math.sin(t) * n.raggio * 2.3, 1.4, 0, Math.PI * 2); c.fill(); }
    }
    if (stile.anello) { c.strokeStyle = stile.colore; c.globalAlpha = 0.7; c.lineWidth = 1.2; c.beginPath(); c.arc(x, y, n.raggio * 2.2, 0, Math.PI * 2); c.stroke(); }
    punto(c, x, y, n.raggio, n.colore, n.alpha);
    c.globalAlpha = n.alpha < 0.6 ? 0.55 : 0.8; c.fillStyle = '#cfd8e6'; c.font = '10px system-ui, sans-serif'; c.textAlign = 'center';
    c.fillText(n.etichetta, x, y + n.raggio * 2.2 + 12);
    if (n.attivita) { // cosa sta facendo (già tagliata a 40 caratteri con ellissi)
      c.globalAlpha = 0.65; c.fillStyle = stile.colore; c.font = '9px system-ui, sans-serif';
      c.fillText(n.attivita, x, y + n.raggio * 2.2 + 24);
    }
  }
  for (const n of g.nodi) if (n.tipo === 'stanza') {
    const [x, y] = P(n);
    if (n.escluso) { punto(c, x, y, n.raggio, n.colore, 0.1); continue; }
    c.fillStyle = n.colore;
    for (let i = 0; i < 8; i++) { const t = (i / 8) * Math.PI * 2; c.globalAlpha = 0.55; c.beginPath(); c.arc(x + Math.cos(t) * 13, y + Math.sin(t) * 13, 1.5, 0, Math.PI * 2); c.fill(); }
    punto(c, x, y, n.raggio, n.colore, 1);
    c.globalAlpha = 0.9; c.fillStyle = n.colore; c.font = `600 ${piccolo ? 10 : 11}px system-ui, sans-serif`;
    etichetta(c, n.etichetta, x, y - 24, piccolo ? 1.5 : 2.6);
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
  const el = document.querySelector('.hero > div:last-child');
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
  const { snap, pensa, apri, pannello, paletteAperta, parete } = useG();
  const canvas = useRef<HTMLCanvasElement>(null);
  const radice = useRef<HTMLDivElement>(null);
  const rispondendo = useRef(false); rispondendo.current = pensa;
  const [dim, setDim] = useState(() => ({ w: window.innerWidth, h: window.innerHeight }));
  const [pannelloRett, setPannello] = useState<Rett | null>(() => leggiPannello(window.innerWidth));
  const [ridotto, setRidotto] = useState(() => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false);
  const [filtro, setFiltro] = useState<FiltroAtlas>(FILTRO_TUTTI);
  const [stanzaZoom, setStanzaZoom] = useState<string | null>(null);
  const [tip, setTip] = useState<Tip | null>(null);
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
  const base = useMemo(() => (snap ? disponi(costruisciGrafo(snap, { telefono })) : null), [snap, telefono]);
  const grafo = useMemo(() => (base ? filtraGrafo(base, filtro) : null), [base, filtro]);
  const testo = snap ? riepilogoAtlas(snap, Date.now(), filtro) : 'Caricamento dei dati.';
  const zona = useMemo(() => {
    const sinistra = dim.w >= 721 ? 72 : 0; // rail del Centro
    return zonaLibera({ x: sinistra, y: 64, w: dim.w - sinistra, h: Math.max(120, dim.h * (telefono ? 0.9 : 0.86) - 64) }, pannelloRett);
  }, [dim, pannelloRett, telefono]);

  // vista (zoom e pan): la corrente sta in un ref, l'animazione la sposta e chiede il ridisegno dello strato fermo
  const vistaRef = useRef<Vista>(VISTA_COMPLETA);
  const ridisegna = useRef<(() => void) | null>(null);
  const anim = useRef(0);
  const grafoRef = useRef<Grafo | null>(null); grafoRef.current = grafo;
  const geoRef = useRef<Geo>(geometria(zona)); geoRef.current = geometria(zona, vistaRef.current);
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
  useEffect(() => {
    const trova = (e: MouseEvent, tocco: boolean): Nodo | null => {
      const g = grafoRef.current; if (!g || !libero(e.target) || !dentro(zonaRef.current, e.clientX, e.clientY)) return null;
      return nodoInPunto(g, geoRef.current.P, e.clientX, e.clientY, tocco);
    };
    const mossa = (e: PointerEvent) => {
      if (e.pointerType === 'touch') return;
      const n = trova(e, false);
      document.documentElement.style.cursor = n && n.tipo !== 'nucleo' ? 'pointer' : '';
      setTip((t) => (n ? { id: n.id, x: e.clientX, y: e.clientY } : t ? null : t));
    };
    const clic = (e: MouseEvent) => {
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
    window.addEventListener('pointermove', mossa); window.addEventListener('click', clic); window.addEventListener('keydown', tasto);
    return () => { window.removeEventListener('pointermove', mossa); window.removeEventListener('click', clic); window.removeEventListener('keydown', tasto); document.documentElement.style.cursor = ''; };
  }, []);

  useEffect(() => {
    const el = canvas.current; const c = el?.getContext('2d'); if (!el || !c) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    el.width = Math.round(dim.w * dpr); el.height = Math.round(dim.h * dpr);
    const g = grafo ?? { nodi: [], link: [] };
    const fermo = document.createElement('canvas'); fermo.width = el.width; fermo.height = el.height; const cf = fermo.getContext('2d'); if (!cf) return;
    const mostraFermo = () => { c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.drawImage(fermo, 0, 0); c.setTransform(dpr, 0, 0, dpr, 0, 0); };
    let geo = geometria(zona, vistaRef.current); const radiceEl = radice.current;
    const disegnaFermo = () => {
      cf.setTransform(dpr, 0, 0, dpr, 0, 0); disegna(cf, g, dim.w, dim.h, !!snap && snap.agents.length === 0, zona, vistaRef.current);
      geo = geometria(zona, vistaRef.current); mostraFermo();
    };
    disegnaFermo(); ridisegna.current = disegnaFermo;
    if (!grafo || ridotto) { radiceEl?.setAttribute('data-atlas-fps', '0'); return () => { ridisegna.current = null; }; }

    let raf = 0; let ultimo: number | null = null; let t0: number | null = null; let conta = 0; let inizioFps = 0; let attivo = false;
    const frame = (ora: number) => {
      raf = requestAnimationFrame(frame);
      if (!devoDisegnare(ultimo, ora)) return;
      ultimo = ora; t0 ??= ora; inizioFps ||= ora; conta++;
      mostraFermo(); disegnaVita(c, grafo, geo, ora - t0, rispondendo.current);
      if (ora - inizioFps >= 1000) { radiceEl?.setAttribute('data-atlas-fps', String(Math.round((conta * 1000) / (ora - inizioFps)))); conta = 0; inizioFps = ora; }
    };
    const aggiorna = () => {
      const vai = possoAnimare(document.hidden, ridotto);
      if (vai && !attivo) { attivo = true; ultimo = null; inizioFps = 0; conta = 0; raf = requestAnimationFrame(frame); }
      else if (!vai && attivo) { attivo = false; cancelAnimationFrame(raf); }
    };
    document.addEventListener('visibilitychange', aggiorna); aggiorna();
    return () => { document.removeEventListener('visibilitychange', aggiorna); cancelAnimationFrame(raf); ridisegna.current = null; };
  }, [grafo, dim, snap, zona, ridotto]);

  const nodoTip = tip && grafo ? grafo.nodi.find((n) => n.id === tip.id) : undefined;
  const scheda: Scheda | null = nodoTip && snap ? schedaNodo(snap, nodoTip) : null;
  const stanze = (snap?.stanze ?? []).filter((st) => st.attiva).sort((a, b) => a.ordine - b.ordine);
  const nascondi = !!pannello || paletteAperta || parete;
  return (
    <div ref={radice} className="atlas-sfondo" data-atlas={grafo ? 'pronto' : 'attesa'} data-atlas-nodi={grafo?.nodi.length ?? 0}>
      <canvas ref={canvas} aria-hidden="true" />
      <p className="sr-only" role="status">{`Atlas di Guardian. ${testo}`}</p>
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
