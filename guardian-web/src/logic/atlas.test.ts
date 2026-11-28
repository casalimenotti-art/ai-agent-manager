import { describe, expect, it } from 'vitest';
import type { Agent, Snapshot, Stanza, Task } from '../types';
import { COLORI_ATLAS, costruisciGrafo, coloreStanzaAtlas, devoDisegnare, disponi, faseImpulso, lampeggio, possoAnimare, puntoSulPercorso, respiro, riepilogoAtlas, statoAgenteAtlas, statoTaskAtlas, stileStato, zonaLibera } from './atlas';

const ORA = Date.parse('2026-11-28T10:00:00Z');
const fa = (s: number) => new Date(ORA - s * 1000).toISOString();
const stanze: Stanza[] = [
  { id: 'sviluppo', nome: 'Sviluppo & Siti', colore: '#338ced', responsabile: 'menotti', ordine: 1, attiva: true },
  { id: 'vendite', nome: 'Vendite', colore: '#e76624', responsabile: 'amico1', ordine: 2, attiva: true },
  { id: 'amministrazione', nome: 'Amministrazione', colore: '#9887ef', responsabile: 'amico2', ordine: 3, attiva: true },
];
const agente = (id: string, user_id: string, stato: Agent['stato'], hb = 10): Agent =>
  ({ id, user_id, nome: id, tipo: 'x', capabilities: [], stato, disponibile: true, last_heartbeat: fa(hb) });
const task = (id: number, stato: Task['stato'], extra: Partial<Task> = {}): Task =>
  ({ id, titolo: `Task ${id}`, priorita: 'media', stato, files_changed: [], created_at: fa(100), updated_at: fa(10), depends_on: [], ...extra });
const snap = (agents: Agent[] = [], tasks: Task[] = []): Snapshot => ({
  users: [], devices: [], agents, projects: [], tasks, events: [], approvals: [], notifications: [], handoffs: [], stanze,
  vendite: [], scadenze: [], costi: [], cervello: null,
});

describe('atlas: grafo', () => {
  it('senza agenti: solo nucleo e 3 stanze, con 3 link', () => {
    const g = costruisciGrafo(snap(), { ora: ORA });
    expect(g.nodi.map((n) => n.tipo)).toEqual(['nucleo', 'stanza', 'stanza', 'stanza']);
    expect(g.link).toHaveLength(3);
    expect(riepilogoAtlas(snap(), ORA)).toMatch(/Nessun agente collegato/);
  });
  it('conta nodi e link: nucleo > stanze > agenti > task', () => {
    const s = snap([agente('a1', 'menotti', 'working'), agente('a2', 'amico1', 'idle')],
      [task(1, 'running', { assigned_agent_id: 'a1' }), task(2, 'ready', { responsabile: 'amico1' }), task(3, 'completed')]);
    const g = costruisciGrafo(s, { ora: ORA });
    expect(g.nodi).toHaveLength(1 + 3 + 2 + 2); // il task completato non c'è
    expect(g.link).toHaveLength(3 + 2 + 2);
    expect(g.link.find((l) => l.a === 't:1')?.da).toBe('a:a1');
    expect(g.link.find((l) => l.a === 't:2')?.da).toBe('s:vendite'); // senza agente: attaccato alla stanza del responsabile
    expect(g.link.find((l) => l.a === 'a:a2')?.da).toBe('s:vendite');
    expect(riepilogoAtlas(s, ORA)).toBe('1 agente al lavoro: a1 su 2.');
  });
  it('sul telefono restano solo nucleo, stanze e agenti', () => {
    const s = snap([agente('a1', 'menotti', 'working')], [task(1, 'running', { assigned_agent_id: 'a1' })]);
    const g = costruisciGrafo(s, { ora: ORA, telefono: true });
    expect(g.nodi.some((n) => n.tipo === 'task' || n.tipo === 'evento')).toBe(false);
    expect(g.nodi).toHaveLength(5);
  });
});

