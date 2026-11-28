// Sfondo "Atlas": il cervello di Guardian come costellazione (nucleo > stanze > agenti > task). Canvas 2D, nessuna animazione
// continua in questa ondata: si ridisegna solo quando cambiano i dati o la finestra. Niente blur né filter: cerchi e linee con globalAlpha.
import { useEffect, useMemo, useRef, useState } from 'react';
import { COLORI_ATLAS, costruisciGrafo, disponi, riepilogoAtlas, stileStato, type Grafo } from '../logic/atlas';
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

export function disegna(c: CanvasRenderingContext2D, g: Grafo, w: number, h: number, vuoto: boolean) {
  const piccolo = w < TELEFONO;
  c.clearRect(0, 0, w, h);
  c.fillStyle = FONDO; c.fillRect(0, 0, w, h);
  const cx = w * (w >= 900 ? 0.62 : 0.5); const cy = h * 0.5; // su schermo largo il nucleo sta a destra del pannello iniziale
  const sx = (w >= 900 ? w * 0.34 : w * 0.42); const sy = h * (piccolo ? 0.36 : 0.4);
  const P = (n: { x: number; y: number }) => [cx + n.x * sx, cy + n.y * sy] as const;
  const per = new Map(g.nodi.map((n) => [n.id, n]));
  const colStanza = (id: string | null) => (id ? per.get(`s:${id}`)?.colore : undefined) ?? COLORI_ATLAS.nucleo;

  // linee sottili: 0.06 per i collegamenti fermi, fino a 0.15 per quelli di chi lavora
  c.lineWidth = 1;
  for (const l of g.link) {
    const a = per.get(l.da); const b = per.get(l.a); if (!a || !b) continue;
    const [x1, y1] = P(a); const [x2, y2] = P(b);
    c.strokeStyle = l.stato === 'fermo' ? (a.tipo === 'nucleo' ? colStanza(l.stanza) : COLORI_ATLAS.fermo) : stileStato(l.stato, colStanza(l.stanza)).colore;
    c.globalAlpha = l.stato === 'fermo' ? (a.tipo === 'nucleo' ? 0.1 : 0.06) : 0.15;
    c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
  }

  // nucleo: disco ghiaccio, nucleo bianco e anelli di puntini
  const nu = per.get('nucleo');
  if (nu) {
    const [x, y] = P(nu); const k = piccolo ? 0.8 : 1;
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
    if (stile.fiore) { // "fiore" di puntini attorno a chi lavora
      c.fillStyle = stile.colore; c.globalAlpha = 0.7;
      for (let i = 0; i < 6; i++) { const t = (i / 6) * Math.PI * 2; c.beginPath(); c.arc(x + Math.cos(t) * n.raggio * 2.3, y + Math.sin(t) * n.raggio * 2.3, 1.4, 0, Math.PI * 2); c.fill(); }
    }
    if (stile.anello) { c.strokeStyle = stile.colore; c.globalAlpha = 0.7; c.lineWidth = 1.2; c.beginPath(); c.arc(x, y, n.raggio * 2.2, 0, Math.PI * 2); c.stroke(); }
    punto(c, x, y, n.raggio, n.colore, n.alpha);
    c.globalAlpha = n.alpha < 0.6 ? 0.55 : 0.8; c.fillStyle = '#cfd8e6'; c.font = '10px system-ui, sans-serif'; c.textAlign = 'center';
    c.fillText(n.etichetta, x, y + n.raggio * 2.2 + 12);
  }
  for (const n of g.nodi) if (n.tipo === 'stanza') {
    const [x, y] = P(n);
    c.fillStyle = n.colore;
    for (let i = 0; i < 8; i++) { const t = (i / 8) * Math.PI * 2; c.globalAlpha = 0.55; c.beginPath(); c.arc(x + Math.cos(t) * 13, y + Math.sin(t) * 13, 1.5, 0, Math.PI * 2); c.fill(); }
    punto(c, x, y, n.raggio, n.colore, 1);
    c.globalAlpha = 0.9; c.fillStyle = n.colore; c.font = `600 ${piccolo ? 10 : 11}px system-ui, sans-serif`;
    etichetta(c, n.etichetta, x, y - 24, piccolo ? 1.5 : 2.6);
  }
  c.globalAlpha = 1;
}

export default function Atlas() {
  const { snap } = useG();
  const canvas = useRef<HTMLCanvasElement>(null);
  const [dim, setDim] = useState(() => ({ w: window.innerWidth, h: window.innerHeight }));
  useEffect(() => {
    const f = () => setDim({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener('resize', f); return () => window.removeEventListener('resize', f);
  }, []);
  const telefono = dim.w < TELEFONO;
  const grafo = useMemo(() => (snap ? disponi(costruisciGrafo(snap, { telefono })) : null), [snap, telefono]);
  const testo = snap ? riepilogoAtlas(snap) : 'Caricamento dei dati.';
  useEffect(() => {
    const el = canvas.current; const c = el?.getContext('2d'); if (!el || !c) return;
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    el.width = Math.round(dim.w * dpr); el.height = Math.round(dim.h * dpr);
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    disegna(c, grafo ?? { nodi: [], link: [] }, dim.w, dim.h, !!snap && snap.agents.length === 0);
  }, [grafo, dim, snap]);
  return (
    <div className="atlas-sfondo" data-atlas={grafo ? 'pronto' : 'attesa'} data-atlas-nodi={grafo?.nodi.length ?? 0}>
      <canvas ref={canvas} aria-hidden="true" />
      <p className="sr-only" role="status">{`Atlas di Guardian. ${testo}`}</p>
    </div>
  );
}
