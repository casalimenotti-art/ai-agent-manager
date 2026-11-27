// Eventi della timeline generati dalle modifiche ai task: stessi tipi di guardian/core/store_supabase.py.
import type { Severita, Task } from '../types';

export interface EventoNuovo { event_type: string; message: string; severity: Severita; task_id: number;
  project_id?: number | null; agent_id?: string | null; user_id: string; files?: string[] }

export function eventiModificaTask(prima: Task, dopo: Task, by: string): EventoNuovo[] {
  const base = { task_id: dopo.id, project_id: dopo.project_id ?? null, agent_id: dopo.assigned_agent_id ?? null, user_id: by };
  const out: EventoNuovo[] = [];
  if (dopo.assigned_agent_id && dopo.assigned_agent_id !== prima.assigned_agent_id)
    out.push({ ...base, event_type: 'task_assigned', message: `Task #${dopo.id} assegnato a ${dopo.assigned_agent_id}`, severity: 'info' });
  if (dopo.stato !== prima.stato) {
    const tipo = ({ running: 'task_started', completed: 'task_completed', failed: 'task_failed' } as Record<string, string>)[dopo.stato] ?? 'task_updated';
    out.push({ ...base, event_type: tipo, message: `Task #${dopo.id} ${prima.stato} → ${dopo.stato}`, severity: dopo.stato === 'failed' ? 'error' : 'info',
      files: dopo.files_changed });
  } else if (['priorita', 'responsabile', 'next_step', 'result', 'error'].some((k) => (dopo as never)[k] !== (prima as never)[k]) ||
             JSON.stringify(dopo.depends_on) !== JSON.stringify(prima.depends_on)) {
    out.push({ ...base, event_type: 'task_updated', message: `Task #${dopo.id} aggiornato`, severity: 'info' });
  }
  return out;
}
