import type { Cambio } from '../logic/live';
import type { AgentLog, Approval, Costo, Scadenza, Vendita, Memory, Priorita, Snapshot, Task, TaskStato, User } from '../types';

export type Diretta = 'live' | 'polling' | 'off';
/** Chi è nell'HQ in questo momento (Presence di Supabase Realtime: niente salvato nel database). */
export interface Presente { id: string; nome: string; stanza: string | null; dal: string }
export interface Presenza { segnala(stanza: string | null): void; stop(): void }

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
  /** Avvisa quando cambiano i dati (con il cambio, se noto, per applicarlo subito). Restituisce la funzione per annullare. */
  ascolta(onCambio: (c?: Cambio) => void, onDiretta: (d: Diretta) => void): () => void;
  /** Annuncia la propria presenza nell'HQ e riceve l'elenco di chi c'è. */
  presenza(u: User, onPresenti: (p: Presente[]) => void): Presenza;
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
  creaVendita(v: Pick<Vendita, 'azienda' | 'fase' | 'fonte'> & Partial<Vendita>, by: string): Promise<void>;
  aggiornaVendita(id: number, campi: Partial<Pick<Vendita, 'fase' | 'valore_eur' | 'prossimo_passo' | 'responsabile'>>, by: string): Promise<void>;
  creaScadenza(s: Pick<Scadenza, 'titolo' | 'data' | 'tipo' | 'fonte'> & Partial<Scadenza>, by: string): Promise<void>;
  aggiornaScadenza(id: number, campi: Partial<Pick<Scadenza, 'stato' | 'data' | 'importo_eur'>>, by: string): Promise<void>;
  creaCosto(c: Pick<Costo, 'descrizione' | 'importo_eur' | 'categoria' | 'ricorrenza' | 'fonte'> & Partial<Costo>, by: string): Promise<void>;
  /** Registra un PC salvando solo l'hash del codice (mai il codice). */
  registraPc(userId: string, nome: string, hashCodice: string, by: string): Promise<void>;
  /** Revoca un PC: il suo codice smette di funzionare (l'hash viene sostituito con uno nuovo mai mostrato). */
  revocaPc(id: number, nuovoHash: string, by: string, nome: string): Promise<void>;
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

/** Stesso controllo di public.senza_dati_personali (migrazione 008): niente email né telefoni dei clienti nel DB condiviso. */
export function senzaDatiPersonali(t: string | undefined | null, campo: string): string {
  const v = (t ?? '').trim();
  if (/[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/i.test(v) || /\d{9,}/.test(v.replace(/[\s.()/-]/g, '')))
    throw new ErroreDati(`Il campo «${campo}» contiene un'email o un numero di telefono: i dati dei clienti restano nel CSV dei lead, non qui.`);
  return v;
}
export function controllaFonte(f: string | undefined | null): string {
  const v = senzaDatiPersonali(controllaTesto(f, 'fonte', 200), 'fonte');
  if (v.length < 3) throw new ErroreDati('Indica la fonte (es. «fattura n. 12», «visita 26/11»): senza fonte il dato non si salva.');
  return v;
}

const SEGRETO = /(sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|(password|passwd|pwd|token|api[_-]?key)\s*[:=]\s*\S+)/i;
/** Stesso principio del filtro di registro/scrivi.py: niente segreti nei testi salvati. */
export function controllaTesto(t: string | undefined | null, campo: string, max = 4000): string {
  const v = (t ?? '').trim();
  if (SEGRETO.test(v)) throw new ErroreDati(`Il campo «${campo}» sembra contenere una password o una chiave: non va salvato.`);
  return v.slice(0, max);
}
