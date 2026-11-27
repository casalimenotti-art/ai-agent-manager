import { describe, expect, it } from 'vitest';
import type { Agent, Snapshot, Task } from '../types';
import { suggerisci } from './assign';
import { attivitaPerGiorno, completatiOggi, durataMediaOre, tassoCompletamento } from './metrics';
import { DOMANDE_ESEMPIO, rispondi } from './intents';
import { report } from './report';
import { statoAgente, statoDispositivo } from './status';

const ORA = Date.parse('2026-11-27T15:00:00Z');
const iso = (minFa: number) => new Date(ORA - minFa * 60_000).toISOString();
const agente = (p: Partial<Agent>): Agent => ({ id: 'a', user_id: 'menotti', nome: 'A', tipo: 'claude-code', capabilities: [],
  stato: 'working', disponibile: true, last_heartbeat: iso(1), ...p });
const task = (p: Partial<Task>): Task => ({ id: 1, titolo: 'T', priorita: 'media', stato: 'ready', files_changed: [], depends_on: [],
  created_at: iso(60), updated_at: iso(10), ...p });
const snap = (p: Partial<Snapshot>): Snapshot => ({ users: [], devices: [], agents: [], projects: [], tasks: [], events: [],
  approvals: [], notifications: [], handoffs: [], ...p });

describe('stati reali', () => {
  it('agente unknown se il bridge tace, PC offline se heartbeat vecchio', () => {
    expect(statoAgente(agente({}), ORA)).toBe('working');
    expect(statoAgente(agente({ last_heartbeat: iso(10) }), ORA)).toBe('unknown');
    expect(statoAgente(agente({ last_heartbeat: null, stato: 'offline' }), ORA)).toBe('offline');
    const d = { id: 1, user_id: 'm', nome: 'PC', stato: 'online', limit_reached: false };
    expect(statoDispositivo({ ...d, last_seen: iso(1) }, ORA)).toBe('online');
    expect(statoDispositivo({ ...d, last_seen: iso(5) }, ORA)).toBe('offline');
    expect(statoDispositivo({ ...d, last_seen: iso(1), limit_reached: true }, ORA)).toBe('limite');
  });
});

describe('assegnazione', () => {
  it('capacità poi carico; esclude errore e non disponibili', () => {
    const ag = [agente({ id: 'c', capabilities: ['testi'] }), agente({ id: 'x', capabilities: ['dati'] }),
      agente({ id: 'e', capabilities: ['testi'], stato: 'error' })];
    expect(suggerisci(['testi'], ag, [], ORA)).toBe('c');
    expect(suggerisci(['cucina'], ag, [], ORA)).toBeNull();
    expect(suggerisci([], ag, [task({ assigned_agent_id: 'c', stato: 'running' })], ORA)).toBe('x');
  });
});

describe('report e prossime azioni', () => {
  it('ordina per priorità e copre i casi', () => {
    const s = snap({
      agents: [agente({ id: 'a1', nome: 'Codex', stato: 'error', error: 'crash' }), agente({ id: 'a2', nome: 'Claude', usage: { five_hour: { pct: 95 } } })],
      tasks: [task({ id: 1, stato: 'blocked' }), task({ id: 2, stato: 'failed', error: 'timeout' }), task({ id: 3, stato: 'running', updated_at: iso(30 * 60) }),
        task({ id: 4, stato: 'ready' }), task({ id: 5, stato: 'completed' }), task({ id: 6, stato: 'planned', depends_on: [5] })],
      approvals: [{ id: 9, action: 'Pagare', status: 'richiesta', action_type: 'pagamento', created_at: iso(5) }],
    });
    const r = report(s, ORA);
    const testi = r.prossime.map((a) => a.testo);
    expect(testi[0]).toMatch(/^Decidi l'approvazione #9/);
    expect(testi.some((t) => t.includes('Controlla l\'agente Codex: crash'))).toBe(true);
    expect(testi.some((t) => t.includes('95%'))).toBe(true);
    expect(testi.some((t) => t.includes('fermo da 30 h'))).toBe(true);
    expect(testi.some((t) => t.includes('Assegna il task #4') && t.includes('suggerito: a2'))).toBe(true);
    expect(testi.some((t) => t.includes('#6') && t.includes('ready'))).toBe(true);
    expect(r.aperti).toBe(4); // failed e completed sono chiusi
  });
});

describe('metriche', () => {
  const ev = (id: number, tipo: string, minFa: number, task_id?: number) => ({ id, event_type: tipo, message: '', files: [],
    severity: 'info' as const, timestamp: iso(minFa), task_id });
  it('completati oggi, tasso, durata media, attività per giorno', () => {
    const s = snap({ events: [ev(1, 'task_started', 180, 1), ev(2, 'task_completed', 60, 1), ev(3, 'task_completed', 60 * 30, 2)],
      tasks: [task({ id: 1, stato: 'completed' }), task({ id: 2, stato: 'failed' }), task({ id: 3, stato: 'running' })] });
    expect(completatiOggi(s, ORA)).toBe(1);
    expect(tassoCompletamento(s, 7, ORA)).toBe(0.5);
    expect(durataMediaOre(s)).toBe(2);
    const g = attivitaPerGiorno(s, 3, ORA);
    expect(g).toHaveLength(3);
    expect(g[2].completati).toBe(1);
    expect(tassoCompletamento(snap({}), 7, ORA)).toBeNull();
    expect(durataMediaOre(snap({}))).toBeNull();
  });
});

describe('router di intenti senza AI', () => {
  it('risponde alle 6 domande d\'esempio con una fonte', () => {
    const s = snap({ agents: [agente({ nome: 'Claude' })], tasks: [task({ stato: 'blocked', titolo: 'Sito' })],
      approvals: [{ id: 1, action: 'Email', status: 'richiesta', action_type: 'email', created_at: iso(1) }] });
    for (const d of DOMANDE_ESEMPIO) {
      const r = rispondi(d, s, ORA);
      expect(r, d).not.toBeNull();
      expect(r!.fonte.length).toBeGreaterThan(3);
    }
    expect(rispondi('Quanti agenti sono attivi?', s, ORA)!.testo).toContain('1 agenti al lavoro');
    expect(rispondi('Cosa è bloccato?', s, ORA)!.testo).toContain('#1 Sito');
    expect(rispondi('Scrivimi una poesia', s, ORA)).toBeNull();
  });
});

describe('contesto del pannello', () => {
  it('spiega perché un task è bloccato e cosa fa un agente', async () => {
    const { rispondiConContesto } = await import('./intents');
    const s = snap({ agents: [agente({ id: 'c', nome: 'Claude', current_task_id: 2 })],
      tasks: [task({ id: 1, titolo: 'Dati', stato: 'running' }), task({ id: 2, titolo: 'Sito', stato: 'needs_approval', depends_on: [1] })],
      approvals: [{ id: 5, action: 'Inviare email', status: 'richiesta', action_type: 'email', task_id: 2, created_at: iso(1) }] });
    const r = rispondiConContesto('perché questo task è fermo?', s, { p: 'task', id: '2' }, ORA)!;
    expect(r.testo).toContain('dipende dal task #1');
    expect(r.testo).toContain("aspetta l'approvazione «Inviare email»");
    expect(rispondiConContesto('cosa sta facendo questo agente?', s, { p: 'agente', id: 'c' }, ORA)!.testo).toContain('task #2');
    expect(rispondiConContesto('quanti agenti sono attivi', s, null, ORA)!.testo).toContain('agenti al lavoro');
  });
});