describe('atlas: colori e stati', () => {
  it('colori per stanza', () => {
    expect(coloreStanzaAtlas(stanze[0])).toBe(COLORI_ATLAS.sviluppo);
    expect(coloreStanzaAtlas(stanze[1])).toBe(COLORI_ATLAS.vendite);
    expect(coloreStanzaAtlas(stanze[2])).toBe(COLORI_ATLAS.amministrazione);
    const g = costruisciGrafo(snap(), { ora: ORA });
    expect(g.nodi.filter((n) => n.tipo === 'stanza').map((n) => n.colore)).toEqual([COLORI_ATLAS.sviluppo, COLORI_ATLAS.vendite, COLORI_ATLAS.amministrazione]);
  });
  it('stato agente e task', () => {
    expect(statoAgenteAtlas(agente('x', 'u', 'working'), ORA)).toBe('attivo');
    expect(statoAgenteAtlas(agente('x', 'u', 'idle'), ORA)).toBe('fermo');
    expect(statoAgenteAtlas(agente('x', 'u', 'error'), ORA)).toBe('bloccato');
    expect(statoAgenteAtlas(agente('x', 'u', 'needs_approval'), ORA)).toBe('ok');
    expect(statoAgenteAtlas(agente('x', 'u', 'working', 9999), ORA)).toBe('fermo'); // bridge silenzioso = unknown
    expect(statoTaskAtlas({ stato: 'running' })).toBe('attivo');
    expect(statoTaskAtlas({ stato: 'failed' })).toBe('bloccato');
    expect(statoTaskAtlas({ stato: 'needs_approval' })).toBe('ok');
    expect(statoTaskAtlas({ stato: 'ready' })).toBe('fermo');
  });
  it('stato > stile', () => {
    expect(stileStato('attivo', '#123456')).toMatchObject({ colore: '#123456', alpha: 1, fiore: true });
    expect(stileStato('fermo', '#123456')).toMatchObject({ colore: COLORI_ATLAS.fermo, fiore: false });
    expect(stileStato('fermo', '#123456').alpha).toBeLessThan(0.6);
    expect(stileStato('bloccato', '#123456')).toMatchObject({ colore: COLORI_ATLAS.bloccato, anello: true, lampeggia: true });
    expect(stileStato('ok', '#123456')).toMatchObject({ colore: COLORI_ATLAS.ok, anello: true });
  });
});

describe('atlas: layout', () => {
  const s = snap([agente('a1', 'menotti', 'working'), agente('a2', 'amico1', 'idle'), agente('a3', 'amico2', 'error')],
    [task(1, 'running', { assigned_agent_id: 'a1' }), task(2, 'blocked', { assigned_agent_id: 'a3' }), task(3, 'ready', { responsabile: 'amico1' })]);
  it('è deterministico con lo stesso seed e cambia con un altro', () => {
    const g = costruisciGrafo(s, { ora: ORA });
    const a = disponi(g, { seed: 3 }); const b = disponi(g, { seed: 3 }); const c = disponi(g, { seed: 4 });
    expect(a.nodi.map((n) => [n.x, n.y])).toEqual(b.nodi.map((n) => [n.x, n.y]));
    expect(a.nodi.map((n) => [n.x, n.y])).not.toEqual(c.nodi.map((n) => [n.x, n.y]));
  });
  it('nucleo al centro, stanze attorno, tutto dentro il quadrato, nessun NaN', () => {
    const l = disponi(costruisciGrafo(s, { ora: ORA }));
    expect(l.nodi[0]).toMatchObject({ id: 'nucleo', x: 0, y: 0 });
    for (const n of l.nodi) { expect(Number.isFinite(n.x + n.y)).toBe(true); expect(Math.abs(n.x)).toBeLessThanOrEqual(1); expect(Math.abs(n.y)).toBeLessThanOrEqual(1); }
    for (const st of l.nodi.filter((n) => n.tipo === 'stanza')) expect(Math.hypot(st.x, st.y)).toBeCloseTo(0.6, 5);
  });
  it('un agente sta più vicino alla sua stanza che alle altre', () => {
    const l = disponi(costruisciGrafo(s, { ora: ORA })); const per = (id: string) => l.nodi.find((n) => n.id === id)!;
    const d = (a: string, b: string) => Math.hypot(per(a).x - per(b).x, per(a).y - per(b).y);
    expect(d('a:a1', 's:sviluppo')).toBeLessThan(d('a:a1', 's:vendite'));
    expect(d('a:a1', 's:sviluppo')).toBeLessThan(d('a:a1', 's:amministrazione'));
  });
});

