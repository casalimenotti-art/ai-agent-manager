// Specchio di guardian/core/models.py: stati calcolati dai segnali reali, mai dichiarati.
import type { Agent, AgentStato, Device } from '../types';
import { AGENT_STATI } from '../types';

export const ONLINE_SECONDI = 120; // PC: heartbeat più vecchio = offline
export const AGENTE_HEARTBEAT_SECONDI = 180; // agente: bridge silenzioso = unknown

export function etaSecondi(ts?: string | null, ora: number = Date.now()): number | null {
  if (!ts) return null;
  const t = Date.parse(ts);
  return Number.isNaN(t) ? null : (ora - t) / 1000;
}

export function statoDispositivo(d: Device, ora?: number): string {
  const eta = etaSecondi(d.last_seen, ora);
  if (eta === null || eta > ONLINE_SECONDI) return 'offline';
  if (d.limit_reached) return 'limite';
  if (d.error) return 'errore';
  return d.stato || 'online';
}

export function statoAgente(a: Agent, ora?: number): AgentStato {
  const eta = etaSecondi(a.last_heartbeat, ora);
  if (eta === null || eta > AGENTE_HEARTBEAT_SECONDI) return a.stato === 'offline' ? 'offline' : 'unknown';
  return (AGENT_STATI as readonly string[]).includes(a.stato) ? a.stato : 'unknown';
}

export const AGENTI_AL_LAVORO: AgentStato[] = ['working', 'waiting', 'needs_approval'];

export function fa(ts?: string | null, ora?: number): string {
  const s = etaSecondi(ts, ora);
  if (s === null) return 'mai';
  if (s < 90) return 'ora';
  if (s < 3600) return `${Math.floor(s / 60)} min fa`;
  if (s < 86400) return `${Math.floor(s / 3600)} h fa`;
  return new Date(ts as string).toLocaleDateString('it-IT', { day: '2-digit', month: 'short' });
}

/** Cervello online se il PC del titolare ha dato un battito nell'ultimo minuto. */
export function cervelloOnline(c: { ultimo_battito?: string | null } | null | undefined, ora?: number): boolean {
  const eta = etaSecondi(c?.ultimo_battito, ora);
  return eta !== null && eta < 60;
}
