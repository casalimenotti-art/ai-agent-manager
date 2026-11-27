import type { AgentLog, Approval, Memory, Priorita, Snapshot, Task, TaskStato, User } from '../types';

export type Diretta = 'live' | 'polling' | 'off';

export interface NuovoTask {
  titolo: string; descrizione?: string; priorita: Priorita; stato: TaskStato; project_id?: number | null;
  responsabile?: string | null; assigned_agent_id?: string | null; depends_on?: number[];
  expected_result?: string; completion_criteria?: string; next_step?: string;
}
export type ModificaTask = Partial<Pick<Task, 'stato' | 'priorita' | 'assigned_agent_id' | 'responsabile' | 'next_step' |
  'project_id' | 'result' | 'error' | 'depends_on'>>;

/** Unica porta d'accesso ai dati per la UI. SupabaseSource in produzione; DemoSource solo in locale (VITE_DEMO=1). */
export interface DataSource {
  readonly modo: 'supabase' | 'demo';
  utente(): Promise<User | null>;
  accedi(email: string, password: string): Promise<User>;
  esci(): Promise<void>;
  carica(userId: string): Promise<Snapshot>;
  ping(): Promise<number>;
  /** Avvisa quando cambiano i dati. Restituisce la funzione per annullare. */
  ascolta(onCambio: () => void, onDiretta: (d: Diretta) => void): () => void;
  creaTask(t: NuovoTask, by: string): Promise<Task>;
  modificaTask(id: number, campi: ModificaTask, by: string): Promise<Task>;
  decidiApprovazione(id: number, stato: 'approvata' | 'rifiutata', by: string): Promise<void>;
  richiediApprovazione(a: Pick<Approval, 'action' | 'action_type'> & Partial<Approval>, by: string): Promise<void>;
  segnaLetta(userId: string, id?: number): Promise<void>;
  creaProgetto(nome: string, descrizione: string, by: string): Promise<void>;
  disponibilitaAgente(agentId: string, disponibile: boolean, by: string): Promise<void>;
  prendiHandoff(id: number, agentId: string | null, by: string): Promise<void>;
  chiudiHandoff(id: number, by: string): Promise<void>;
  logAgente(agentId: string, limite?: number): Promise<AgentLog[]>;
  memoria(filtro: { project_id?: number; task_id?: number; q?: string }): Promise<Memory[]>;
  aggiungiMemoria(m: Pick<Memory, 'kind' | 'content' | 'source'> & Partial<Memory>, by: string): Promise<void>;
  /** Domanda al cervello sul PC del titolare: restituisce le frasi della risposta mentre arrivano. */
  chiediCervello(userId: string, testo: string, contesto: Record<string, unknown>): AsyncIterable<string>;
}

export class ErroreDati extends Error {}

/** Messaggi leggibili per i vincoli del database (stessi casi di guardian/core/store.py:messaggio_db). */
export function messaggioVincolo(raw: string): string {
  if (/tasks_titolo_aperto/.test(raw)) return 'Esiste già un task aperto con questo titolo in questo progetto.';
  if (/tasks_un_running/.test(raw)) return 'Questo agente ha già un task in esecuzione: completalo o mettilo in attesa prima.';
  if (/dipendenze|dipendere/i.test(raw)) return 'Il task ha dipendenze non ancora completate: non può essere pronto o in esecuzione.';
  if (/projects_nome_uniq/.test(raw)) return 'Esiste già un progetto con questo nome.';
  if (/row-level security|permission denied/i.test(raw)) return 'Non hai i permessi per questa operazione.';
  return 'Operazione non riuscita. Riprova o controlla la connessione.';
}

const SEGRETO = /(sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|(password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*\S+)/i;
/** Stesso principio del filtro di registro/scrivi.py: niente segreti nei testi salvati. */
export function controllaTesto(t: string | undefined | null, campo: string, max = 4000): string {
  const v = (t ?? '').trim();
  if (SEGRETO.test(v)) throw new ErroreDati(`Il campo «${campo}» sembra contenere una password o una chiave: non va salvato.`);
  return v.slice(0, max);
}
