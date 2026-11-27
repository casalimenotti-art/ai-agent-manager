// Sfondo vivo dell'HQ: il volto di NEXO Sentinel. Strati renderizzati in Blender, composti dal vivo con WebGL2.
// Si anima solo con stati reali (conversazione, nucleo, richieste, eventi). Non segue il cursore.
import { useEffect, useRef, useState } from 'react';
import { statoNucleo } from '../logic/guardian';
import { leggiPreferenze, useG } from '../state';
import { useConversazione } from '../ui/Conversazione';
import { Compositore, STRATI, type Meta, type Strato } from './shader';
import { decadiAmpiezza, segnalaEvento, segnali } from './segnali';
import { copertura, statoVolto, type Ingressi, type Uscite } from './stati';

const BASE = `${import.meta.env.BASE_URL}volto/`;
type Modalita = 'webgl' | 'immagine';

function sceltaModalita(): { modalita: Modalita; piccolo: boolean } {
  const piccolo = window.innerWidth < 720;
  const ridotto = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  const pref = leggiPreferenze().volto;
  let gl = false;
  try { gl = !!document.createElement('canvas').getContext('webgl2'); } catch { gl = false; }
  return { modalita: !piccolo && !ridotto && gl && pref !== 'immagine' ? 'webgl' : 'immagine', piccolo };
}

async function carica(cartella: string, strati: readonly Strato[]) {
  const imgs = await Promise.all(strati.map(async (s) => {
    const r = await fetch(`${cartella}${s}.webp`);
    if (!r.ok) throw new Error(`strato ${s} mancante`);
    return [s, await createImageBitmap(await r.blob())] as const;
  }));
  return Object.fromEntries(imgs) as Record<Strato, ImageBitmap>;
}

