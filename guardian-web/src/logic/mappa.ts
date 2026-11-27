// Ondata 8: mappa operativa. Persone → agenti → task attivi → stanze, solo con collegamenti reali dei dati.
import { TASK_TERMINALI, type Snapshot } from '../types';
import { stanzaDiTask } from './stanze';
import { statoAgente } from './status';

export type TipoNodo = 'persona' | 'agente' | 'task' | 'stanza';
export interface Nodo { id: string; tipo: TipoNodo; etichetta: string; sotto?: string; x: number; y: number; stato?: string; impulso?: boolean; rif: string }
export interface Arco { da: string; a: string; attivo?: boolean }
export interface Mappa { nodi: Nodo[]; archi: Arco[]; altezza: number; nascosti: number }

export const COLONNE: { tipo: TipoNodo; x: number; titolo: string }[] = [
  { tipo: 'persona', x: 90, titolo: 'Persone' }, { tipo: 'agente', x: 340, titolo: 'Agenti' },
  { tipo: 'task', x: 620, titolo: 'Task attivi' }, { tipo: 'stanza', x: 890, titolo: 'Stanze' },
];
const PASSO = 64, TESTA = 70, MAX_TASK = 10, IMPULSO_MS = 120_000;
const ORDINE_TASK: Record<string, number> = { running: 0, needs_approval: 1, blocked: 2, waiting: 3, failed: 4, ready: 5, planned: 6, backlog: 7 };

export function costruisciMappa(s: Snapshot, ora = Date.now()): Mappa {
  const recenti = new Set(s.events.filter((e) => ora - Date.parse(e.timestamp) < IMPULSO_MS).flatMap((e) => [e.agent_id, e.task_id && `t${e.task_id}`]).filter(Boolean) as string[]);
  const tutti = s.tasks.filter((t) => !TASK_TERMINALI.includes(t.stato))
    .sort((a, b) => (ORDINE_TASK[a.stato] ?? 9) - (ORDINE_TASK[b.stato] ?? 9) || Date.parse(b.updated_at ?? '') - Date.parse(a.updated_at ?? ''));
  const tasks = tutti.slice(0, MAX_TASK);
  const persone = s.users.filter((u) => u.stato !== 'disattivo');
  const colonne: Omit<Nodo, 'x' | 'y'>[][] = [
    persone.map((u) => ({ id: `u:${u.id}`, tipo: 'persona', etichetta: u.nome, sotto: u.agente ?? undefined, rif: u.id })),
    s.agents.map((a) => ({ id: `a:${a.id}`, tipo: 'agente', etichetta: a.nome || a.id, sotto: statoAgente(a, ora), stato: statoAgente(a, ora), impulso: recenti.has(a.id), rif: a.id })),
    tasks.map((t) => ({ id: `t:${t.id}`, tipo: 'task', etichetta: `#${t.id} ${t.titolo}`, sotto: t.stato, stato: t.stato, impulso: recenti.has(`t${t.id}`), rif: String(t.id) })),
    s.stanze.map((st) => ({ id: `s:${st.id}`, tipo: 'stanza', etichetta: st.nome, rif: st.id })),
  ];
  const nodi: Nodo[] = colonne.flatMap((c, ci) => c.map((n, i) => ({ ...n, x: COLONNE[ci].x, y: TESTA + i * PASSO }) as Nodo));
  const ids = new Set(nodi.map((n) => n.id));
  const archi: Arco[] = [];
  for (const a of s.agents) if (ids.has(`u:${a.user_id}`)) archi.push({ da: `u:${a.user_id}`, a: `a:${a.id}`, attivo: recenti.has(a.id) });
  for (const t of tasks) {
    if (t.assigned_agent_id && ids.has(`a:${t.assigned_agent_id}`)) archi.push({ da: `a:${t.assigned_agent_id}`, a: `t:${t.id}`, attivo: t.stato === 'running' });
    else if (t.responsabile && ids.has(`u:${t.responsabile}`)) archi.push({ da: `u:${t.responsabile}`, a: `t:${t.id}` });
    const st = stanzaDiTask(t, s);
    if (st && ids.has(`s:${st}`)) archi.push({ da: `t:${t.id}`, a: `s:${st}` });
  }
  const righe = Math.max(1, ...colonne.map((c) => c.length));
  return { nodi, archi, altezza: TESTA + righe * PASSO, nascosti: tutti.length - tasks.length };
}