describe('atlas: vita (ondata 2)', () => {
  it('limite di fps: 30 fps = almeno ~33 ms tra due disegni', () => {
    expect(devoDisegnare(null, 0)).toBe(true);
    expect(devoDisegnare(1000, 1016)).toBe(false); // 60 Hz: salta un frame
    expect(devoDisegnare(1000, 1033.4)).toBe(true);
    expect(devoDisegnare(1000, 1020, 60)).toBe(true);
    // simulazione a 60 Hz per 1 s: al massimo 30 disegni
    let ultimo: number | null = null; let n = 0;
    for (let t = 0; t < 1000; t += 1000 / 60) if (devoDisegnare(ultimo, t)) { ultimo = t; n++; }
    expect(n).toBeLessThanOrEqual(31); expect(n).toBeGreaterThanOrEqual(28);
  });
  it('anima solo se visibile e senza reduced-motion', () => {
    expect(possoAnimare(false, false)).toBe(true);
    expect(possoAnimare(true, false)).toBe(false);
    expect(possoAnimare(false, true)).toBe(false);
  });
  it('impulso lungo la spezzata e fase ciclica', () => {
    const pts = [[0, 0], [10, 0], [10, 10]] as const;
    expect(puntoSulPercorso(pts, 0)).toEqual([0, 0]);
    expect(puntoSulPercorso(pts, 0.5)).toEqual([10, 0]);
    expect(puntoSulPercorso(pts, 1)).toEqual([10, 10]);
    const f = faseImpulso(123456, 3); expect(f).toBeGreaterThanOrEqual(0); expect(f).toBeLessThan(1);
  });
  it('respiro più ampio quando il cervello risponde; lampeggio in 0..1', () => {
    expect(respiro(0, true).ampiezza).toBeGreaterThan(respiro(0, false).ampiezza);
    for (const t of [0, 300, 999, 5000]) { const l = lampeggio(t); expect(l).toBeGreaterThanOrEqual(0); expect(l).toBeLessThanOrEqual(1); }
  });
  it('stati: attivo con etichetta attività, bloccato, serve OK (stato o approvazione)', () => {
    const s = snap([agente('a1', 'menotti', 'working'), agente('a2', 'amico1', 'error'), agente('a3', 'amico2', 'idle')],
      [task(1, 'running', { titolo: 'Rifare la pagina prezzi con il nuovo listino e le foto', assigned_agent_id: 'a1' })]);
    s.agents[0].current_task_id = 1;
    s.approvals = [{ id: 1, action: 'x', status: 'richiesta', created_at: fa(5), action_type: 'email', agent_id: 'a3' }];
    const g = costruisciGrafo(s, { ora: ORA }); const per = (id: string) => g.nodi.find((n) => n.id === `a:${id}`)!;
    expect(per('a1').stato).toBe('attivo'); expect(per('a1').attivita!.length).toBeLessThanOrEqual(40); expect(per('a1').attivita).toMatch(/…$/);
    expect(per('a2').stato).toBe('bloccato'); expect(per('a2').attivita).toBeUndefined();
    expect(per('a3').okInAttesa).toBe(true); expect(per('a1').okInAttesa).toBe(false);
  });
  it("attività: senza task usa l'ultimo evento", () => {
    const s = snap([agente('a1', 'menotti', 'working')]);
    s.events = [{ id: 1, event_type: 'x', message: 'vecchio', files: [], severity: 'info', timestamp: fa(500), agent_id: 'a1' },
      { id: 2, event_type: 'x', message: 'ultimo evento', files: [], severity: 'info', timestamp: fa(20), agent_id: 'a1' }];
    expect(costruisciGrafo(s, { ora: ORA }).nodi.find((n) => n.id === 'a:a1')!.attivita).toBe('ultimo evento');
  });
  it('zona libera: sceglie il rettangolo più grande fuori dal pannello', () => {
    const area = { x: 72, y: 64, w: 1368, h: 700 };
    const z = zonaLibera(area, { x: 96, y: 193, w: 440, h: 456 });
    expect(z.x).toBe(536); expect(z.x + z.w).toBe(1440);
    const t = zonaLibera({ x: 0, y: 64, w: 390, h: 700 }, { x: 12, y: 400, w: 366, h: 340 });
    expect(t.y).toBe(64); expect(t.y + t.h).toBeLessThanOrEqual(400);
    expect(zonaLibera(area, null)).toBe(area);
  });
});

