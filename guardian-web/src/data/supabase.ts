// SupabaseSource: Auth + query con RLS + Realtime. Solo la anon key pubblica nel browser.
// Le colonne lette sono esplicite dove serve: devices.token_hash NON è leggibile (voluto, vedi migrazione 001).
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import type { AgentLog, Memory, Snapshot, Task, User } from '../types';
import { eventiModificaTask } from './eventi';
import { controllaTesto, type DataSource, type Diretta, ErroreDati, messaggioVincolo, type ModificaTask, type NuovoTask } from './source';

const COLONNE_DEVICES = 'id,user_id,nome,agent_name,model,stato,current_task_id,error,limit_reached,last_seen,last_checkpoint,created_at';
const TABELLE_LIVE = ['agents', 'tasks', 'approvals', 'notifications', 'activity_events', 'devices', 'handoffs', 'stanze', 'projects'];

export class SupabaseSource implements DataSource {
  readonly modo = 'supabase' as const;
  private c: SupabaseClient;

  constructor(url: string, anonKey: string) {
    this.c = createClient(url, anonKey, { auth: { persistSession: true, autoRefreshToken: true } });
  }

  private async q<T>(p: PromiseLike<{ data: T | null; error: { message: string } | null }>): Promise<T> {
    const { data, error } = await p;
    if (error) throw new ErroreDati(messaggioVincolo(error.message));
    return data as T;
  }

  private async membro(email: string): Promise<User | null> {
    const r = await this.q<User[]>(this.c.from('users').select('id,nome,ruolo,agente,stato,accesso').eq('email', email.toLowerCase()).eq('stato', 'attivo'));
    return r[0] ?? null;
  }

  async utente(): Promise<User | null> {
    const { data } = await this.c.auth.getSession();
    const email = data.session?.user.email;
    return email ? this.membro(email) : null;
  }

  async accedi(email: string, password: string): Promise<User> {
    const { error } = await this.c.auth.signInWithPassword({ email: email.trim().toLowerCase(), password });
    if (error) throw new ErroreDati('Email o password non validi.');
    const u = await this.membro(email.trim());
    if (!u) { await this.c.auth.signOut(); throw new ErroreDati('Questo account non è tra i collaboratori autorizzati di Guardian.'); }
    return u;
  }

  async esci() { await this.c.auth.signOut(); }

  async carica(userId: string): Promise<Snapshot> {
    const [users, devices, agents, projects, tasks, events, approvals, notifications, handoffs, stanze] = await Promise.all([
      this.q(this.c.from('users').select('id,nome,ruolo,agente,stato,accesso').order('id')),
      this.q(this.c.from('devices').select(COLONNE_DEVICES).order('user_id')),
      this.q(this.c.from('agents').select('*').order('user_id')),
      this.q(this.c.from('projects').select('*').order('nome')),
      this.q(this.c.from('tasks').select('*').order('updated_at', { ascending: false }).limit(500)),
      this.q(this.c.from('activity_events').select('*').order('timestamp', { ascending: false }).limit(400)),
      this.q(this.c.from('approvals').select('*').order('created_at', { ascending: false }).limit(200)),
      this.q(this.c.from('notifications').select('*').eq('user_id', userId).order('created_at', { ascending: false }).limit(100)),
      this.q(this.c.from('handoffs').select('*').order('timestamp', { ascending: false }).limit(100)),
      // 005 non ancora applicata: niente stanze invece di un errore
      this.q(this.c.from('stanze').select('*').eq('attiva', true).order('ordine').then((r) => ({ data: r.error ? [] : r.data, error: null }))),
    ]);
    return { users, devices, agents, projects, tasks, events, approvals, notifications, handoffs, stanze } as Snapshot;
  }

  async ping(): Promise<number> {
    const t0 = performance.now();
    await this.q(this.c.from('users').select('id').limit(1));
    return performance.now() - t0;
  }

  ascolta(onCambio: () => void, onDiretta: (d: Diretta) => void): () => void {
    let ch = this.c.channel('guardian-live');
    for (const t of TABELLE_LIVE) ch = ch.on('postgres_changes', { event: '*', schema: 'public', table: t }, () => onCambio());
    ch.subscribe((status) => onDiretta(status === 'SUBSCRIBED' ? 'live' : 'polling'));
    return () => { void this.c.removeChannel(ch); };
  }

  private async evento(e: Record<string, unknown>) {
    await this.q(this.c.from('activity_events').insert({ files: [], ...e }));
  }

  async creaTask(t: NuovoTask, by: string): Promise<Task> {
    const riga = { ...t, titolo: controllaTesto(t.titolo, 'titolo', 200), descrizione: controllaTesto(t.descrizione, 'descrizione') || null,
      next_step: controllaTesto(t.next_step, 'prossimo passo', 1000) || null, depends_on: t.depends_on ?? [], created_by: by };
    if (!riga.titolo) throw new ErroreDati('Il titolo è obbligatorio.');
    const [creato] = await this.q<Task[]>(this.c.from('tasks').insert(riga).select());
    await this.evento({ event_type: 'task_created', message: `Creato task: ${creato.titolo}`, user_id: by, task_id: creato.id, project_id: creato.project_id });
    if (creato.assigned_agent_id) await this.evento({ event_type: 'task_assigned', message: `Task #${creato.id} assegnato a ${creato.assigned_agent_id}`,
      user_id: by, task_id: creato.id, agent_id: creato.assigned_agent_id });
    return creato;
  }

