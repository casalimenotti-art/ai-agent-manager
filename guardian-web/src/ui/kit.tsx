// Componenti di base del design system.
import { AlertTriangle, CheckCircle2, CircleDashed, CircleHelp, Loader2, PauseCircle, PlayCircle, ShieldAlert, WifiOff, XCircle,
  type LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';
import type { AgentStato, Severita, TaskStato } from '../types';

export const ETICHETTE_TASK: Record<TaskStato, string> = { backlog: 'Da fare', planned: 'Pianificato', ready: 'Pronto', running: 'In esecuzione',
  waiting: 'In attesa', blocked: 'Bloccato', needs_approval: 'Da approvare', completed: 'Completato', failed: 'Fallito', cancelled: 'Annullato' };
export const ETICHETTE_AGENTE: Record<AgentStato, string> = { online: 'Online', offline: 'Offline', idle: 'Inattivo', working: 'Al lavoro',
  waiting: 'In attesa', needs_approval: 'Chiede permesso', error: 'Errore', unknown: 'Sconosciuto' };

const STILE_TASK: Record<TaskStato, [string, LucideIcon]> = {
  backlog: ['', CircleDashed], planned: ['', CircleDashed], ready: ['accent', PlayCircle], running: ['accent', Loader2], waiting: ['warn', PauseCircle],
  blocked: ['serious', AlertTriangle], needs_approval: ['warn', ShieldAlert], completed: ['ok', CheckCircle2], failed: ['crit', XCircle], cancelled: ['', XCircle] };
const STILE_AGENTE: Record<AgentStato, [string, LucideIcon]> = {
  online: ['ok', CheckCircle2], idle: ['ok', CheckCircle2], working: ['accent', Loader2], waiting: ['warn', PauseCircle],
  needs_approval: ['warn', ShieldAlert], error: ['crit', XCircle], offline: ['', WifiOff], unknown: ['', CircleHelp] };

export function StatoTask({ s }: { s: TaskStato }) {
  const [c, I] = STILE_TASK[s]; return <span className={`pill ${c}`}><I aria-hidden />{ETICHETTE_TASK[s]}</span>;
}
export function StatoAgente({ s }: { s: AgentStato }) {
  const [c, I] = STILE_AGENTE[s]; return <span className={`pill ${c}`}><I aria-hidden />{ETICHETTE_AGENTE[s]}</span>;
}
export function Gravita({ s }: { s: Severita }) {
  if (s === 'info') return null;
  const c = s === 'warning' ? 'warn' : 'crit';
  return <span className={`pill ${c}`}><AlertTriangle aria-hidden />{s === 'warning' ? 'attenzione' : s === 'error' ? 'errore' : 'critico'}</span>;
}
export function Vuoto({ icona: I = CircleDashed, children }: { icona?: LucideIcon; children: ReactNode }) {
  return <div className="empty" role="status"><I size={22} aria-hidden /><div>{children}</div></div>;
}
export function Scheletro({ righe = 3 }: { righe?: number }) {
  return <div className="stack" aria-busy="true" aria-label="Caricamento">{Array.from({ length: righe }, (_, i) => <div key={i} className="skeleton" style={{ width: `${90 - i * 12}%` }} />)}</div>;
}
export function Sezione({ titolo, icona: I, conta, azione, children, className = '' }:
  { titolo: string; icona?: LucideIcon; conta?: number; azione?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`} aria-label={titolo}>
      <h3 className="section-title">{I && <I size={15} aria-hidden />}{titolo}{conta !== undefined && <span className="count">{conta}</span>}<span className="grow" />{azione}</h3>
      {children}
    </section>
  );
}
