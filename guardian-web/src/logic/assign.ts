// Specchio di guardian/planner/assign.py: capacità in comune, poi carico minore.
import type { Agent, Task } from '../types';
import { TASK_TERMINALI } from '../types';
import { statoAgente } from './status';

export function carico(agentId: string, tasks: Task[]): number {
  return tasks.filter((t) => t.assigned_agent_id === agentId && !TASK_TERMINALI.includes(t.stato)).length;
}

export function suggerisci(capacita: string[], agenti: Agent[], tasks: Task[], ora?: number): string | null {
  const richieste = new Set(capacita.map((c) => c.toLowerCase()));
  const candidati: [number, number, string][] = [];
  for (const a of agenti) {
    const s = statoAgente(a, ora);
    if (!a.disponibile || s === 'error' || s === 'offline') continue;
    const comuni = (a.capabilities || []).filter((c) => richieste.has(c.toLowerCase())).length;
    if (richieste.size && !comuni) continue;
    candidati.push([-comuni, carico(a.id, tasks), a.id]);
  }
  candidati.sort((x, y) => x[0] - y[0] || x[1] - y[1] || x[2].localeCompare(y[2]));
  return candidati[0]?.[2] ?? null;
}