export default function VoltoSfondo({ punto = [0.62, 0.42] }: { punto?: [number, number] }) {
  const { snap, pingOk, pensa } = useG();
  const conv = useConversazione();
  const contenitore = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const bagliore = useRef<HTMLDivElement>(null);
  const img = useRef<HTMLImageElement>(null);
  const [scelta] = useState(sceltaModalita);
  const [modalita, setModalita] = useState<Modalita>(scelta.modalita);
  const [meta, setMeta] = useState<Meta | null>(null);
  const cartella = scelta.piccolo || modalita === 'immagine' ? `${BASE}960/` : BASE;
  const k = cartella.endsWith('960/') ? 0.5 : 1; // gli strati da 960 px sono metà di quelli descritti in meta.json

  // ingressi reali, letti a ogni frame senza re-render
  const ingressi = useRef<Omit<Ingressi, 'adesso' | 'ultimaRichiesta' | 'ultimoEvento' | 'ampiezzaVoce'>>({ fase: 'spento', nucleo: 'idle', pensa: false, livelloMic: 0 });
  const opz = { pingOk, ascolta: conv.fase === 'ascolto', pensa: pensa || conv.fase === 'elaborazione', parla: conv.fase === 'parla' };
  ingressi.current = { fase: conv.fase, nucleo: statoNucleo(snap, opz), pensa, livelloMic: conv.livello };
  const puntoEff = punto;
  const puntoRef = useRef(puntoEff); puntoRef.current = puntoEff;

  // evento nuovo (Realtime o demo): breve lampo
  const ultimoId = useRef<number | null>(null);
  useEffect(() => {
    const id = snap?.events[0]?.id ?? null;
    if (ultimoId.current !== null && id !== null && id !== ultimoId.current) segnalaEvento();
    ultimoId.current = id;
  }, [snap?.events]);

  useEffect(() => {
    let vivo = true;
    fetch(`${BASE}meta.json`).then((r) => r.json()).then((m: Meta) => {
      if (!vivo) return;
      const s = (p: [number, number]): [number, number] => [p[0] * k, p[1] * k];
      setMeta({ ...m, larghezza: m.larghezza * k, altezza: m.altezza * k,
        occhio: { centro: s(m.occhio.centro), asse_x: s(m.occhio.asse_x), asse_y: s(m.occhio.asse_y) },
        iride: { ...m.iride, rettangolo: m.iride.rettangolo.map((v) => v * k) as Meta['iride']['rettangolo'] } });
    }).catch(() => setModalita('immagine'));
    return () => { vivo = false; };
  }, [k]);

  useEffect(() => {
    if (!meta) return;
    let comp: Compositore | null = null;
    let raf = 0, ultimo = performance.now(), rot = 0, prec: Uscite | null = null, ultimoAttr = 0, ultimoDisegno = 0, lampi = 0, inLampo = false;
    let annullato = false;
    const avvia = async () => {
      if (modalita === 'webgl' && canvas.current) {
        try {
          comp = new Compositore(canvas.current, meta, await carica(cartella, STRATI));
          canvas.current.addEventListener('webglcontextlost', () => { comp = null; setModalita('immagine'); });
        } catch { if (!annullato) setModalita('immagine'); return; }
      }
      if (annullato) { comp?.distruggi(); return; }
      contenitore.current?.setAttribute('data-volto-modalita', modalita);
      contenitore.current?.classList.add('pronto');
      const passo = (ora: number) => {
        raf = requestAnimationFrame(passo);
        if (document.hidden) return;
        const dt = Math.min(0.1, (ora - ultimo) / 1000); ultimo = ora;
        decadiAmpiezza(dt);
        const i: Ingressi = { ...ingressi.current, ampiezzaVoce: segnali.ampiezza, ultimaRichiesta: segnali.ultimaRichiesta, ultimoEvento: segnali.ultimoEvento, adesso: ora };
        prec = statoVolto(i, prec, dt);
        rot += prec.velocitaAnelli * dt * 0.8;
        if (prec.flash > 0.05 && !inLampo) { lampi++; contenitore.current?.setAttribute('data-volto-lampi', String(lampi)); }
        inLampo = prec.flash > 0.05;
        if (contenitore.current && contenitore.current.dataset.voltoFase !== i.fase) contenitore.current.dataset.voltoFase = i.fase;
        // a riposo bastano ~15 fotogrammi al secondo
        const recente = Math.max(i.ultimaRichiesta ?? -1e9, i.ultimoEvento ?? -1e9) > ora - 3000;
        const riposo = i.fase === 'spento' && !i.pensa && !recente && (i.nucleo === 'idle' || i.nucleo === 'working');
        if (riposo && ora - ultimoDisegno < 66) return;
        ultimoDisegno = ora;
        const el = contenitore.current; if (!el) return;
        const W = el.clientWidth, H = el.clientHeight;
        const cop = copertura(W, H, meta.larghezza, meta.altezza, meta.occhio.centro, puntoRef.current);
        if (comp && canvas.current) {
          const dpr = Math.min(1.5, window.devicePixelRatio || 1);
          const cw = Math.round(W * dpr), ch = Math.round(H * dpr);
          if (canvas.current.width !== cw || canvas.current.height !== ch) { canvas.current.width = cw; canvas.current.height = ch; }
          comp.disegna(prec, rot, ora / 1000, cop);
        } else if (img.current && bagliore.current) {
          img.current.style.transform = `translate(${cop.x}px, ${cop.y}px) scale(${cop.scala})`;
          const [cx, cy] = meta.occhio.centro;
          const r = Math.hypot(...meta.occhio.asse_x) * cop.scala;
          const b = bagliore.current.style;
          b.left = `${cop.x + cx * cop.scala - r * 1.6}px`; b.top = `${cop.y + cy * cop.scala - r * 1.6}px`;
          b.width = b.height = `${r * 3.2}px`;
          b.opacity = String(Math.min(1, prec.intensitaOcchio * 1.1 + prec.flash * 0.5));
        }
        if (ora - ultimoAttr > 100) {
          ultimoAttr = ora;
          el.setAttribute('data-volto-intensita', (Math.round(prec.intensitaOcchio * 20) / 20).toFixed(2));
        }
      };
      raf = requestAnimationFrame(passo);
    };
    void avvia();
    return () => { annullato = true; cancelAnimationFrame(raf); comp?.distruggi(); };
  }, [meta, modalita, cartella]);

  return (
    <div ref={contenitore} className="volto-sfondo" aria-hidden="true" data-volto-modalita={modalita} data-volto-fase="spento" data-volto-intensita="0.15">
      {modalita === 'webgl' ? <canvas ref={canvas} /> : <>
        <img ref={img} src={`${cartella}base.webp`} alt="" className="volto-img" />
        <div ref={bagliore} className="volto-bagliore" />
      </>}
    </div>
  );
}
