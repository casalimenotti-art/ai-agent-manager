// Le stanze dell'HQ: a quale stanza appartiene un task/agente/evento e il riepilogo di ogni stanza. Tutto dai dati.
import type { Agent, Snapshot, Stanza, Task } from '../types';
import { TASK_TERMINALI } from '../types';
import { statoAgente } from './status';

/** Stanza di un task: quella del suo progetto; se senza progetto, quella del suo responsabile; altrimenti nessuna. */
export function stanzaDiTask(t: Task, s: Snapshot): string | null {
  const p = t.project_id ? s.projects.find((x) => x.id === t.project_id) : undefined;
  if (p?.stanza_id) return p.stanza_id;
  return s.stanze.find((st) => st.responsabile && st.responsabile === t.responsabile)?.id ?? null;
}
export const agentiDiStanza = (st: Stanza, s: Snapshot): Agent[] => s.agents.filter((a) => a.user_id === st.responsabile);
export const taskDiStanza = (st: Stanza, s: Snapshot): Task[] => s.tasks.filter((t) => stanzaDiTask(t, s) === st.id);

export interface RiepilogoStanza { stanza: Stanza; agenti: Agent[]; attivi: number; fermi: number; inEsecuzione: number; approvazioni: number;
  completati: number; ultimoEvento?: Snapshot['events'][number]; alLavoro: number }

export function riepilogoStanza(st: Stanza, s: Snapshot, ora?: number): RiepilogoStanza {
  const ts = taskDiStanza(st, s); const ids = new Set(ts.map((t) => t.id)); const agenti = agentiDiStanza(st, s);
  const progetti = new Set(s.projects.filter((p) => p.stanza_id === st.id).map((p) => p.id));
  return {
    stanza: st, agenti,
    attivi: ts.filter((t) => !TASK_TERMINALI.includes(t.stato)).length,
    fermi: ts.filter((t) => ['blocked', 'failed'].includes(t.stato)).length,
    inEsecuzione: ts.filter((t) => t.stato === 'running').length,
    completati: ts.filter((t) => t.stato === 'completed').length,
    approvazioni: s.approvals.filter((a) => a.status === 'richiesta' && a.task_id && ids.has(a.task_id)).length,
    alLavoro: agenti.filter((a) => ['working', 'waiting', 'needs_approval'].includes(statoAgente(a, ora))).length,
    ultimoEvento: s.events.find((e) => (e.task_id && ids.has(e.task_id)) || (e.project_id && progetti.has(e.project_id)) ||
      (e.agent_id && agenti.some((a) => a.id === e.agent_id))),
  };
}

/** Colonne del kanban: il trascinamento imposta uno stato reale (i vincoli li controlla il database). */
export const COLONNE_KANBAN = [
  { id: 'coda', nome: 'Da fare', stati: ['backlog', 'planned', 'ready'], destinazione: 'ready' },
  { id: 'corso', nome: 'In corso', stati: ['running', 'waiting'], destinazione: 'running' },
  { id: 'fermi', nome: 'Fermi', stati: ['blocked', 'needs_approval', 'failed'], destinazione: 'blocked' },
  { id: 'chiusi', nome: 'Chiusi', stati: ['completed', 'cancelled'], destinazione: 'completed' },
] as const;

/** Palette alternativa (preferenza personale «Soft»): stessi ruoli, tinte più chiare. La palette «Accesa» viene dal DB. */
export const COLORI_SOFT: Record<string, string> = { sviluppo: '#6aabf1', vendite: '#f0a06b', amministrazione: '#b9acf4' };