  async modificaTask(id: number, campi: ModificaTask, by: string): Promise<Task> {
    const [prima] = await this.q<Task[]>(this.c.from('tasks').select('*').eq('id', id));
    if (!prima) throw new ErroreDati('Task inesistente.');
    if (campi.next_step !== undefined) campi.next_step = controllaTesto(campi.next_step, 'prossimo passo', 1000) || null;
    const [dopo] = await this.q<Task[]>(this.c.from('tasks').update(campi).eq('id', id).select());
    for (const e of eventiModificaTask(prima, dopo, by)) await this.evento({ ...e });
    return dopo;
  }

  async decidiApprovazione(id: number, stato: 'approvata' | 'rifiutata', by: string) {
    // needs_approval -> ready/planned/blocked e le notifiche le fanno i trigger della migrazione 002.
    const r = await this.q<{ action: string; task_id: number | null }[]>(this.c.from('approvals')
      .update({ status: stato, decided_by: by, decided_at: new Date().toISOString() }).eq('id', id).eq('status', 'richiesta').select('action,task_id'));
    if (!r.length) throw new ErroreDati('Approvazione già decisa da qualcun altro.');
    await this.evento({ event_type: 'approval_decided', message: `Approvazione #${id} (${r[0].action}): ${stato}`, user_id: by, task_id: r[0].task_id });
  }

  async richiediApprovazione(a: Parameters<DataSource['richiediApprovazione']>[0], by: string) {
    const riga = { action: controllaTesto(a.action, 'azione', 200), action_type: a.action_type, task_id: a.task_id ?? null,
      reason: controllaTesto(a.reason, 'motivo', 1000) || null, impact: controllaTesto(a.impact, 'impatto', 1000) || null,
      data_involved: controllaTesto(a.data_involved, 'dati coinvolti', 1000) || null, agent_id: a.agent_id ?? null, requested_by: by };
    if (!riga.action) throw new ErroreDati("Descrivi l'azione da approvare.");
    await this.q(this.c.from('approvals').insert(riga));
    await this.evento({ event_type: 'approval_requested', message: `Richiesta approvazione: ${riga.action}`, user_id: by, task_id: riga.task_id, severity: 'warning' });
  }

  async segnaLetta(userId: string, id?: number) {
    let q = this.c.from('notifications').update({ read_at: new Date().toISOString() }).eq('user_id', userId);
    q = id ? q.eq('id', id) : q.is('read_at', null);
    await this.q(q);
  }

  async creaProgetto(nome: string, descrizione: string, by: string) {
    const n = controllaTesto(nome, 'nome', 120);
    if (!n) throw new ErroreDati('Il nome è obbligatorio.');
    const [p] = await this.q<{ id: number }[]>(this.c.from('projects').insert({ nome: n, descrizione: controllaTesto(descrizione, 'descrizione', 2000) || null, created_by: by }).select('id'));
    await this.evento({ event_type: 'project_created', message: `Creato progetto: ${n}`, user_id: by, project_id: p.id });
  }

  async disponibilitaAgente(agentId: string, disponibile: boolean, by: string) {
    await this.q(this.c.from('agents').update({ disponibile }).eq('id', agentId));
    await this.evento({ event_type: 'agent_state', message: `${agentId}: ${disponibile ? 'disponibile' : 'non disponibile'} (manuale)`, user_id: by, agent_id: agentId });
  }

  async prendiHandoff(id: number, agentId: string | null, by: string) {
    const campi = agentId ? { stato: 'preso', to_agent_id: agentId } : { stato: 'preso' };
    const r = await this.q<unknown[]>(this.c.from('handoffs').update(campi).eq('id', id).eq('stato', 'aperto').select('id'));
    if (!r.length) throw new ErroreDati('Handoff già preso.');
    await this.evento({ event_type: 'handoff_taken', message: `Handoff #${id} preso${agentId ? ` da ${agentId}` : ''}`, user_id: by, agent_id: agentId });
  }

  async chiudiHandoff(id: number, by: string) {
    await this.q(this.c.from('handoffs').update({ stato: 'chiuso' }).eq('id', id));
    await this.evento({ event_type: 'handoff_closed', message: `Handoff #${id} chiuso`, user_id: by });
  }

  async logAgente(agentId: string, limite = 100): Promise<AgentLog[]> {
    return this.q(this.c.from('agent_logs').select('*').eq('agent_id', agentId).order('ts', { ascending: false }).limit(limite));
  }

  async memoria(f: { project_id?: number; task_id?: number; q?: string }): Promise<Memory[]> {
    let q = this.c.from('memory').select('id,project_id,task_id,kind,content,source,created_by,created_at,superseded_by').is('superseded_by', null);
    if (f.project_id) q = q.eq('project_id', f.project_id);
    if (f.task_id) q = q.eq('task_id', f.task_id);
    if (f.q?.trim()) q = q.textSearch('ricerca', f.q.trim(), { config: 'italian', type: 'plain' });
    return this.q(q.order('created_at', { ascending: false }).limit(100));
  }

  async aggiungiMemoria(m: Parameters<DataSource['aggiungiMemoria']>[0], by: string) {
    const content = controllaTesto(m.content, 'contenuto'); const source = controllaTesto(m.source, 'fonte', 300);
    if (!content || !source) throw new ErroreDati('Contenuto e fonte sono obbligatori.');
    await this.q(this.c.from('memory').insert({ kind: m.kind, content, source, project_id: m.project_id ?? null, task_id: m.task_id ?? null, created_by: by }));
  }
}
