import { describe, expect, it } from 'vitest';
import { bersaglio, copertura, statoVolto, type Ingressi, type Uscite } from './stati';

const base = (p: Partial<Ingressi> = {}): Ingressi => ({ fase: 'spento', nucleo: 'idle', pensa: false, livelloMic: 0, ampiezzaVoce: 0,
  ultimaRichiesta: null, ultimoEvento: null, adesso: 10_000, ...p });
/** Simula `ms` millisecondi a 60 fps partendo da uno stato già assestato su `da`. */
function simula(da: Ingressi, a: (t: number) => Ingressi, ms: number): Uscite {
  let u: Uscite | null = null;
  for (let t = 0; t < 3000; t += 16) u = statoVolto({ ...da, adesso: da.adesso - 3000 + t }, u, 0.016);
  for (let t = 0; t <= ms; t += 16) u = statoVolto(a(t), u, 0.016);
  return u!;
}

describe('volto: stati reali → animazione', () => {
  it('inattivo: occhio fioco (~15%), iride socchiusa, respiro lento', () => {
    const b = bersaglio(base());
    expect(b.intensitaOcchio).toBeCloseTo(0.15, 2);
    expect(b.aperturaIride).toBeCloseTo(0.3, 2);
    expect(Math.abs(b.parallasse[1])).toBeLessThanOrEqual(1);
  });
  it('richiesta ricevuta: lampo, occhio a 0.7, testa che si alza e poi torna', () => {
    const t0 = 10_000;
    const subito = bersaglio(base({ ultimaRichiesta: t0, adesso: t0 + 40 }));
    expect(subito.flash).toBeGreaterThan(0.5);
    const dopo = bersaglio(base({ ultimaRichiesta: t0, adesso: t0 + 300 }));
    expect(dopo.intensitaOcchio).toBeGreaterThanOrEqual(0.7);
    expect(dopo.parallasse[1]).toBeLessThan(-2);
    expect(bersaglio(base({ ultimaRichiesta: t0, adesso: t0 + 2000 })).parallasse[1]).toBeGreaterThan(-1.1);
  });
  it('pensa: anelli accesi e veloci', () => {
    const b = bersaglio(base({ pensa: true }));
    expect(b.intensitaAnelli).toBeCloseTo(0.8, 2);
    expect(b.velocitaAnelli).toBeGreaterThan(1.5);
    expect(bersaglio(base({ fase: 'elaborazione' })).intensitaAnelli).toBeCloseTo(0.8, 2);
  });
  it('parla: occhio e bocca seguono l\'ampiezza della voce', () => {
    expect(bersaglio(base({ fase: 'parla', ampiezzaVoce: 1 })).intensitaOcchio).toBeCloseTo(1, 2);
    expect(bersaglio(base({ fase: 'parla', ampiezzaVoce: 0 })).intensitaOcchio).toBeCloseTo(0.55, 2);
    expect(bersaglio(base({ fase: 'parla', ampiezzaVoce: 0.6 })).intensitaBocca).toBeCloseTo(0.6, 2);
  });
  it('ascolta: iride aperta, anello sul livello del microfono', () => {
    const b = bersaglio(base({ fase: 'ascolto', livelloMic: 0.5 }));
    expect(b.aperturaIride).toBe(1);
    expect(b.intensitaAnelli).toBeGreaterThan(bersaglio(base({ fase: 'ascolto', livelloMic: 0 })).intensitaAnelli);
    expect(b.intensitaOcchio).toBeCloseTo(0.45, 2);
  });
  it('evento nuovo: lampo breve', () => {
    expect(bersaglio(base({ ultimoEvento: 9_960 })).flash).toBeGreaterThan(0.1);
    expect(bersaglio(base({ ultimoEvento: 9_800 })).flash).toBe(0);
  });
  it('barge-in: occhio e bocca giù in meno di 200 ms', () => {
    const parla = base({ fase: 'parla', ampiezzaVoce: 1 });
    const u = simula(parla, (t) => base({ fase: 'ascolto', adesso: 10_000 + t }), 192);
    expect(u.intensitaBocca).toBeLessThan(0.05);
    expect(u.intensitaOcchio).toBeLessThan(0.5);
  });
  it('approvazione: anelli ambra; errore: sfarfallio rosso poi occhio fioco', () => {
    const a = bersaglio(base({ nucleo: 'approval' }));
    expect(a.coloreAnelli[0]).toBeGreaterThan(a.coloreAnelli[2]);
    const e = simula(base(), (t) => base({ nucleo: 'error', adesso: 10_000 + t }), 900);
    expect(e.intensitaOcchio).toBeLessThan(0.12);
    expect(e.coloreOcchio[0]).toBeGreaterThan(e.coloreOcchio[2]);
  });
  it('smorzamento: niente scatti (tranne lampo e barge-in)', () => {
    const u0 = simula(base(), () => base(), 0);
    const u1 = statoVolto(base({ pensa: true }), u0, 0.016);
    expect(u1.intensitaAnelli - u0.intensitaAnelli).toBeLessThan(0.2);
  });
});

describe('copertura dello schermo', () => {
  it('riempie lo schermo e porta l\'occhio verso il punto voluto senza scoprire i bordi', () => {
    const c = copertura(1440, 900, 1920, 1080, [820, 560], [0.58, 0.42]);
    expect(1920 * c.scala).toBeGreaterThanOrEqual(1440);
    expect(1080 * c.scala).toBeGreaterThanOrEqual(900);
    expect(c.x).toBeLessThanOrEqual(0); expect(c.x + 1920 * c.scala).toBeGreaterThanOrEqual(1440);
    expect(Math.abs(c.x + 820 * c.scala - 0.58 * 1440)).toBeLessThan(260);
  });
  it('a schermo stretto (telefono) l\'occhio resta visibile', () => {
    const c = copertura(390, 844, 960, 540, [410, 280], [0.5, 0.35]);
    const ox = c.x + 410 * c.scala;
    expect(ox).toBeGreaterThan(0); expect(ox).toBeLessThan(390);
  });
});
