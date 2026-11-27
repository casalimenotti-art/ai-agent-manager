// Catalogo delle metriche (vedi PIANO.md): ogni numero ha una definizione e una fonte. Mai valori inventati.
import type { Snapshot } from '../types';
import { AGENTI_AL_LAVORO, statoAgente, statoDispositivo } from './status';

const GIORNO = 86_400_000;
const inizioGiorno = (ora: number) => { const d = new Date(ora); d.setHours(0, 0, 0, 0); return d.getTime(); };

export function agentiAlLavoro(s: Snapshot, ora?: number) { return s.agents.filter((a) => AGENTI_AL_LAVORO.includes(statoAgente(a, ora))).length; }
export function agentiConSegnale(s: Snapshot, ora?: number) { return s.agents.filter((a) => !['unknown', 'offline'].includes(statoAgente(a, ora))).length; }
export function pcOnline(s: Snapshot, ora?: number) { return s.devices.filter((d) => statoDispositivo(d, ora) !== 'offline').length; }

/** Eventi task_completed con timestamp di oggi (ora locale). Fonte: activity_events. */
export function completatiOggi(s: Snapshot, ora = Date.now()) {
  const da = inizioGiorno(ora);
  return s.events.filter((e) => e.event_type === 'task_completed' && Date.parse(e.timestamp) >= da).length;
}

/** completed / (completed + failed + cancelled) tra i task aggiornati negli ultimi `giorni`. null se nessun task chiuso. */
export function tassoCompletamento(s: Snapshot, giorni = 7, ora = Date.now()): number | null {
  const da = ora - giorni * GIORNO;
  const chiusi = s.tasks.filter((t) => ['completed', 'failed', 'cancelled'].includes(t.stato) && Date.parse(t.updated_at) >= da);
  return chiusi.length ? chiusi.filter((t) => t.stato === 'completed').length / chiusi.length : null;
}

/** Durata media (ore) da task_started a task_completed per i task che hanno entrambi gli eventi. null se nessuno. */
export function durataMediaOre(s: Snapshot): number | null {
  const inizio = new Map<number, number>(); const durate: number[] = [];
  for (const e of [...s.events].sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp))) {
    if (!e.task_id) continue;
    if (e.event_type === 'task_started' && !inizio.has(e.task_id)) inizio.set(e.task_id, Date.parse(e.timestamp));
    if (e.event_type === 'task_completed' && inizio.has(e.task_id)) durate.push((Date.parse(e.timestamp) - inizio.get(e.task_id)!) / 3_600_000);
  }
  return durate.length ? durate.reduce((a, b) => a + b, 0) / durate.length : null;
}

export function errori24h(s: Snapshot, ora = Date.now()) {
  return s.events.filter((e) => (e.severity === 'error' || e.severity === 'critical') && ora - Date.parse(e.timestamp) < GIORNO).length;
}

/** Eventi per giorno negli ultimi `giorni` (inclusi i giorni a zero). Fonte: activity_events. */
export function attivitaPerGiorno(s: Snapshot, giorni = 14, ora = Date.now()) {
  const oggi = inizioGiorno(ora);
  const out = Array.from({ length: giorni }, (_, i) => ({ giorno: oggi - (giorni - 1 - i) * GIORNO, eventi: 0, completati: 0 }));
  for (const e of s.events) {
    const idx = Math.floor((inizioGiorno(Date.parse(e.timestamp)) - out[0].giorno) / GIORNO);
    if (idx >= 0 && idx < giorni) { out[idx].eventi++; if (e.event_type === 'task_completed') out[idx].completati++; }
  }
  return out;
}

/** Task aperti assegnati per agente. Fonte: tasks.assigned_agent_id. */
export function caricoPerAgente(s: Snapshot) {
  return s.agents.map((a) => ({ id: a.id, nome: a.nome,
    aperti: s.tasks.filter((t) => t.assigned_agent_id === a.id && !['completed', 'failed', 'cancelled'].includes(t.stato)).length,
    completati: s.tasks.filter((t) => t.assigned_agent_id === a.id && t.stato === 'completed').length }));
}
