import { describe, expect, it } from 'vitest';
import type { Snapshot } from '../types';
import { applicaCambio } from './live';
import { costruisciMappa } from './mappa';

const base = (): Snapshot => ({
  users: [{ id: 'menotti', nome: 'Menotti', stato: 'attivo' }, { id: 'amico1', nome: 'Niko', stato: 'attivo' }] as Snapshot['users'],
  devices: [], projects: [{ id: 1, nome: 'Siti', stanza_id: 'sviluppo' }] as Snapshot['projects'],
  agents: [{ id: 'menotti-claude', user_id: 'menotti', nome: 'Claude', stato: 'working', last_heartbeat: new Date().toISOString() }] as Snapshot['agents'],
  tasks: [{ id: 1, titolo: 'Sito', stato: 'running', priorita: 'alta', project_id: 1, assigned_agent_id: 'menotti-claude', files_changed: [], depends_on: [] },
    { id: 2, titolo: 'Fatto', stato: 'completed', priorita: 'bassa', files_changed: [], depends_on: [] }] as unknown as Snapshot['tasks'],
  events: [], approvals: [], notifications: [], handoffs: [],
  stanze: [{ id: 'sviluppo', nome: 'Sviluppo & Siti', colore: '#22d3ee', ordine: 1, attiva: true, responsabile: 'menotti' }], vendite: [], scadenze: [], costi: [], cervello: null,
});

describe('Realtime incrementale', () => {
  it('aggiorna, inserisce e cancella senza ricaricare', () => {
    let s = applicaCambio(base(), { tabella: 'tasks', tipo: 'UPDATE', nuovo: { id: 1, stato: 'completed' } }, 'menotti')!;
    expect(s.tasks.find((t) => t.id === 1)?.stato).toBe('completed');
    expect(s.tasks.find((t) => t.id === 1)?.titolo).toBe('Sito');
    s = applicaCambio(s, { tabella: 'activity_events', tipo: 'INSERT', nuovo: { id: 9, event_type: 'nota', message: 'ciao' } }, 'menotti')!;
    expect(s.events[0].id).toBe(9);
    s = applicaCambio(s, { tabella: 'tasks', tipo: 'DELETE', vecchio: { id: 2 } }, 'menotti')!;
    expect(s.tasks.map((t) => t.id)).toEqual([1]);
  });
  it('ignora le notifiche degli altri, toglie token_hash, chiede il ricaricamento per tabelle ignote', () => {
    const s = base();
    expect(applicaCambio(s, { tabella: 'notifications', tipo: 'INSERT', nuovo: { id: 1, user_id: 'amico1' } }, 'menotti')!.notifications).toHaveLength(0);
    const a = applicaCambio(s, { tabella: 'agents', tipo: 'UPDATE', nuovo: { id: 'menotti-claude', token_hash: 'x', stato: 'idle' } }, 'menotti')!;
    expect('token_hash' in a.agents[0]).toBe(false);
    expect(applicaCambio(s, { tabella: 'devices', tipo: 'UPDATE', nuovo: { id: 1 } }, 'menotti')).toBeNull();
    expect(applicaCambio(s, { tabella: 'guardian_cervello', tipo: 'UPDATE', nuovo: { modello: 'claude-code', ultimo_battito: 'x' } }, 'menotti')!.cervello?.modello).toBe('claude-code');
  });
});

describe('mappa operativa', () => {
  it('collega solo ciò che i dati collegano', () => {
    const m = costruisciMappa(base());
    expect(m.nodi.filter((n) => n.tipo === 'task').map((n) => n.rif)).toEqual(['1']); // il completato non c'è
    expect(m.archi).toContainEqual({ da: 'u:menotti', a: 'a:menotti-claude', attivo: false });
    expect(m.archi).toContainEqual({ da: 'a:menotti-claude', a: 't:1', attivo: true });
    expect(m.archi).toContainEqual({ da: 't:1', a: 's:sviluppo' });
    expect(m.archi.some((a) => a.da === 'u:amico1')).toBe(false); // Niko senza agenti: nessun arco inventato
  });
});

import { costoMese, giorniA, pipelinePerFase, scadenzeDaGuardare } from './amministrazione';
import { senzaDatiPersonali } from '../data/source';
import type { Costo, Scadenza, Vendita } from '../types';

describe('stanze Vendite e Amministrazione', () => {
  const oggi = new Date(2026, 10, 27);
  it('scadenze: scadute e vicine, in ordine', () => {
    const sc = [{ id: 1, titolo: 'A', data: '2026-12-20', stato: 'aperta' }, { id: 2, titolo: 'B', data: '2026-11-26', stato: 'aperta' },
      { id: 3, titolo: 'C', data: '2026-11-30', stato: 'fatta' }, { id: 4, titolo: 'D', data: '2026-12-01', stato: 'aperta' }] as Scadenza[];
    expect(scadenzeDaGuardare(sc, 7, oggi).map((s) => s.id)).toEqual([2, 4]);
    expect(giorniA('2026-11-26', oggi)).toBe(-1);
  });
  it('costo del mese: mensili + annuali/12 + una tantum del mese', () => {
    const c = [{ importo_eur: 100, ricorrenza: 'mensile', data: '2026-01-01', categoria: 'abbonamenti_ai' }, { importo_eur: 120, ricorrenza: 'annuale', data: '2026-03-01', categoria: 'hosting' },
      { importo_eur: 45, ricorrenza: 'una_tantum', data: '2026-11-03', categoria: 'marketing' }, { importo_eur: 999, ricorrenza: 'una_tantum', data: '2026-10-03', categoria: 'altro' }] as Costo[];
    expect(costoMese(c, oggi).totale).toBe(155);
  });
  it('pipeline per fase e tasso di vittoria', () => {
    const v = [{ fase: 'proposta', valore_eur: 1000 }, { fase: 'vinto', valore_eur: 500 }, { fase: 'perso' }, { fase: 'perso' }] as Vendita[];
    const p = pipelinePerFase(v);
    expect([p.aperte, p.valoreAperto, p.tassoVittoria]).toEqual([1, 1000, 33]);
  });
  it('rifiuta email e telefoni, accetta importi', () => {
    expect(() => senzaDatiPersonali('mario.rossi@gmail.com', 'azienda')).toThrow();
    expect(() => senzaDatiPersonali('chiamare 347 123 4567', 'passo')).toThrow();
    expect(senzaDatiPersonali('Preventivo 1.200.000 lire, fattura n. 12', 'x')).toContain('fattura');
  });
});
