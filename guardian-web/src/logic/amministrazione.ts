// Ondate 5 e 7: numeri delle stanze Vendite e Amministrazione, calcolati solo dai dati inseriti (migrazione 008).
import { FASI_VENDITA, type Costo, type FaseVendita, type Scadenza, type Vendita } from '../types';

const GIORNO = 86_400_000;
const giornoLocale = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
/** Giorni da oggi alla data (negativi = scaduta). */
export const giorniA = (data: string, oggi = new Date()) => Math.round((Date.parse(`${data}T00:00:00`) - giornoLocale(oggi)) / GIORNO);

export function scadenzeDaGuardare(sc: Scadenza[], giorni = 14, oggi = new Date()) {
  return sc.filter((s) => s.stato === 'aperta' && giorniA(s.data, oggi) <= giorni).sort((a, b) => a.data.localeCompare(b.data));
}

/** Spesa del mese corrente: ricorrenti mensili + annuali divisi per 12 + una tantum con data in questo mese. */
export function costoMese(costi: Costo[], oggi = new Date()) {
  const mese = `${oggi.getFullYear()}-${String(oggi.getMonth() + 1).padStart(2, '0')}`;
  let totale = 0; const perCategoria: Record<string, number> = {};
  for (const c of costi) {
    const quota = c.ricorrenza === 'mensile' ? c.importo_eur : c.ricorrenza === 'annuale' ? c.importo_eur / 12 : c.data.startsWith(mese) ? c.importo_eur : 0;
    if (!quota) continue;
    totale += quota; perCategoria[c.categoria] = (perCategoria[c.categoria] ?? 0) + quota;
  }
  return { totale: Math.round(totale * 100) / 100, perCategoria, ricorrenti: costi.filter((c) => c.ricorrenza !== 'una_tantum').length };
}

export function pipelinePerFase(v: Vendita[]) {
  const fasi = Object.fromEntries(FASI_VENDITA.map((f) => [f, { numero: 0, valore: 0 }])) as Record<FaseVendita, { numero: number; valore: number }>;
  for (const x of v) { fasi[x.fase].numero++; fasi[x.fase].valore += x.valore_eur ?? 0; }
  const aperte = v.filter((x) => x.fase !== 'vinto' && x.fase !== 'perso');
  const chiuse = fasi.vinto.numero + fasi.perso.numero;
  return { fasi, aperte: aperte.length, valoreAperto: aperte.reduce((t, x) => t + (x.valore_eur ?? 0), 0),
    tassoVittoria: chiuse ? Math.round((fasi.vinto.numero / chiuse) * 100) : null };
}

export const euro = (n: number) => new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: n % 1 ? 2 : 0 }).format(n);
