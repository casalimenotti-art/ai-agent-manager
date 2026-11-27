// Pannelli del lavoro: task, approvazioni, handoff, memoria. Ogni azione chiama la fonte dati reale.
import { BookOpen, ListTodo, Plus, ShieldCheck, Shuffle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { suggerisci } from '../../logic/assign';
import { fa } from '../../logic/status';
import { useG, type Pannello } from '../../state';
import { ACTION_TYPES, MEMORY_KINDS, PRIORITA, TASK_STATI, TASK_TERMINALI, type ActionType, type Memory, type Priorita, type TaskStato } from '../../types';
import { ETICHETTE_TASK, Scheletro, StatoTask, Vuoto } from '../kit';

export const ETICHETTE_AZIONE: Record<ActionType, string> = { email: 'Invio email', pubblicazione: 'Pubblicazione', contatto_cliente: 'Contatto con clienti',
  spesa: 'Spesa', pagamento: 'Pagamento', irreversibile: 'Modifica irreversibile', account_esterno: 'Account esterno',
  comando_pericoloso: 'Comando pericoloso', altro: 'Altro' };

function NuovoTask({ onFatto }: { onFatto: () => void }) {
  const { snap, source, esegui, user } = useG();
  const [f, setF] = useState({ titolo: '', descrizione: '', priorita: 'media' as Priorita, stato: 'backlog' as TaskStato, project_id: '', agente: '',
    responsabile: user.id, deps: [] as number[], atteso: '', criteri: '', next: '' });
  if (!snap) return null;
  const aperti = snap.tasks.filter((t) => !TASK_TERMINALI.includes(t.stato));
  const sug = suggerisci([], snap.agents, snap.tasks);
  return (
    <form className="card stack" onSubmit={async (e) => {
      e.preventDefault();
      const ok = await esegui(() => source.creaTask({ titolo: f.titolo, descrizione: f.descrizione, priorita: f.priorita, stato: f.stato,
        project_id: f.project_id ? Number(f.project_id) : null, assigned_agent_id: f.agente || null, responsabile: f.responsabile || null,
        depends_on: f.deps, expected_result: f.atteso, completion_criteria: f.criteri, next_step: f.next }, user.id), 'Task creato');
      if (ok) onFatto();
    }}>
      <label className="field">Titolo *<input className="input" required value={f.titolo} onChange={(e) => setF({ ...f, titolo: e.target.value })} /></label>
      <label className="field">Descrizione<textarea className="input" value={f.descrizione} onChange={(e) => setF({ ...f, descrizione: e.target.value })} /></label>
      <div className="grid2">
        <label className="field">Azienda<select className="input" value={f.project_id} onChange={(e) => setF({ ...f, project_id: e.target.value })}>
          <option value="">—</option>{snap.projects.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}</select></label>
        <label className="field">Responsabile<select className="input" value={f.responsabile} onChange={(e) => setF({ ...f, responsabile: e.target.value })}>
          {snap.users.map((u) => <option key={u.id} value={u.id}>{u.nome}</option>)}</select></label>
        <label className="field">Agente{sug ? ` (suggerito: ${sug})` : ''}<select className="input" value={f.agente} onChange={(e) => setF({ ...f, agente: e.target.value })}>
          <option value="">—</option>{snap.agents.map((a) => <option key={a.id} value={a.id}>{a.nome} · {a.id}</option>)}</select></label>
        <label className="field">Priorità<select className="input" value={f.priorita} onChange={(e) => setF({ ...f, priorita: e.target.value as Priorita })}>
          {PRIORITA.map((p) => <option key={p}>{p}</option>)}</select></label>
        <label className="field">Stato iniziale<select className="input" value={f.stato} onChange={(e) => setF({ ...f, stato: e.target.value as TaskStato })}>
          {(['backlog', 'planned', 'ready'] as TaskStato[]).map((s) => <option key={s} value={s}>{ETICHETTE_TASK[s]}</option>)}</select></label>
        <label className="field">Dipende da<select className="input" multiple value={f.deps.map(String)} style={{ minHeight: 70 }}
          onChange={(e) => setF({ ...f, deps: Array.from(e.target.selectedOptions).map((o) => Number(o.value)) })}>
          {aperti.map((t) => <option key={t.id} value={t.id}>#{t.id} {t.titolo}</option>)}</select></label>
      </div>
      <label className="field">Risultato atteso<input className="input" value={f.atteso} onChange={(e) => setF({ ...f, atteso: e.target.value })} /></label>
      <label className="field">Criteri di completamento<input className="input" value={f.criteri} onChange={(e) => setF({ ...f, criteri: e.target.value })} /></label>
      <label className="field">Prossimo passo<input className="input" value={f.next} onChange={(e) => setF({ ...f, next: e.target.value })} /></label>
      <button className="btn primary" type="submit"><Plus size={16} aria-hidden />Crea task</button>
    </form>
  );
}

const FILTRI: Record<string, { nome: string; stati: TaskStato[] }> = {
  attivi: { nome: 'Attivi', stati: ['running', 'waiting', 'needs_approval', 'blocked', 'ready'] }, fermi: { nome: 'Bloccati / falliti', stati: ['blocked', 'failed'] },
  coda: { nome: 'In coda', stati: ['backlog', 'planned', 'ready'] }, chiusi: { nome: 'Chiusi', stati: ['completed', 'failed', 'cancelled'] },
  tutti: { nome: 'Tutti', stati: [...TASK_STATI] } };

export function TasksPanel({ filtro }: Pannello) {
  const { snap, apri } = useG();
  const [f, setF] = useState(filtro && FILTRI[filtro] ? filtro : 'attivi');
  const [nuovo, setNuovo] = useState(filtro === 'nuovo');
  const [azienda, setAzienda] = useState('');
  if (!snap) return <Scheletro />;
  const lista = snap.tasks.filter((t) => FILTRI[f].stati.includes(t.stato) && (!azienda || String(t.project_id) === azienda));
  return (<>
    <div className="row">
      {Object.entries(FILTRI).map(([k, v]) => <button key={k} className={`btn sm ${f === k ? 'primary' : ''}`} aria-pressed={f === k} onClick={() => setF(k)}>{v.nome}</button>)}
    </div>
    <div className="row">
      <select className="input" style={{ maxWidth: 240 }} value={azienda} onChange={(e) => setAzienda(e.target.value)} aria-label="Filtra per azienda">
        <option value="">Tutte le aziende</option>{snap.projects.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}</select>
      <button className="btn" onClick={() => setNuovo((n) => !n)} aria-expanded={nuovo}><Plus size={16} aria-hidden />Nuovo task</button>
    </div>
    {nuovo && <NuovoTask onFatto={() => setNuovo(false)} />}
    {lista.length === 0 ? <Vuoto icona={ListTodo}>Nessun task in questo filtro.</Vuoto> : (
      <div className="list">{lista.map((t) => (
        <button key={t.id} className="item" onClick={() => apri({ p: 'task', id: String(t.id) })}>
          <div style={{ flex: 1 }}><div className="t">#{t.id} {t.titolo}</div><div className="s">{t.priorita} · {fa(t.updated_at)}</div></div><StatoTask s={t.stato} />
        </button>))}</div>)}
  </>);
}

export function TaskPanel({ id }: Pannello) {
  const { snap, source, esegui, user, apri } = useG();
  const t = snap?.tasks.find((x) => String(x.id) === id);
  const [m, setM] = useState({ stato: t?.stato, priorita: t?.priorita, agente: t?.assigned_agent_id ?? '', next: t?.next_step ?? '' });
  const [mem, setMem] = useState<Memory[] | null>(null);
  useEffect(() => { if (t) setM({ stato: t.stato, priorita: t.priorita, agente: t.assigned_agent_id ?? '', next: t.next_step ?? '' }); }, [t?.id, t?.updated_at]); // eslint-disable-line
  useEffect(() => { if (t) void source.memoria({ task_id: t.id }).then(setMem).catch(() => setMem([])); }, [source, t?.id]); // eslint-disable-line
  if (!snap) return <Scheletro />;
  if (!t) return <Vuoto>Task non trovato (forse è stato eliminato o non hai accesso).</Vuoto>;
  const nome = (uid?: string | null) => snap.users.find((u) => u.id === uid)?.nome ?? uid ?? '—';
  const eventi = snap.events.filter((e) => e.task_id === t.id).slice(0, 15);
  const handoff = snap.handoffs.filter((h) => h.task_id === t.id);
  const appr = snap.approvals.filter((a) => a.task_id === t.id);
  return (<>
    <div className="row"><StatoTask s={t.stato} /><span className="pill">{t.priorita}</span>
      {t.project_id && <button className="pill accent" style={{ border: 0, cursor: 'pointer' }} onClick={() => apri({ p: 'azienda', id: String(t.project_id) })}>
        {snap.projects.find((p) => p.id === t.project_id)?.nome}</button>}</div>
    {t.descrizione && <p style={{ margin: 0 }}>{t.descrizione}</p>}
    <dl className="kv">
      <dt>Responsabile</dt><dd>{nome(t.responsabile)}</dd>
      <dt>Agente</dt><dd>{t.assigned_agent_id ? <a href="#" onClick={(e) => { e.preventDefault(); apri({ p: 'agente', id: t.assigned_agent_id! }); }}>{t.assigned_agent_id}</a> : '—'}</dd>
      <dt>Piano</dt><dd>{t.plan_id ? `piano #${t.plan_id}` : '—'}</dd>
      {t.expected_result && <><dt>Risultato atteso</dt><dd>{t.expected_result}</dd></>}
      {t.completion_criteria && <><dt>Criteri</dt><dd>{t.completion_criteria}</dd></>}
      {t.result && <><dt>Risultato</dt><dd>{t.result}</dd></>}
      {t.error && <><dt>Errore</dt><dd style={{ color: 'var(--crit)' }}>{t.error}</dd></>}
      <dt>Dipende da</dt><dd>{t.depends_on.length ? t.depends_on.map((d) => {
        const dt = snap.tasks.find((x) => x.id === d);
        return <button key={d} className="pill" style={{ border: 0, cursor: 'pointer', marginRight: 4 }} onClick={() => apri({ p: 'task', id: String(d) })}>
          #{d} {dt ? ETICHETTE_TASK[dt.stato] : ''}</button>; }) : '—'}</dd>
      <dt>Aggiornato</dt><dd>{fa(t.updated_at)}</dd>
    </dl>
    <form className="card stack" onSubmit={(e) => { e.preventDefault();
      void esegui(() => source.modificaTask(t.id, { stato: m.stato, priorita: m.priorita, assigned_agent_id: m.agente || null, next_step: m.next }, user.id), 'Task aggiornato'); }}>
      <h3 className="section-title" style={{ margin: 0 }}>Aggiorna</h3>
      <div className="grid2">
        <label className="field">Stato<select className="input" value={m.stato} onChange={(e) => setM({ ...m, stato: e.target.value as TaskStato })}>
          {TASK_STATI.map((s) => <option key={s} value={s}>{ETICHETTE_TASK[s]}</option>)}</select></label>
        <label className="field">Priorità<select className="input" value={m.priorita} onChange={(e) => setM({ ...m, priorita: e.target.value as Priorita })}>
          {PRIORITA.map((p) => <option key={p}>{p}</option>)}</select></label>
        <label className="field">Agente<select className="input" value={m.agente} onChange={(e) => setM({ ...m, agente: e.target.value })}>
          <option value="">—</option>{snap.agents.map((a) => <option key={a.id} value={a.id}>{a.nome} · {a.id}</option>)}</select></label>
        <label className="field">Prossimo passo<input className="input" value={m.next} onChange={(e) => setM({ ...m, next: e.target.value })} /></label>
      </div>
      <p className="dim" style={{ fontSize: 12, margin: 0 }}>Il database rifiuta i titoli duplicati, un secondo task in esecuzione per lo stesso agente e i task pronti con dipendenze aperte.
        «Riprova» automatico non esiste: Guardian non esegue i task, li coordina.</p>
      <div className="row"><button className="btn primary" type="submit">Salva</button>
        <button className="btn" type="button" onClick={() => apri({ p: 'approvazioni', filtro: `nuova-${t.id}` })}><ShieldCheck size={16} aria-hidden />Richiedi approvazione</button></div>
    </form>
    {appr.length > 0 && <div className="stack"><h3 className="section-title">Approvazioni</h3>{appr.map((a) => (
      <button key={a.id} className="item" onClick={() => apri({ p: 'approvazione', id: String(a.id) })}><ShieldCheck size={16} aria-hidden />
        <div><div className="t">{a.action}</div><div className="s">{a.status}</div></div></button>))}</div>}
    <div className="stack"><h3 className="section-title">Memoria del task</h3>
      {mem === null ? <Scheletro righe={2} /> : mem.length === 0 ? <Vuoto icona={BookOpen}>Nessuna voce.</Vuoto> :
        mem.map((x) => <div key={x.id} className="item static"><div><div className="t">{x.kind}</div><div style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{x.content}</div>
          <div className="s">Fonte: {x.source} · {fa(x.created_at)}</div></div></div>)}</div>
    {handoff.length > 0 && <div className="stack"><h3 className="section-title">Handoff</h3>{handoff.map((h) => (
      <div key={h.id} className="item static"><Shuffle size={16} aria-hidden /><div><div className="t">{h.agent_name} → {h.to_agent_id ?? 'chiunque'} ({h.stato})</div>
        <div className="s">Prossimo passo: {h.next_step}</div></div></div>))}</div>}
    <div className="stack"><h3 className="section-title">Cronologia</h3>
      {eventi.length === 0 ? <Vuoto>Nessun evento.</Vuoto> : eventi.map((e) => <div key={e.id} className="item static"><div><div className="t" style={{ fontWeight: 500 }}>{e.message}</div>
        <div className="s mono">{fa(e.timestamp)} · {e.event_type}</div></div></div>)}</div>
  </>);
}

function NuovaApprovazione({ taskId, onFatto }: { taskId?: number; onFatto: () => void }) {
  const { snap, source, esegui, user } = useG();
  const [f, setF] = useState({ action: '', action_type: 'email' as ActionType, reason: '', impact: '', data_involved: '', task_id: taskId ? String(taskId) : '', agent_id: '' });
  if (!snap) return null;
  return (
    <form className="card stack" onSubmit={async (e) => { e.preventDefault();
      const ok = await esegui(() => source.richiediApprovazione({ ...f, task_id: f.task_id ? Number(f.task_id) : null, agent_id: f.agent_id || null }, user.id), 'Richiesta registrata');
      if (ok !== undefined) onFatto(); }}>
      <label className="field">Azione proposta *<input className="input" required value={f.action} onChange={(e) => setF({ ...f, action: e.target.value })} /></label>
      <div className="grid2">
        <label className="field">Tipo<select className="input" value={f.action_type} onChange={(e) => setF({ ...f, action_type: e.target.value as ActionType })}>
          {ACTION_TYPES.map((a) => <option key={a} value={a}>{ETICHETTE_AZIONE[a]}</option>)}</select></label>
        <label className="field">Agente che la propone<select className="input" value={f.agent_id} onChange={(e) => setF({ ...f, agent_id: e.target.value })}>
          <option value="">— (persona)</option>{snap.agents.map((a) => <option key={a.id} value={a.id}>{a.nome} · {a.id}</option>)}</select></label>
      </div>
      <label className="field">Motivo<input className="input" value={f.reason} onChange={(e) => setF({ ...f, reason: e.target.value })} /></label>
      <label className="field">Impatto previsto<input className="input" value={f.impact} onChange={(e) => setF({ ...f, impact: e.target.value })} /></label>
      <label className="field">Dati coinvolti (descrivili, non incollarli)<input className="input" value={f.data_involved} onChange={(e) => setF({ ...f, data_involved: e.target.value })} /></label>
      <label className="field">Task collegato<select className="input" value={f.task_id} onChange={(e) => setF({ ...f, task_id: e.target.value })}>
        <option value="">—</option>{snap.tasks.filter((t) => !TASK_TERMINALI.includes(t.stato)).map((t) => <option key={t.id} value={t.id}>#{t.id} {t.titolo}</option>)}</select></label>
      <button className="btn primary" type="submit">Invia richiesta</button>
    </form>
  );
}

export function ApprovalsPanel({ filtro }: Pannello) {
  const { snap, apri } = useG();
  const taskId = filtro?.startsWith('nuova-') ? Number(filtro.slice(6)) : undefined;
  const [nuova, setNuova] = useState(!!filtro?.startsWith('nuova'));
  if (!snap) return <Scheletro />;
  const attese = snap.approvals.filter((a) => a.status === 'richiesta'); const storico = snap.approvals.filter((a) => a.status !== 'richiesta');
  const riga = (a: typeof snap.approvals[number]) => (
    <button key={a.id} className="item" onClick={() => apri({ p: 'approvazione', id: String(a.id) })}><ShieldCheck size={16} aria-hidden color={a.status === 'richiesta' ? 'var(--warn)' : undefined} />
      <div style={{ flex: 1 }}><div className="t">{a.action}</div><div className="s">{ETICHETTE_AZIONE[a.action_type]} · {fa(a.created_at)}</div></div>
      <span className={`pill ${a.status === 'richiesta' ? 'warn' : a.status === 'approvata' ? 'ok' : 'crit'}`}>{a.status}</span></button>);
  return (<>
    <p className="note">Le azioni esterne restano ferme finché una persona le approva. Guardian registra la decisione: non invia email, non paga, non pubblica.</p>
    <div className="row"><button className="btn" onClick={() => setNuova((n) => !n)} aria-expanded={nuova}><Plus size={16} aria-hidden />Richiedi approvazione</button></div>
    {nuova && <NuovaApprovazione taskId={taskId} onFatto={() => setNuova(false)} />}
    <h3 className="section-title">In attesa <span className="count">{attese.length}</span></h3>
    {attese.length === 0 ? <Vuoto icona={ShieldCheck}>Niente da approvare.</Vuoto> : <div className="list">{attese.map(riga)}</div>}
    <h3 className="section-title">Storico <span className="count">{storico.length}</span></h3>
    {storico.length === 0 ? <Vuoto>Nessuna decisione ancora.</Vuoto> : <div className="list">{storico.map(riga)}</div>}
    <p className="dim" style={{ fontSize: 12 }}>«Chiedi modifiche» e la scadenza delle richieste non esistono ancora nel database: servirebbe una migrazione approvata.</p>
  </>);
}

export function ApprovalPanel({ id }: Pannello) {
  const { snap, source, esegui, user, apri } = useG();
  const a = snap?.approvals.find((x) => String(x.id) === id);
  if (!snap) return <Scheletro />;
  if (!a) return <Vuoto>Approvazione non trovata.</Vuoto>;
  const nome = (uid?: string | null) => snap.users.find((u) => u.id === uid)?.nome ?? uid ?? '—';
  return (<>
    <div className="row"><span className={`pill ${a.status === 'richiesta' ? 'warn' : a.status === 'approvata' ? 'ok' : 'crit'}`}>{a.status}</span>
      <span className="pill">{ETICHETTE_AZIONE[a.action_type]}</span></div>
    <h3 style={{ margin: 0, fontSize: 18 }}>{a.action}</h3>
    <dl className="kv">
      <dt>Proposta da</dt><dd>{a.agent_id ? `${a.agent_id} (agente)` : nome(a.requested_by)} · {fa(a.created_at)}</dd>
      <dt>Motivo</dt><dd>{a.reason || '—'}</dd><dt>Impatto previsto</dt><dd>{a.impact || '—'}</dd><dt>Dati coinvolti</dt><dd>{a.data_involved || '—'}</dd>
      {a.description && <><dt>Dettagli</dt><dd>{a.description}</dd></>}
      <dt>Task</dt><dd>{a.task_id ? <a href="#" onClick={(e) => { e.preventDefault(); apri({ p: 'task', id: String(a.task_id) }); }}>#{a.task_id}</a> : '—'}</dd>
      {a.decided_by && <><dt>Deciso da</dt><dd>{nome(a.decided_by)} · {fa(a.decided_at)}</dd></>}
    </dl>
    {a.status === 'richiesta' ? (
      <div className="grid2">
        <button className="btn primary" onClick={() => void esegui(() => source.decidiApprovazione(a.id, 'approvata', user.id), 'Approvata')}>Approva</button>
        <button className="btn danger" onClick={() => void esegui(() => source.decidiApprovazione(a.id, 'rifiutata', user.id), 'Rifiutata')}>Rifiuta</button>
      </div>) : <p className="dim">Decisione registrata. Guardian non ha eseguito l'azione.</p>}
  </>);
}

export function HandoffPanel({ filtro }: Pannello) {
  const { snap, source, esegui, user } = useG();
  const [stato, setStato] = useState(filtro ?? 'aperto');
  const [chi, setChi] = useState<Record<number, string>>({});
  if (!snap) return <Scheletro />;
  const lista = snap.handoffs.filter((h) => h.stato === stato);
  return (<>
    <p className="note">Un handoff conserva il contesto per riprendere il lavoro: chi lo prende riparte dal «prossimo passo». Cambiare modello non è un handoff.
      Si salvano dal PC con <span className="mono">guardian_bridge.py checkpoint</span> o dal Guardian classico.</p>
    <div className="row">{(['aperto', 'preso', 'chiuso'] as const).map((s) => <button key={s} className={`btn sm ${stato === s ? 'primary' : ''}`} aria-pressed={stato === s} onClick={() => setStato(s)}>{s}</button>)}</div>
    {lista.length === 0 ? <Vuoto icona={Shuffle}>Nessun handoff {stato}.</Vuoto> : lista.map((h) => (
      <div key={h.id} className="card stack">
        <div className="row between"><b>{h.agent_name} → {h.to_agent_id ?? 'chiunque'}</b><span className="dim" style={{ fontSize: 12 }}>{fa(h.timestamp)}{h.task_id ? ` · task #${h.task_id}` : ''}</span></div>
        <div><b>Prossimo passo:</b> {h.next_step}</div>
        <dl className="kv">
          <dt>Stato</dt><dd>{h.summary}</dd>
          {h.tests_pending && <><dt>Test mancanti</dt><dd>{h.tests_pending}</dd></>}
          {h.dependencies && <><dt>Dipendenze</dt><dd>{h.dependencies}</dd></>}
          {h.important_notes && <><dt>Da non perdere</dt><dd>{h.important_notes}</dd></>}
          {h.files_changed.length > 0 && <><dt>File</dt><dd className="mono" style={{ fontSize: 12 }}>{h.files_changed.join(', ')}</dd></>}
        </dl>
        {h.stato === 'aperto' && <div className="row">
          <select className="input" style={{ maxWidth: 240 }} value={chi[h.id] ?? ''} onChange={(e) => setChi({ ...chi, [h.id]: e.target.value })} aria-label="Chi lo prende">
            <option value="">— lo prendo io</option>{snap.agents.map((a) => <option key={a.id} value={a.id}>{a.nome} · {a.id}</option>)}</select>
          <button className="btn primary" onClick={() => void esegui(() => source.prendiHandoff(h.id, chi[h.id] || null, user.id), 'Handoff preso')}>Prendi in carico</button></div>}
        {h.stato === 'preso' && <button className="btn" onClick={() => void esegui(() => source.chiudiHandoff(h.id, user.id), 'Handoff chiuso')}>Chiudi</button>}
      </div>))}
  </>);
}

export function MemoriaPanel() {
  const { snap, source, esegui, user } = useG();
  const [q, setQ] = useState(''); const [proj, setProj] = useState('');
  const [voci, setVoci] = useState<Memory[] | null>(null); const [err, setErr] = useState('');
  const [n, setN] = useState({ kind: 'decisione', content: '', source: '' });
  const cerca = () => { setVoci(null); source.memoria({ q, project_id: proj ? Number(proj) : undefined }).then((v) => { setVoci(v); setErr(''); })
    .catch((e) => { setVoci([]); setErr(e instanceof Error ? e.message : 'Errore'); }); };
  useEffect(cerca, []); // eslint-disable-line
  return (<>
    <form className="row" onSubmit={(e) => { e.preventDefault(); cerca(); }}>
      <input className="input" style={{ flex: 1, minWidth: 160 }} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cerca nella memoria" aria-label="Cerca nella memoria" />
      <select className="input" style={{ maxWidth: 200 }} value={proj} onChange={(e) => setProj(e.target.value)} aria-label="Azienda">
        <option value="">Tutte le aziende</option>{snap?.projects.map((p) => <option key={p.id} value={p.id}>{p.nome}</option>)}</select>
      <button className="btn" type="submit">Cerca</button></form>
    {err && <div className="err">{err}</div>}
    {voci === null ? <Scheletro /> : voci.length === 0 ? <Vuoto icona={BookOpen}>Nessuna voce trovata.</Vuoto> : voci.map((m) => (
      <div key={m.id} className="item static"><div><div className="t">{m.kind}{m.task_id ? ` · task #${m.task_id}` : ''}</div>
        <div style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{m.content}</div><div className="s">Fonte: {m.source} · {fa(m.created_at)}</div></div></div>))}
    <form className="card stack" onSubmit={async (e) => { e.preventDefault();
      const ok = await esegui(() => source.aggiungiMemoria({ ...n, project_id: proj ? Number(proj) : null }, user.id), 'Salvato in memoria');
      if (ok !== undefined) { setN({ ...n, content: '', source: '' }); cerca(); } }}>
      <h3 className="section-title" style={{ margin: 0 }}>Aggiungi alla memoria</h3>
      <label className="field">Tipo<select className="input" value={n.kind} onChange={(e) => setN({ ...n, kind: e.target.value })}>{MEMORY_KINDS.map((k) => <option key={k}>{k}</option>)}</select></label>
      <label className="field">Contenuto *<textarea className="input" required value={n.content} onChange={(e) => setN({ ...n, content: e.target.value })} /></label>
      <label className="field">Fonte * (da dove viene)<input className="input" required value={n.source} onChange={(e) => setN({ ...n, source: e.target.value })} /></label>
      <button className="btn primary" type="submit">Salva</button>
    </form>
  </>);
}
