// Stato del nucleo di Guardian e testo di stato: sempre derivati da segnali reali (mai frasi fisse).
import type { Snapshot } from '../types';
import { statoAgente } from './status';

export type StatoNucleo = 'offline' | 'error' | 'listening' | 'thinking' | 'approval' | 'working' | 'idle';

export function statoNucleo(s: Snapshot | null, o: { pingOk: boolean | null; ascolta: boolean; pensa: boolean }, ora?: number): StatoNucleo {
  if (o.pingOk === false) return 'error';
  if (!s) return 'offline';
  if (o.ascolta) return 'listening';
  if (o.pensa) return 'thinking';
  if (s.approvals.some((a) => a.status === 'richiesta')) return 'approval';
  if (s.agents.some((a) => statoAgente(a, ora) === 'working')) return 'working';
  return 'idle';
}

export function testoStato(s: Snapshot | null, o: { pingOk: boolean | null; ascolta: boolean; pensa: boolean }, ora?: number): string {
  if (o.pingOk === false) return 'Database non raggiungibile: i dati mostrati potrebbero non essere aggiornati.';
  if (!s) return 'Collegamento ai dati in corso…';
  if (o.ascolta) return 'Ti ascolto.';
  if (o.pensa) return 'Sto elaborando la richiesta…';
  const lav = s.agents.filter((a) => statoAgente(a, ora) === 'working').length;
  const att = s.approvals.filter((a) => a.status === 'richiesta').length;
  const err = s.agents.filter((a) => statoAgente(a, ora) === 'error').length;
  const parti: string[] = [];
  if (lav) parti.push(`Coordino ${lav} ${lav === 1 ? 'agente al lavoro' : 'agenti al lavoro'}`);
  if (att) parti.push(`${att} ${att === 1 ? 'approvazione' : 'approvazioni'} in attesa`);
  if (err) parti.push(`${err} ${err === 1 ? 'agente' : 'agenti'} in errore`);
  if (!parti.length) return s.agents.length ? 'Nessun agente al lavoro in questo momento. Sistemi monitorati.' : 'Nessun agente collegato: avvia il Guardian Bridge sui PC.';
  return `${parti.join(' · ')}.`;
}
