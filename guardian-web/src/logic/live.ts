// Ondata 8: i messaggi Realtime si applicano subito ai dati già caricati (niente attesa del ricaricamento completo).
// Funzione pura e testata; un cambio non riconosciuto restituisce null = serve il ricaricamento completo.
import type { Snapshot } from '../types';

export interface Cambio { tabella: string; tipo: 'INSERT' | 'UPDATE' | 'DELETE'; nuovo?: Record<string, unknown>; vecchio?: Record<string, unknown> }

const CHIAVI: Record<string, keyof Snapshot> = {
  tasks: 'tasks', agents: 'agents', approvals: 'approvals', notifications: 'notifications', activity_events: 'events',
  handoffs: 'handoffs', projects: 'projects', stanze: 'stanze', vendite_pipeline: 'vendite', scadenze: 'scadenze', costi: 'costi',
};
const LIMITI: Partial<Record<keyof Snapshot, number>> = { tasks: 500, events: 400, approvals: 200, notifications: 100, handoffs: 100 };
const NASCOSTI = ['token_hash']; // mai nel browser, anche se un messaggio lo portasse

export function applicaCambio(s: Snapshot, c: Cambio, userId: string): Snapshot | null {
  if (c.tabella === 'guardian_cervello') {
    if (c.tipo === 'DELETE') return { ...s, cervello: null };
    const n = c.nuovo ?? {};
    return { ...s, cervello: { modello: (n.modello as string) ?? null, ultimo_battito: (n.ultimo_battito as string) ?? null } };
  }
  const k = CHIAVI[c.tabella];
  if (!k) return null;
  const riga = c.nuovo ? Object.fromEntries(Object.entries(c.nuovo).filter(([x]) => !NASCOSTI.includes(x))) : undefined;
  if (k === 'notifications' && riga && riga.user_id !== userId) return s; // le notifiche degli altri non si mostrano
  let lista = [...(s[k] as unknown as { id: unknown }[])];
  const id = (riga?.id ?? c.vecchio?.id) as unknown;
  if (id === undefined) return null;
  const i = lista.findIndex((x) => x.id === id);
  if (c.tipo === 'DELETE' || (k === 'stanze' && riga && riga.attiva === false)) { if (i >= 0) lista.splice(i, 1); }
  else if (i >= 0) lista[i] = { ...lista[i], ...riga } as { id: unknown };
  else lista.unshift(riga as { id: unknown });
  if (k === 'stanze') lista = (lista as unknown as Snapshot['stanze']).sort((a, b) => a.ordine - b.ordine) as unknown as { id: unknown }[];
  const max = LIMITI[k]; if (max) lista = lista.slice(0, max);
  return { ...s, [k]: lista } as Snapshot;
}
