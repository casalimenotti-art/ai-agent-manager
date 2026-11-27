// DemoSource: dati di esempio IN MEMORIA, solo con VITE_DEMO=1 (sviluppo locale e test E2E).
// Non scrive mai su Supabase. L'interfaccia mostra sempre il banner "Dati di esempio — solo locale".
// Applica gli stessi vincoli del DB (titoli unici tra gli aperti, un running per agente, dipendenze, needs_approval).
import type { Agent, AgentLog, Approval, Memory, Snapshot, Task, User } from '../types';
import { TASK_TERMINALI } from '../types';
import { eventiModificaTask } from './eventi';
import { controllaTesto, type DataSource, type Diretta, ErroreDati, type ModificaTask, type NuovoTask } from './source';

const min = (m: number) => new Date(Date.now() - m * 60_000).toISOString();

function seme(): Snapshot & { logs: AgentLog[]; memory: Memory[] } {
  const users: User[] = [
    { id: 'menotti', nome: 'Menotti', ruolo: 'Siti, test, software, dashboard', agente: 'Claude Code', stato: 'attivo', accesso: 'admin' },
    { id: 'amico1', nome: 'Niko', ruolo: 'Vendite e dati clienti', agente: 'Codex', stato: 'attivo', accesso: 'member' },
    { id: 'amico2', nome: 'Francesco', ruolo: 'Amministrazione', agente: 'Codex', stato: 'attivo', accesso: 'member' },
  ];
  const agents: Agent[] = [
    { id: 'menotti-claude', user_id: 'menotti', device_id: 1, nome: 'Claude Code', tipo: 'claude-code', capabilities: ['python', 'siti', 'test'],
      stato: 'working', current_task_id: 1, last_heartbeat: min(0.5), last_activity: min(1), disponibile: true,
      usage: { five_hour: { pct: 42 }, seven_day: { pct: 18 } } },
    { id: 'amico1-codex', user_id: 'amico1', device_id: 2, nome: 'Codex', tipo: 'codex', capabilities: ['vendite', 'dati'],
      stato: 'idle', last_heartbeat: min(1), last_activity: min(25), disponibile: true },
    { id: 'amico2-codex', user_id: 'amico2', device_id: null, nome: 'Codex', tipo: 'codex', capabilities: ['amministrazione'],
      stato: 'idle', last_heartbeat: min(300), disponibile: true },
  ];
  const t = (p: Partial<Task> & Pick<Task, 'id' | 'titolo' | 'stato'>): Task => ({ priorita: 'media', files_changed: [], depends_on: [],
    created_at: min(600), updated_at: min(30), responsabile: 'menotti', ...p });
  const tasks: Task[] = [
    t({ id: 1, titolo: 'Sito demo Ottica Ungari', stato: 'running', priorita: 'alta', project_id: 1, assigned_agent_id: 'menotti-claude',
      next_step: 'Rifinire il footer e i contatti', expected_result: 'Bozza pronta per la visita', updated_at: min(4) }),
    t({ id: 2, titolo: 'Bozze contatto 30 clienti', stato: 'ready', priorita: 'urgente', project_id: 2, responsabile: 'amico1' }),
    t({ id: 3, titolo: 'Invio preventivo a Bellini B&B', stato: 'needs_approval', project_id: 2, responsabile: 'amico1', assigned_agent_id: 'amico1-codex' }),
    t({ id: 4, titolo: 'Pubblicazione siti demo', stato: 'planned', project_id: 1, depends_on: [1] }),
    t({ id: 5, titolo: 'Apertura partita IVA della SRL', stato: 'blocked', project_id: 3, responsabile: 'amico2', error: 'Manca la firma del notaio' }),
    t({ id: 6, titolo: 'Test dashboard su telefono', stato: 'completed', project_id: 1, updated_at: min(90) }),
    t({ id: 7, titolo: 'Collegare Gmail per le bozze', stato: 'backlog', priorita: 'bassa' }),
  ];
  const ev = (id: number, event_type: string, message: string, m: number, extra: object = {}) =>
    ({ id, event_type, message, timestamp: min(m), files: [], severity: 'info' as const, user_id: 'menotti', ...extra });
  return {
    users, agents, tasks,
    devices: [
      { id: 1, user_id: 'menotti', nome: 'JARVIS-7472', agent_name: 'Claude Code', stato: 'online', limit_reached: false, last_seen: min(0.5), last_checkpoint: min(40) },
      { id: 2, user_id: 'amico1', nome: 'PC-Niko', agent_name: 'Codex', stato: 'online', limit_reached: false, last_seen: min(1) },
    ],
    projects: [
      { id: 1, nome: 'Siti web', descrizione: 'Siti demo e siti dei clienti', stato: 'attivo', created_at: min(5000) },
      { id: 2, nome: 'Agenzia AI · vendite', descrizione: 'Contatti e preventivi', stato: 'attivo', created_at: min(5000) },
      { id: 3, nome: 'Amministrazione SRL', descrizione: null, stato: 'attivo', created_at: min(5000) },
    ],
    events: [
      ev(1, 'task_started', 'Claude Code ha preso il task #1: Sito demo Ottica Ungari', 50, { task_id: 1, agent_id: 'menotti-claude', agent_name: 'Claude Code' }),
      ev(2, 'approval_requested', 'Richiesta approvazione: Invio preventivo a Bellini B&B', 35, { task_id: 3, severity: 'warning', user_id: 'amico1' }),
      ev(3, 'task_completed', 'Task #6 running → completed', 90, { task_id: 6 }),
      ev(4, 'checkpoint', 'Handoff salvato. Prossimo passo: Rifinire il footer e i contatti', 40, { task_id: 1, agent_id: 'menotti-claude' }),
      ev(5, 'task_updated', 'Task #5 running → blocked', 120, { task_id: 5, user_id: 'amico2', severity: 'warning' }),
      ev(6, 'agent_connected', 'Codex: unknown → idle', 25, { agent_id: 'amico1-codex', user_id: 'amico1' }),
    ],
    approvals: [{ id: 1, task_id: 3, action: 'Invio preventivo a Bellini B&B', action_type: 'email', status: 'richiesta', requested_by: 'amico1',
      agent_id: 'amico1-codex', reason: 'Il cliente ha chiesto il preventivo in visita', impact: '1 email al cliente',
      data_involved: 'Email pubblica del B&B, importo del preventivo', created_at: min(35) }],
    notifications: [
      { id: 1, user_id: 'menotti', kind: 'approval_requested', message: 'Da approvare: Invio preventivo a Bellini B&B', ref_table: 'approvals', ref_id: '1', created_at: min(35) },
      { id: 2, user_id: 'menotti', kind: 'task_failed', message: 'Esempio già letto', ref_table: 'tasks', ref_id: '5', read_at: min(60), created_at: min(120) },
    ],
    handoffs: [{ id: 1, task_id: 1, agent_name: 'Claude Code', summary: 'Sito al 70%: header e galleria fatti', next_step: 'Rifinire il footer e i contatti',
      files_changed: ['siti-demo/ottica-ungari.html'], tests_pending: 'Controllo su telefono', important_notes: 'Orari da confermare col cliente',
      from_agent_id: 'menotti-claude', to_agent_id: 'amico1-codex', stato: 'aperto', timestamp: min(40) }],
    logs: [
      { id: 1, agent_id: 'menotti-claude', device_id: 1, task_id: 1, level: 'info', source: 'hook', message: 'Strumento: Edit', ts: min(1) },
      { id: 2, agent_id: 'menotti-claude', device_id: 1, task_id: 1, level: 'info', source: 'hook', message: "Richiesta all'agente: rifinisci il footer", ts: min(3) },
    ],
    memory: [{ id: 1, project_id: 1, kind: 'decisione', content: 'Nei siti demo niente risorse esterne (font, CDN).', source: 'CONTINUA.md', created_by: 'menotti', created_at: min(2000) }],
  };
}