// ---------- ondata 3 ----------
import { DURATA_ZOOM_MS, FILTRO_TUTTI, easeOut, filtraGrafo, interpolaVista, nodoInPunto, nodoVisibile, schedaNodo, VISTA_COMPLETA, vistaStanza } from './atlas';
describe('atlas ondata 3', () => {
  const s = snap([agente('a1', 'menotti', 'working'), agente('a2', 'amico1', 'idle')], [task(1, 'running', { assigned_agent_id: 'a1' }), task(2, 'ready')]);
  const g = disponi(costruisciGrafo(s, { ora: ORA }));
  const P = (n: { x: number; y: number }) => [400 + n.x * 300, 300 + n.y * 250] as const;

  it('hit-test: punto sul nodo lo trova, lontano no, gli esclusi non rispondono', () => {
    const a1 = g.nodi.find((n) => n.id === 'a:a1')!; const [x, y] = P(a1);
    expect(nodoInPunto(g, P, x + 2, y + 1)?.id).toBe('a:a1');
    expect(nodoInPunto(g, P, 5, 5)).toBeNull();
    const f = filtraGrafo(g, { stanza: 'vendite', soloAttivi: false });
    expect(nodoInPunto(f, P, x, y)).toBeNull();
  });
  it('filtro: stanza e solo attivi, alpha 0.1 per gli esclusi, input intatto', () => {
    const f = filtraGrafo(g, { stanza: 'sviluppo', soloAttivi: false });
    expect(f.nodi.find((n) => n.id === 'a:a1')!.escluso).toBeUndefined();
    expect(f.nodi.find((n) => n.id === 'a:a2')!.alpha).toBe(0.1);
    expect(f.nodi.find((n) => n.id === 'nucleo')!.escluso).toBeUndefined();
    expect(g.nodi.find((n) => n.id === 'a:a2')!.alpha).not.toBe(0.1);
    expect(filtraGrafo(g, FILTRO_TUTTI)).toBe(g);
    expect(nodoVisibile({ tipo: 'task', stanza: null, stato: 'fermo' }, { stanza: 'tutti', soloAttivi: true })).toBe(false);
    expect(nodoVisibile({ tipo: 'stanza', stanza: 'vendite', stato: 'attivo' }, { stanza: 'tutti', soloAttivi: true })).toBe(true);
  });
  it('riepilogo segue il filtro', () => {
    expect(riepilogoAtlas(s, ORA)).toContain('1 agente al lavoro: a1 su 2');
    expect(riepilogoAtlas(s, ORA, { stanza: 'vendite', soloAttivi: false })).toBe('Filtro: Vendite. Nessun agente al lavoro su 1.');
  });
  it('zoom: vista della stanza, ease-out e reduced-motion', () => {
    const v = vistaStanza(g, 'sviluppo');
    expect(v.z).toBeGreaterThanOrEqual(1); expect(v.z).toBeLessThanOrEqual(3);
    expect(vistaStanza(g, 'inesistente')).toEqual(VISTA_COMPLETA);
    expect(DURATA_ZOOM_MS).toBe(400);
    expect(easeOut(0)).toBe(0); expect(easeOut(1)).toBe(1); expect(easeOut(0.5)).toBeGreaterThan(0.5);
    expect(interpolaVista(VISTA_COMPLETA, v, 0)).toEqual(VISTA_COMPLETA);
    expect(interpolaVista(VISTA_COMPLETA, v, 1)).toEqual(v);
    expect(interpolaVista(VISTA_COMPLETA, v, 0.1, true)).toEqual(v);
  });
  it('scheda del nodo: agente, task e stanza', () => {
    const a = schedaNodo(s, g.nodi.find((n) => n.id === 'a:a1')!);
    expect(a.apre).toEqual({ p: 'agente', id: 'a1' }); expect(a.righe.map((r) => r.k)).toEqual(['Agente', 'PC', 'Stato', 'Task', 'Ultimo evento']);
    expect(schedaNodo(s, g.nodi.find((n) => n.id === 't:1')!).apre).toEqual({ p: 'task', id: '1' });
    expect(schedaNodo(s, g.nodi.find((n) => n.id === 's:vendite')!).apre).toEqual({ zoom: 'vendite' });
  });
});
