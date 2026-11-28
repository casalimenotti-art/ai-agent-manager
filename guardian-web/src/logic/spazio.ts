import { statoAgente, statoDispositivo } from './status';
import type { Agent, Device } from '../types';

export interface MacchinaScena { id: number | null; nome: string; stato: string; agenti: Agent[] }
export interface PuntoSpazio { x: number; y: number; z: number }
export interface PercorsoSpazio { inizio: PuntoSpazio; controllo: PuntoSpazio; fine: PuntoSpazio }
export type StatoAgenteVisuale = 'working' | 'approval' | 'error' | 'idle';

export function statoAgenteVisuale(agent: Agent, ora?: number): StatoAgenteVisuale {
  const stato = statoAgente(agent, ora);
  if (stato === 'working') return 'working';
  if (stato === 'waiting' || stato === 'needs_approval') return 'approval';
  if (stato === 'error') return 'error';
  return 'idle';
}

/** Assegna prima col device_id; ripiega sull'utente solo quando possiede un solo PC registrato. */
export function agentiSuDispositivo(dispositivi: Device[], agenti: Agent[], device: Device): Agent[] {
  const espliciti = agenti.filter((agent) => agent.device_id === device.id);
  if (dispositivi.filter((d) => d.user_id === device.user_id).length !== 1) return espliciti;
  const perUtente = agenti.filter((agent) => !agent.device_id && agent.user_id === device.user_id);
  return [...espliciti, ...perUtente];
}

export function macchinePerScena(dispositivi: Device[], agenti: Agent[]): MacchinaScena[] {
  const elenco: MacchinaScena[] = dispositivi.slice(0, 3).map((device) => ({
    id: device.id, nome: device.nome, stato: statoDispositivo(device), agenti: agentiSuDispositivo(dispositivi, agenti, device),
  }));
  while (elenco.length < 3) elenco.push({ id: null, nome: 'PC non collegato', stato: 'offline', agenti: [] });
  return elenco;
}

/** Etichetta leggibile; un heartbeat scaduto prevale sullo stato di un agente. */
export function statoMacchinaVisuale(macchina: MacchinaScena, ora?: number): string {
  if (macchina.id === null) return 'Registra un PC';
  if (macchina.stato === 'error' || macchina.stato === 'errore' || macchina.stato === 'limite') return 'Errore';
  if (macchina.stato === 'offline') return 'Scollegato';
  if (['connecting', 'in_collegamento'].includes(macchina.stato)) return 'In collegamento';
  if (macchina.agenti.some((agent) => statoAgenteVisuale(agent, ora) === 'working')) return 'Al lavoro';
  if (macchina.stato === 'online') return 'Inattivo';
  return 'Scollegato';
}

/** Punto su una Bézier quadratica 3D; t è limitato all'intervallo del percorso. */
export function puntoPercorso3D(percorso: PercorsoSpazio, t: number): PuntoSpazio {
  const u = Math.max(0, Math.min(1, t)); const v = 1 - u;
  return {
    x: v * v * percorso.inizio.x + 2 * v * u * percorso.controllo.x + u * u * percorso.fine.x,
    y: v * v * percorso.inizio.y + 2 * v * u * percorso.controllo.y + u * u * percorso.fine.y,
    z: v * v * percorso.inizio.z + 2 * v * u * percorso.controllo.z + u * u * percorso.fine.z,
  };
}

/** Twinkle discreto con fase e periodo stabili per ciascuna stella. */
export function alphaStella(base: number, fase: number, periodo: number, secondi: number): number {
  return base * (1 + 0.15 * Math.sin(2 * Math.PI * secondi / periodo + fase));
}
