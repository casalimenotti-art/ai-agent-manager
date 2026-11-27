// Tipi di dominio: specchio dello schema Supabase (supabase/migrations/001–004). Non inventare campi.
export const TASK_STATI = ['backlog', 'planned', 'ready', 'running', 'waiting', 'blocked', 'needs_approval', 'completed',
  'failed', 'cancelled'] as const;
export type TaskStato = (typeof TASK_STATI)[number];
export const TASK_TERMINALI: TaskStato[] = ['completed', 'failed', 'cancelled'];
export const AGENT_STATI = ['online', 'offline', 'idle', 'working', 'waiting', 'needs_approval', 'error', 'unknown'] as const;
export type AgentStato = (typeof AGENT_STATI)[number];
export const PRIORITA = ['bassa', 'media', 'alta', 'urgente'] as const;
export type Priorita = (typeof PRIORITA)[number];
export const ACTION_TYPES = ['email', 'pubblicazione', 'contatto_cliente', 'spesa', 'pagamento', 'irreversibile',
  'account_esterno', 'comando_pericoloso', 'altro'] as const;
export type ActionType = (typeof ACTION_TYPES)[number];
export type Severita = 'info' | 'warning' | 'error' | 'critical';
export const MEMORY_KINDS = ['obiettivo', 'decisione', 'info_progetto', 'preferenza', 'risultato', 'errore', 'procedura',
  'ripresa'] as const;

export interface User { id: string; nome: string; ruolo?: string | null; agente?: string | null; stato: string; accesso?: string }
export interface Device {
  id: number; user_id: string; nome: string; agent_name?: string | null; model?: string | null; stato: string;
  current_task_id?: number | null; error?: string | null; limit_reached: boolean; last_seen?: string | null;
  last_checkpoint?: string | null; created_at?: string;
}
export interface Usage { five_hour?: { pct: number; resets_at?: unknown }; seven_day?: { pct: number; resets_at?: unknown } }
export interface Agent {
  id: string; user_id: string; device_id?: number | null; nome: string; tipo: string; capabilities: string[];
  stato: AgentStato; current_task_id?: number | null; last_heartbeat?: string | null; last_activity?: string | null;
  error?: string | null; disponibile: boolean; usage?: Usage | null;
}
export interface Project { id: number; nome: string; descrizione?: string | null; stato: string; created_at: string; updated_at?: string; stanza_id?: string | null }
/** Stanza dell'HQ (migrazione 005): dato, non codice. */
export interface Stanza { id: string; nome: string; descrizione?: string | null; colore: string; responsabile?: string | null; ordine: number; attiva: boolean }
export interface Task {
  id: number; titolo: string; descrizione?: string | null; responsabile?: string | null; agente?: string | null;
  priorita: Priorita; stato: TaskStato; next_step?: string | null; files_changed: string[]; created_by?: string | null;
  created_at: string; updated_at: string; project_id?: number | null; plan_id?: number | null;
  assigned_agent_id?: string | null; depends_on: number[]; result?: string | null; error?: string | null;
  expected_result?: string | null; completion_criteria?: string | null;
}
export interface ActivityEvent {
  id: number; task_id?: number | null; device_id?: number | null; user_id?: string | null; agent_name?: string | null;
  agent_id?: string | null; project_id?: number | null; event_type: string; message: string; files: string[];
  severity: Severita; timestamp: string;
}
export interface Approval {
  id: number; task_id?: number | null; action: string; description?: string | null; status: 'richiesta' | 'approvata' | 'rifiutata';
  requested_by?: string | null; decided_by?: string | null; created_at: string; decided_at?: string | null;
  agent_id?: string | null; action_type: ActionType; reason?: string | null; impact?: string | null; data_involved?: string | null;
}
export interface Notification {
  id: number; user_id: string; kind: string; message: string; ref_table?: string | null; ref_id?: string | null;
  read_at?: string | null; created_at: string;
}
export interface Handoff {
  id: number; task_id?: number | null; agent_name: string; summary: string; completed_steps?: string | null;
  files_changed: string[]; decisions?: string | null; errors?: string | null; tests?: string | null; next_step: string;
  timestamp: string; from_agent_id?: string | null; to_agent_id?: string | null; tests_pending?: string | null;
  dependencies?: string | null; important_notes?: string | null; stato: 'aperto' | 'preso' | 'chiuso';
}
export interface Memory {
  id: number; project_id?: number | null; task_id?: number | null; kind: string; content: string; source: string;
  created_by?: string | null; created_at: string; superseded_by?: number | null;
}
export interface AgentLog {
  id: number; agent_id?: string | null; device_id?: number | null; task_id?: number | null; level: string; source: string;
  message: string; ts: string;
}

/** Fotografia di tutti i dati che la vista centrale usa. */
export interface Snapshot {
  users: User[]; devices: Device[]; agents: Agent[]; projects: Project[]; tasks: Task[]; events: ActivityEvent[];
  approvals: Approval[]; notifications: Notification[]; handoffs: Handoff[]; stanze: Stanza[];
  /** Stato del cervello sul PC del titolare (migrazione 006); null se non configurato. */
  cervello: { modello?: string | null; ultimo_battito?: string | null } | null;
}