export class DemoSource implements DataSource {
  readonly modo = 'demo' as const;
  private d = seme();
  private ascoltatori = new Set<() => void>();
  private loggato: User | null = null;

  private cambiato() { this.ascoltatori.forEach((f) => f()); }
  private nid(arr: { id: number }[]) { return Math.max(0, ...arr.map((x) => x.id)) + 1; }
  private evento(e: Partial<Snapshot['events'][number]> & { event_type: string; message: string }) {
    this.d.events.unshift({ id: this.nid(this.d.events), files: [], severity: 'info', timestamp: new Date().toISOString(), ...e });
  }
  private notifica(userIds: string[] | null, kind: string, message: string, ref_table: string, ref_id: string | number) {
    for (const u of userIds ?? this.d.users.map((x) => x.id))
      this.d.notifications.unshift({ id: this.nid(this.d.notifications), user_id: u, kind, message, ref_table, ref_id: String(ref_id), created_at: new Date().toISOString() });
  }

  async utente() { return this.loggato; }
  async accedi(email: string) { this.loggato = this.d.users.find((u) => email.startsWith(u.id)) ?? this.d.users[0]; return this.loggato; }
  async esci() { this.loggato = null; }
  async carica(userId: string): Promise<Snapshot> {
    const { logs: _l, memory: _m, ...s } = this.d;
    return structuredClone({ ...s, notifications: s.notifications.filter((n) => n.user_id === userId) });
  }
  async ping() { return 1; }
  ascolta(onCambio: () => void, onDiretta: (d: Diretta) => void) {
    this.ascoltatori.add(onCambio); onDiretta('off');
    return () => { this.ascoltatori.delete(onCambio); };
  }

