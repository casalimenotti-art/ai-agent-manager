// Specchio di guardian/planner/report.py: prossime azioni deterministiche dai dati (nessun modello AI).
import type { Snapshot, TaskStato } from '../types';
import { TASK_STATI, TASK_TERMINALI } from '../types';
import { suggerisci } from './assign';
import { giorniA, scadenzeDaGuardare } from './amministrazione';
import { etaSecondi, statoAgente } from './status';

export const FERMO_ORE = 24;
export const USO_ALTO = 90;

export interface Azione { priorita: 1 | 2 | 3; testo: string; ref: { tipo: 'task' | 'agent' | 'approval' | 'stanza'; id: string | number } }
export interface Report { conteggi: Record<TaskStato, number>; aperti: number; approvazioni: number; prossime: Azione[] }

export function report(s: Snapshot, ora?: number): Report {
  const az: Azione[] = [];
  const perId = new Map(s.tasks.map((t) => [t.id, t]));
  const attese = s.approvals.filter((a) => a.status === 'richiesta');
  for (const a of attese) az.push({ priorita: 1, testo: `Decidi l'approvazione #${a.id}: ${a.action}`, ref: { tipo: 'approval', id: a.id } });
  for (const a of s.agents) {
    const st = statoAgente(a, ora);
    if (st === 'error') az.push({ priorita: 1, testo: `Controlla l'agente ${a.nome}: ${a.error || 'in errore'}`, ref: { tipo: 'agent', id: a.id } });
    else if (st === 'needs_approval') az.push({ priorita: 1, testo: `${a.nome} aspetta un permesso sul PC di ${a.user_id}`, ref: { tipo: 'agent', id: a.id } });
    const uso = Math.max(0, ...Object.values(a.usage || {}).map((w) => (w && typeof w.pct === 'number' ? w.pct : 0)));
    if (uso >= USO_ALTO) az.push({ priorita: 2, testo: `${a.nome} è al ${Math.round(uso)}% di utilizzo: salva un handoff prima del limite`, ref: { tipo: 'agent', id: a.id } });
  }
  for (const t of s.tasks) {
    const ref = { tipo: 'task' as const, id: t.id };
    if (t.stato === 'failed') az.push({ priorita: 2, testo: `Analizza il task fallito #${t.id} ${t.titolo}${t.error ? `: ${t.error}` : ''}`, ref });
    else if (t.stato === 'blocked') az.push({ priorita: 2, testo: `Sblocca il task #${t.id} ${t.titolo}`, ref });
    else if (t.stato === 'running' && (etaSecondi(t.updated_at, ora) ?? 0) > FERMO_ORE * 3600) {
      const ore = Math.floor((etaSecondi(t.updated_at, ora) ?? 0) / 3600);
      az.push({ priorita: 2, testo: `Task #${t.id} in esecuzione ma fermo da ${ore} h: chiedi un checkpoint`, ref });
    } else if (t.stato === 'ready' && !t.assigned_agent_id) {
      const sug = suggerisci([], s.agents, s.tasks, ora);
      az.push({ priorita: 3, testo: `Assegna il task #${t.id} ${t.titolo}${sug ? ` (suggerito: ${sug})` : ' (nessun agente disponibile)'}`, ref });
    } else if (t.stato === 'planned' && t.depends_on.length && t.depends_on.every((d) => perId.get(d)?.stato === 'completed')) {
      az.push({ priorita: 3, testo: `Le dipendenze del task #${t.id} sono completate: portalo a ready`, ref });
    }
  }
  // Solo web (migrazione 008): scadenze scadute o entro 7 giorni.
  for (const sc of scadenzeDaGuardare(s.scadenze ?? [], 7, ora ? new Date(ora) : undefined)) {
    const g = giorniA(sc.data, ora ? new Date(ora) : undefined);
    az.push({ priorita: g < 0 ? 1 : 2, testo: g < 0 ? `Scadenza passata da ${-g} g: ${sc.titolo}` : `Scadenza ${g === 0 ? 'oggi' : `tra ${g} g`}: ${sc.titolo}`,
      ref: { tipo: 'stanza', id: 'amministrazione' } });
  }
  const conteggi = Object.fromEntries(TASK_STATI.map((st) => [st, s.tasks.filter((t) => t.stato === st).length])) as Record<TaskStato, number>;
  return {
    conteggi, aperti: s.tasks.filter((t) => !TASK_TERMINALI.includes(t.stato)).length, approvazioni: attese.length,
    prossime: az.sort((a, b) => a.priorita - b.priorita),
  };
}
