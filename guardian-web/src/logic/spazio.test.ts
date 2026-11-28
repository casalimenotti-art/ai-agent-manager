import { describe, expect, it } from 'vitest';
import type { Agent, Device } from '../types';
import { agentiSuDispositivo, alphaStella, macchinePerScena, puntoPercorso3D, statoAgenteVisuale, statoMacchinaVisuale } from './spazio';

const ORA = Date.parse('2026-11-28T10:00:00Z');
const device = (id: number, user_id: string, stato = 'online'): Device => ({
  id, user_id, nome: `PC ${id}`, stato, limit_reached: false, last_seen: new Date(ORA - 10_000).toISOString(),
});
const agent = (id: string, user_id: string, extra: Partial<Agent> = {}): Agent => ({
  id, user_id, nome: id, tipo: 'codex', capabilities: [], stato: 'idle', disponibile: true,
  last_heartbeat: new Date(ORA - 10_000).toISOString(), ...extra,
});

describe('logica della scena spaziale', () => {
  it('assegna prima tramite device_id e non duplica il fallback utente', () => {
    const pc = device(1, 'menotti');
    const diretta = agent('diretta', 'menotti', { device_id: 1 });
    const fallback = agent('fallback', 'menotti');
    expect(agentiSuDispositivo([pc], [diretta, fallback], pc).map((a) => a.id)).toEqual(['diretta', 'fallback']);
  });

  it('usa il fallback per utente solo quando possiede un solo PC', () => {
    const primo = device(1, 'menotti'); const secondo = device(2, 'menotti');
    const senzaPC = agent('codex', 'menotti');
    expect(agentiSuDispositivo([primo], [senzaPC], primo)).toEqual([senzaPC]);
    expect(agentiSuDispositivo([primo, secondo], [senzaPC], primo)).toEqual([]);
  });

  it('crea al massimo tre nodi e riempie gli slot mancanti senza inventare dispositivi', () => {
    const scena = macchinePerScena([device(1, 'a')], []);
    expect(scena).toHaveLength(3);
    expect(scena[0].id).toBe(1);
    expect(scena.slice(1).every((pc) => pc.id === null)).toBe(true);
    expect(macchinePerScena([device(1, 'a'), device(2, 'b'), device(3, 'c'), device(4, 'd')], [])).toHaveLength(3);
  });

  it('non dichiara collegato un PC con heartbeat offline', () => {
    const pc = device(1, 'menotti', 'offline');
    const agenteAttivo = agent('attivo', 'menotti', { stato: 'working', device_id: 1 });
    expect(statoMacchinaVisuale({ id: pc.id, nome: pc.nome, stato: pc.stato, agenti: [agenteAttivo] }, ORA)).toBe('Scollegato');
  });

  it('mappa gli stati reali degli agenti a forme visuali testuali', () => {
    expect(statoAgenteVisuale(agent('a', 'u', { stato: 'working' }), ORA)).toBe('working');
    expect(statoAgenteVisuale(agent('b', 'u', { stato: 'needs_approval' }), ORA)).toBe('approval');
    expect(statoAgenteVisuale(agent('c', 'u', { stato: 'error' }), ORA)).toBe('error');
    expect(statoAgenteVisuale(agent('d', 'u', { stato: 'idle' }), ORA)).toBe('idle');
    expect(statoAgenteVisuale(agent('e', 'u', { stato: 'working', last_heartbeat: null }), ORA)).toBe('idle');
  });

  it('distingue lavoro, errore e slot non collegato nel PC', () => {
    const pc = { id: 1, nome: 'PC', stato: 'online' };
    expect(statoMacchinaVisuale({ ...pc, agenti: [agent('a', 'u', { stato: 'working' })] }, ORA)).toBe('Al lavoro');
    expect(statoMacchinaVisuale({ ...pc, stato: 'errore', agenti: [] }, ORA)).toBe('Errore');
    expect(statoMacchinaVisuale({ ...pc, agenti: [] }, ORA)).toBe('Inattivo');
    expect(statoMacchinaVisuale({ id: null, nome: 'slot', stato: 'offline', agenti: [] }, ORA)).toBe('Registra un PC');
  });

  it('calcola la Bézier ai capi e al centro del percorso 3D', () => {
    const curva = { inizio: { x: 0, y: 0, z: 0 }, controllo: { x: 2, y: 2, z: 0 }, fine: { x: 4, y: 0, z: 2 } };
    expect(puntoPercorso3D(curva, 0)).toEqual(curva.inizio);
    expect(puntoPercorso3D(curva, 1)).toEqual(curva.fine);
    expect(puntoPercorso3D(curva, 0.5)).toEqual({ x: 2, y: 1, z: 0.5 });
    expect(puntoPercorso3D(curva, 2)).toEqual(curva.fine);
  });

  it('mantiene il twinkle deterministico entro ±15% della luminosità di base', () => {
    const bassa = alphaStella(0.4, 0, 4, 0);
    const alta = alphaStella(0.4, 0, 4, 1);
    expect(bassa).toBeCloseTo(0.34);
    expect(alta).toBeCloseTo(0.4);
    expect(alphaStella(0.4, 0, 4, 5)).toBeCloseTo(bassa);
    expect(bassa).toBeGreaterThanOrEqual(0.4 * 0.85);
    expect(alta).toBeLessThanOrEqual(0.4);
  });
});