  private controlla(t: Task) {
    const aperti = this.d.tasks.filter((x) => x.id !== t.id && !TASK_TERMINALI.includes(x.stato));
    if (!TASK_TERMINALI.includes(t.stato) && aperti.some((x) => (x.project_id ?? 0) === (t.project_id ?? 0) && x.titolo.toLowerCase() === t.titolo.toLowerCase()))
      throw new ErroreDati('Esiste già un task aperto con questo titolo in questo progetto.');
    if (t.stato === 'running' && t.assigned_agent_id && aperti.some((x) => x.stato === 'running' && x.assigned_agent_id === t.assigned_agent_id))
      throw new ErroreDati('Questo agente ha già un task in esecuzione: completalo o mettilo in attesa prima.');
    if (['ready', 'running'].includes(t.stato) && t.depends_on.some((d) => this.d.tasks.find((x) => x.id === d)?.stato !== 'completed'))
      throw new ErroreDati('Il task ha dipendenze non ancora completate: non può essere pronto o in esecuzione.');
  }

  async creaTask(n: NuovoTask, by: string) {
    const titolo = controllaTesto(n.titolo, 'titolo', 200);
    if (!titolo) throw new ErroreDati('Il titolo è obbligatorio.');
    const ora = new Date().toISOString();
    const t: Task = { id: this.nid(this.d.tasks), titolo, descrizione: controllaTesto(n.descrizione, 'descrizione') || null, priorita: n.priorita,
      stato: n.stato, project_id: n.project_id ?? null, responsabile: n.responsabile ?? null, assigned_agent_id: n.assigned_agent_id ?? null,
      depends_on: n.depends_on ?? [], files_changed: [], expected_result: n.expected_result || null, completion_criteria: n.completion_criteria || null,
      next_step: controllaTesto(n.next_step, 'prossimo passo', 1000) || null, created_by: by, created_at: ora, updated_at: ora };
    this.controlla(t);
    this.d.tasks.unshift(t);
    this.evento({ event_type: 'task_created', message: `Creato task: ${t.titolo}`, user_id: by, task_id: t.id, project_id: t.project_id });
    this.cambiato();
    return structuredClone(t);
  }

  async modificaTask(id: number, campi: ModificaTask, by: string) {
    const i = this.d.tasks.findIndex((t) => t.id === id);
    if (i < 0) throw new ErroreDati('Task inesistente.');
    const prima = this.d.tasks[i];
    const dopo: Task = { ...prima, ...campi, updated_at: new Date().toISOString() };
    this.controlla(dopo);
    this.d.tasks[i] = dopo;
    for (const e of eventiModificaTask(prima, dopo, by)) this.evento(e);
    if (dopo.stato === 'failed' && prima.stato !== 'failed') this.notifica(dopo.responsabile ? [dopo.responsabile] : null, 'task_failed', `Task #${id} fallito: ${dopo.titolo}`, 'tasks', id);
    this.cambiato();
    return structuredClone(dopo);
  }

  async decidiApprovazione(id: number, stato: 'approvata' | 'rifiutata', by: string) {
    const a = this.d.approvals.find((x) => x.id === id && x.status === 'richiesta');
    if (!a) throw new ErroreDati('Approvazione già decisa da qualcun altro.');
    Object.assign(a, { status: stato, decided_by: by, decided_at: new Date().toISOString() });
    const t = this.d.tasks.find((x) => x.id === a.task_id);
    if (t && t.stato === 'needs_approval' && !this.d.approvals.some((x) => x.task_id === t.id && x.status === 'richiesta')) {
      t.stato = stato === 'rifiutata' ? 'blocked' : t.depends_on.some((d) => this.d.tasks.find((x) => x.id === d)?.stato !== 'completed') ? 'planned' : 'ready';
      t.updated_at = new Date().toISOString();
    }
    this.evento({ event_type: 'approval_decided', message: `Approvazione #${id} (${a.action}): ${stato}`, user_id: by, task_id: a.task_id });
    if (a.requested_by) this.notifica([a.requested_by], 'approval_decided', `${a.action}: ${stato}`, 'approvals', id);
    this.cambiato();
  }

