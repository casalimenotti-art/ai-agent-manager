// Il volto di NEXO Sentinel mostra SOLO stati reali: fase della conversazione, stato del nucleo, "sta pensando",
// livello del microfono, ampiezza della voce, richieste ed eventi appena arrivati. Funzioni pure e testate.
import type { StatoNucleo } from '../logic/guardian';
import type { Fase } from '../voce/motore';

export type RGB = [number, number, number];
export interface Ingressi {
  fase: Fase; nucleo: StatoNucleo; pensa: boolean; livelloMic: number; ampiezzaVoce: number;
  /** momenti in ms (performance.now) */
  ultimaRichiesta: number | null; ultimoEvento: number | null; adesso: number;
}
export interface Uscite {
  intensitaOcchio: number; coloreOcchio: RGB; intensitaAnelli: number; velocitaAnelli: number; coloreAnelli: RGB;
  aperturaIride: number; intensitaBocca: number; parallasse: [number, number]; flash: number; scansione: number;
  /** memoria interna per le transizioni */
  fase: Fase; nucleo: StatoNucleo; dalNucleo: number;
}

const NEUTRO: RGB = [1, 1, 1];
const AMBRA: RGB = [1.25, 0.95, 0.5];
const ROSSO: RGB = [1.9, 0.35, 0.3];
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));

/** Valori verso cui il volto si muove in questo istante (la tabella del prompt §4). */
export function bersaglio(i: Ingressi, dalNucleo = -1e9): Uscite {
  const t = i.adesso / 1000;
  const respiro = Math.sin((2 * Math.PI * t) / 7);
  let u: Uscite = {
    intensitaOcchio: 0.15, coloreOcchio: NEUTRO, intensitaAnelli: 0.05, velocitaAnelli: 0.15, coloreAnelli: NEUTRO,
    aperturaIride: 0.3, intensitaBocca: 0, parallasse: [0, respiro], flash: 0, scansione: 0,
    fase: i.fase, nucleo: i.nucleo, dalNucleo,
  };
  if (i.pensa || i.fase === 'elaborazione') {
    u = { ...u, intensitaOcchio: 0.6, intensitaAnelli: 0.8, velocitaAnelli: 2.6, aperturaIride: 0.6, scansione: 1 };
  } else if (i.fase === 'parla') {
    const a = clamp01(i.ampiezzaVoce);
    u = { ...u, intensitaOcchio: 0.55 + 0.45 * a, intensitaBocca: a, intensitaAnelli: 0.4, velocitaAnelli: 0.6, aperturaIride: 0.8,
      parallasse: [0, respiro * 0.5 + Math.sin(t * 2 * Math.PI * 0.9) * 1.5 * Math.min(1, a * 2)] };
  } else if (i.fase === 'ascolto' || i.fase === 'avvio') {
    u = { ...u, intensitaOcchio: 0.45, aperturaIride: 1, intensitaAnelli: 0.25 + 0.75 * clamp01(i.livelloMic * 4), velocitaAnelli: 0.4 };
  }
  if (i.nucleo === 'approval') {
    u = { ...u, coloreAnelli: AMBRA, intensitaAnelli: Math.max(u.intensitaAnelli, 0.3 + 0.12 * Math.sin(t * 2.2)) };
  }
  if (i.nucleo === 'error' || i.nucleo === 'offline') {
    const da = i.adesso - dalNucleo;
    const sfarfalla = da < 600 ? (Math.sin(da / 18) > 0 ? 0.7 : 0.15) : 0.08;
    u = { ...u, intensitaOcchio: sfarfalla, coloreOcchio: ROSSO, coloreAnelli: ROSSO, intensitaAnelli: 0.05, velocitaAnelli: 0.05, aperturaIride: 0.15 };
  }
  // richiesta ricevuta: si sveglia (lampo 120 ms, occhio 0.7, testa che si alza e torna in 1,2 s)
  if (i.ultimaRichiesta != null) {
    const d = i.adesso - i.ultimaRichiesta;
    if (d >= 0 && d < 1500) {
      if (d < 120) u.flash = Math.max(u.flash, 1 - d / 120);
      u.intensitaOcchio = Math.max(u.intensitaOcchio, 0.7 * Math.min(1, d / 300 + 0.4));
      const sale = d < 250 ? d / 250 : Math.max(0, 1 - (d - 250) / 1200);
      u.parallasse = [u.parallasse[0], u.parallasse[1] - 4 * sale];
    }
  }
  if (i.ultimoEvento != null) {
    const d = i.adesso - i.ultimoEvento;
    if (d >= 0 && d < 80) u.flash = Math.max(u.flash, 0.3 * (1 - d / 80));
  }
  return u;
}

/** Un passo di animazione: smorzamento morbido verso il bersaglio; il lampo e il barge-in sono immediati. */
export function statoVolto(i: Ingressi, prec: Uscite | null, dt: number): Uscite {
  const dalNucleo = !prec || prec.nucleo !== i.nucleo ? i.adesso : prec.dalNucleo;
  const b = bersaglio(i, dalNucleo);
  if (!prec) return b;
  const bargeIn = prec.fase === 'parla' && i.fase === 'ascolto';
  const k = (tau: number) => 1 - Math.exp(-dt / tau);
  const m = (a: number, c: number, tau = 0.18) => a + (c - a) * k(tau);
  const mc = (a: RGB, c: RGB): RGB => [m(a[0], c[0], 0.25), m(a[1], c[1], 0.25), m(a[2], c[2], 0.25)];
  const errore = i.nucleo === 'error' || i.nucleo === 'offline';
  return {
    ...b,
    intensitaOcchio: bargeIn || errore ? b.intensitaOcchio : m(prec.intensitaOcchio, b.intensitaOcchio, b.intensitaOcchio > prec.intensitaOcchio ? 0.12 : 0.22),
    intensitaBocca: bargeIn ? 0 : m(prec.intensitaBocca, b.intensitaBocca, 0.06),
    intensitaAnelli: m(prec.intensitaAnelli, b.intensitaAnelli, 0.2),
    velocitaAnelli: m(prec.velocitaAnelli, b.velocitaAnelli, 0.5),
    aperturaIride: m(prec.aperturaIride, b.aperturaIride, 0.25),
    coloreOcchio: errore ? b.coloreOcchio : mc(prec.coloreOcchio, b.coloreOcchio),
    coloreAnelli: mc(prec.coloreAnelli, b.coloreAnelli),
    parallasse: [m(prec.parallasse[0], b.parallasse[0], 0.15), m(prec.parallasse[1], b.parallasse[1], 0.15)],
    scansione: m(prec.scansione, b.scansione, 0.3),
    // durante il barge-in la fase "parla" non deve rientrare: restiamo in ascolto
    fase: i.fase,
  };
}

/** Copertura tipo object-fit: cover, spostata in modo che l'occhio cada vicino a `punto` (frazioni dello schermo). */
export function copertura(W: number, H: number, w: number, h: number, occhio: [number, number], punto: [number, number]) {
  const scala = Math.max(W / w, H / h) * 1.04; // un filo di margine per la parallasse
  const lw = w * scala, lh = h * scala;
  const x = Math.min(0, Math.max(W - lw, punto[0] * W - occhio[0] * scala));
  const y = Math.min(0, Math.max(H - lh, punto[1] * H - occhio[1] * scala));
  return { scala, x, y };
}