  async richiediApprovazione(a: Parameters<DataSource['richiediApprovazione']>[0], by: string) {
    const action = controllaTesto(a.action, 'azione', 200);
    if (!action) throw new ErroreDati("Descrivi l'azione da approvare.");
    const id = this.nid(this.d.approvals);
    const riga: Approval = { id, action, action_type: a.action_type, status: 'richiesta', requested_by: by, created_at: new Date().toISOString(),
      task_id: a.task_id ?? null, reason: a.reason ?? null, impact: a.impact ?? null, data_involved: a.data_involved ?? null, agent_id: a.agent_id ?? null };
    this.d.approvals.unshift(riga);
    const t = this.d.tasks.find((x) => x.id === riga.task_id);
    if (t && !TASK_TERMINALI.includes(t.stato)) t.stato = 'needs_approval';
    this.evento({ event_type: 'approval_requested', message: `Richiesta approvazione: ${action}`, user_id: by, task_id: riga.task_id, severity: 'warning' });
    this.notifica(null, 'approval_requested', `Da approvare: ${action}`, 'approvals', id);
    this.cambiato();
  }

  async segnaLetta(userId: string, id?: number) {
    for (const n of this.d.notifications) if (n.user_id === userId && (!id || n.id === id) && !n.read_at) n.read_at = new Date().toISOString();
    this.cambiato();
  }

  async creaProgetto(nome: string, descrizione: string, by: string) {
    const n = controllaTesto(nome, 'nome', 120);
    if (!n) throw new ErroreDati('Il nome è obbligatorio.');
    if (this.d.projects.some((p) => p.nome.toLowerCase() === n.toLowerCase())) throw new ErroreDati('Esiste già un progetto con questo nome.');
    const id = this.nid(this.d.projects);
    this.d.projects.push({ id, nome: n, descrizione: descrizione || null, stato: 'attivo', created_at: new Date().toISOString() });
    this.evento({ event_type: 'project_created', message: `Creato progetto: ${n}`, user_id: by, project_id: id });
    this.cambiato();
  }

  async disponibilitaAgente(agentId: string, disponibile: boolean, by: string) {
    const a = this.d.agents.find((x) => x.id === agentId);
    if (a) a.disponibile = disponibile;
    this.evento({ event_type: 'agent_state', message: `${agentId}: ${disponibile ? 'disponibile' : 'non disponibile'} (manuale)`, user_id: by, agent_id: agentId });
    this.cambiato();
  }

  async prendiHandoff(id: number, agentId: string | null, by: string) {
    const h = this.d.handoffs.find((x) => x.id === id && x.stato === 'aperto');
    if (!h) throw new ErroreDati('Handoff già preso.');
    h.stato = 'preso'; if (agentId) h.to_agent_id = agentId;
    this.evento({ event_type: 'handoff_taken', message: `Handoff #${id} preso${agentId ? ` da ${agentId}` : ''}`, user_id: by, task_id: h.task_id });
    this.cambiato();
  }

  async chiudiHandoff(id: number, by: string) {
    const h = this.d.handoffs.find((x) => x.id === id);
    if (h) h.stato = 'chiuso';
    this.evento({ event_type: 'handoff_closed', message: `Handoff #${id} chiuso`, user_id: by, task_id: h?.task_id });
    this.cambiato();
  }

  async logAgente(agentId: string) { return structuredClone(this.d.logs.filter((l) => l.agent_id === agentId)); }

  async memoria(f: { project_id?: number; task_id?: number; q?: string }) {
    const parole = (f.q ?? '').toLowerCase().split(/\s+/).filter(Boolean);
    return structuredClone(this.d.memory.filter((m) => !m.superseded_by && (!f.project_id || m.project_id === f.project_id) &&
      (!f.task_id || m.task_id === f.task_id) && parole.every((p) => m.content.toLowerCase().includes(p))));
  }

  async aggiungiMemoria(m: Parameters<DataSource['aggiungiMemoria']>[0], by: string) {
    const content = controllaTesto(m.content, 'contenuto'); const source = controllaTesto(m.source, 'fonte', 300);
    if (!content || !source) throw new ErroreDati('Contenuto e fonte sono obbligatori.');
    this.d.memory.unshift({ id: this.nid(this.d.memory), kind: m.kind, content, source, project_id: m.project_id ?? null,
      task_id: m.task_id ?? null, created_by: by, created_at: new Date().toISOString() });
    this.cambiato();
  }
}
